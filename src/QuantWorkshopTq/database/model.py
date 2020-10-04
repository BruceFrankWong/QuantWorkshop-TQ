# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'


from typing import Dict, List
from datetime import date

from sqlalchemy.orm import relationship
from sqlalchemy import Column, ForeignKey, String, Integer, Float, Date, DateTime

from . import ModelBase, db_session


class Exchange(ModelBase):
    __tablename__ = 'exchange'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    fullname = Column(String, nullable=False, unique=True)
    symbol = Column(String, nullable=False, unique=True)

    holiday_list = relationship('Holiday', back_populates='exchange')
    stock_list = relationship('Stock', back_populates='exchange')
    futures_list = relationship('Futures', back_populates='exchange')
    option_list = relationship('Option', back_populates='exchange')

    def is_trading_day(self, day: date) -> bool:
        if 6 <= day.isoweekday() <= 7:
            return False
        for holiday in self.get_holiday_by_year(day.year):
            if holiday.begin <= day <= holiday.end:
                return False
        return False

    def get_holiday_by_year(self, year: int) -> list:
        if year <= 2000 or year > date.today().year:
            raise ValueError('Parameter <year> should be in [2001, Current Year]')
        return db_session.query(Holiday).filter(Holiday.exchange_id == self.id,
                                                Holiday.begin >= date(year, 1, 1),
                                                Holiday.begin <= date(year+1, 1, 1)
                                                ).all()

    def __repr__(self):
        return f'<Exchange(name={self.name}, fullname={self.fullname}, abbr={self.symbol})>'


class Holiday(ModelBase):
    __tablename__ = 'holiday'

    id = Column(Integer, primary_key=True)
    begin = Column(Date, nullable=False)
    end = Column(Date, nullable=False)
    reason = Column(String)

    exchange_id = Column(Integer, ForeignKey('exchange.id'), nullable=False)

    exchange = relationship('Exchange', back_populates='holiday_list')

    def __repr__(self):
        return f'<Holiday(name={self.name}, fullname={self.fullname}, abbr={self.symbol})>'


class Stock(ModelBase):
    __tablename__ = 'stock'
    id = Column(Integer, primary_key=True)
    exchange_id = Column(Integer, ForeignKey('exchange.id'), nullable=False)
    symbol = Column(String, nullable=False, unique=True)

    exchange = relationship('Exchange', back_populates='stock_list')

    def __repr__(self):
        return f'<Stock(name={self.name},' \
               f'exchange={db_session.query(Exchange).filter_by(id=self.exchange_id).one().symbol},' \
               f'symbol={self.symbol})>'


class Futures(ModelBase):
    __tablename__ = 'futures'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    symbol = Column(String, nullable=False, unique=True)
    contract_url = Column(String, nullable=False)
    margin = Column(Float, nullable=False)
    size = Column(Integer, nullable=False)
    unit = Column(String, nullable=False)
    fluctuation = Column(Float, nullable=False)
    exchange_id = Column(Integer, ForeignKey('exchange.id'), nullable=False)

    exchange = relationship('Exchange', back_populates='futures_list')
    contract_list = relationship('FuturesContract', back_populates='futures')
    main_contract_list = relationship('FuturesMainContract', back_populates='futures')

    @property
    def trading_contracts(self) -> List[str]:
        return self.trading_contracts_at(date.today())

    def trading_contracts_at(self, day: date) -> List[str]:
        return db_session.query(FuturesContract).filter(FuturesContract.futures_id == self.id,
                                                        FuturesContract.listed_date >= day,
                                                        FuturesContract.expiration_date <= day
                                                        ).all()

    @property
    def contract_size(self) -> str:
        return f'{self.size} {self.unit}'

    def __repr__(self):
        return f'<Futures(name={self.name},' \
               f'exchange={db_session.query(Exchange).filter_by(id=self.exchange_id).one().symbol},' \
               f'symbol={self.symbol})>'


class Option(ModelBase):
    __tablename__ = 'option'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    symbol = Column(String, nullable=False, unique=True)
    exchange_id = Column(Integer, ForeignKey('exchange.id'), nullable=False)

    exchange = relationship('Exchange', back_populates='option_list')

    @property
    def symbol_call(self) -> str:
        return f'{self.symbol}'

    @property
    def symbol_put(self) -> str:
        return f'{self.symbol}'

    def __repr__(self):
        return f'<Option(name={self.name},' \
               f'exchange={db_session.query(Exchange).filter_by(id=self.exchange_id).one().symbol},' \
               f'symbol={self.symbol})>'


class FuturesContract(ModelBase):
    __tablename__ = 'futures_contract'

    id = Column(Integer, primary_key=True)
    listed_date = Column(Date, nullable=False)
    expiration_date = Column(Date, nullable=False)
    futures_id = Column(Integer, ForeignKey('futures.id'), nullable=False)

    futures = relationship('Futures', back_populates='contract_list')
    quote_list = relationship('FuturesContractQuote', back_populates='contract')


class FuturesContractQuote(ModelBase):
    __tablename__ = 'futures_contract_quote'

    id = Column(Integer, primary_key=True)

    date = Column(Date, nullable=False)                 # 日期
    open = Column(Float, nullable=False)                # 开盘价
    high = Column(Float, nullable=False)                # 最高价
    low = Column(Float, nullable=False)                 # 最低价
    close = Column(Float, nullable=False)               # 收盘价
    volume = Column(Integer, nullable=False)            # 成交量
    amount = Column(Float, nullable=False)              # 成交额
    open_interest = Column(Integer, nullable=False)     # 持仓量
    settlement = Column(Float, nullable=False)          # 结算价

    contract_id = Column(Integer, ForeignKey('futures_contract.id'), nullable=False)

    contract = relationship('FuturesContract', back_populates='quote_list')


class FuturesMainContract(ModelBase):
    """
    期货主力合约
    """
    __tablename__ = 'futures_main_contract'

    id = Column(Integer, primary_key=True)
    datetime = Column(DateTime, nullable=False)
    futures_id = Column(Integer, ForeignKey='futures.id', nullable=False)
    contract_id = Column(Integer, ForeignKey='futures_contract.id', nullable=False)

    futures = relationship('Futures', back_populates='main_contract_list')

    def get_contract(self) -> FuturesContract:
        return db_session.query(FuturesContract).filter_by(id=self.contract_id).one()


class BacktestRecord(ModelBase):
    """
    回测记录
    """
    __tablename__ = 'backtest_record'

    id = Column(Integer, primary_key=True)
    strategy = Column(String(20), nullable=False)
    symbol = Column(String(20), nullable=False)
    backtest_start = Column(DateTime, nullable=False)
    backtest_end = Column(DateTime, nullable=False)
    real_start = Column(DateTime, nullable=False)
    real_end = Column(DateTime)

    order_list = relationship('BacktestOrder', back_populates='backtest')
    trade_list = relationship('BacktestTrade', back_populates='backtest')

    @property
    def backtest_id(self) -> str:
        return f'backtest_record_{self.datetime.strftime("%Y-%m-%d_%H-%M-%S")}'

    def __repr__(self):
        return f'<Backtest({self.strategy} on: {self.symbol}, at: {self.datetime}, record: {self.backtest_id})>'


class BacktestOrder(ModelBase):
    __tablename__ = 'backtest_order'

    id = Column(Integer, primary_key=True)
    insert_datetime = Column(DateTime, nullable=False)
    last_datetime = Column(DateTime)
    order_id = Column(String, nullable=False)
    direction = Column(String, nullable=False)
    offset = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    volume_orign = Column(Integer, nullable=False)
    volume_left = Column(Integer)
    status = Column(String, nullable=False)
    opponent = Column(String)

    backtest_id = Column(Integer, ForeignKey('backtest_record.id'), nullable=False)

    backtest = relationship('BacktestRecord', back_populates='order_list')
    trade_list = relationship('BacktestTrade', back_populates='order')

    def __repr__(self):
        return f'<BacktestOrder(order_id={self.order_id}, {self.direction} {self.offset}, {self.volume} @{self.price})>'


class BacktestTrade(ModelBase):
    __tablename__ = 'backtest_trade'

    id = Column(Integer, primary_key=True)
    order_id = Column(String, nullable=False)   # 委托单ID
    trade_id = Column(String, nullable=False)                               # 成交ID
    exchange_trade_id = Column(String, nullable=False)                      # 交易所成交号
    exchange_id = Column(String, nullable=False)                            # 交易所
    instrument_id = Column(String, nullable=False)                          # 交易所内的合约代码
    direction = Column(String, nullable=False)   # 下单方向
    offset = Column(String, nullable=False)         # 开平标志
    price = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    datetime = Column(DateTime, nullable=False)

    backtest_order_id = Column(Integer, ForeignKey('backtest_order.id'), nullable=False)
    backtest_id = Column(Integer, ForeignKey('backtest_record.id'), nullable=False)

    order = relationship('BacktestOrder', back_populates='trade_list')
    backtest = relationship('BacktestRecord', back_populates='trade_list')

    def __repr__(self):
        return f'<BacktestTrade(order_id={self.order_id}, {self.direction} {self.offset}, {self.volume} @{self.price})>'
