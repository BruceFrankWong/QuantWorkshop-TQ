# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'

from typing import Dict, List

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
    futures_list = relationship('Futures', back_populates='exchange')
    options_list = relationship('Options', back_populates='exchange')

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


class Product(ModelBase):
    __tablename__ = 'product'
    id = Column(Integer, primary_key=True)


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

    @property
    def contract(self) -> str:
        return f'{self.symbol}'

    @property
    def contract_size(self) -> str:
        return f'{self.size} {self.unit}'

    def __repr__(self):
        return f'<Futures(name={self.name},' \
               f'exchange={db_session.query(Exchange).filter_by(id=self.exchange_id).one().symbol},' \
               f'symbol={self.symbol})>'


class Options(ModelBase):
    __tablename__ = 'options'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    symbol = Column(String, nullable=False, unique=True)
    exchange_id = Column(Integer, ForeignKey('exchange.id'), nullable=False)

    exchange = relationship('Exchange', back_populates='options_list')

    @property
    def symbol_call(self) -> str:
        return f'{self.symbol}'

    @property
    def symbol_put(self) -> str:
        return f'{self.symbol}'

    def __repr__(self):
        return f'<Options(name={self.name},' \
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


class TQDirection(ModelBase):
    """
    天勤量化SDK，下单方向。
        BUY=买
        SELL=卖
    """
    __tablename__ = 'tq_direction'

    id = Column(Integer, primary_key=True)
    value = Column(String, nullable=False)
    zh = Column(String, nullable=False)

    order_list = relationship('TQOrder', back_populates='direction')
    trade_list = relationship('TQTrade', back_populates='direction')

    def __repr__(self):
        return f'<TQDirection(value={self.value}, zh={self.zh})>'


class TQOffset(ModelBase):
    """
    天勤量化SDK，开平标志。
        OPEN=开仓
        CLOSE=平仓
        CLOSETODAY=平今
    """
    __tablename__ = 'tq_offset'

    id = Column(Integer, primary_key=True)
    value = Column(String, nullable=False)
    zh = Column(String, nullable=False)

    order_list = relationship('TQOrder', back_populates='offset')
    trade_list = relationship('TQTrade', back_populates='offset')

    def __repr__(self):
        return f'<TQOffset(value={self.value}, zh={self.zh})>'


class TQOrder(ModelBase):
    __tablename__ = 'tq_order'

    id = Column(Integer, primary_key=True)
    datetime = Column(DateTime, nullable=False)
    order_id = Column(String, nullable=False)
    direction_id = Column(Integer, ForeignKey('tq_direction.id'), nullable=False)
    offset_id = Column(Integer, ForeignKey('tq_offset.id'), nullable=False)
    price = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    status = Column(String, nullable=False)
    opponent = Column(String)

    direction = relationship('TQDirection', back_populates='order_list')
    offset = relationship('TQOffset', back_populates='order_list')
    trade_list = relationship('TQTrade', back_populates='order')

    def __repr__(self):
        return f'<TQOrder(order_id={self.order_id}, zh={self.zh})>'


class TQTrade(ModelBase):
    __tablename__ = 'tq_trade'

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('tq_order.id'), nullable=False)   # 委托单ID
    trade_id = Column(String, nullable=False)                               # 成交ID
    exchange_trade_id = Column(String, nullable=False)                      # 交易所成交号
    exchange_id = Column(String, nullable=False)                            # 交易所
    instrument_id = Column(String, nullable=False)                          # 交易所内的合约代码
    direction_id = Column(Integer, ForeignKey('tq_direction.id'), nullable=False)   # 下单方向
    offset_id = Column(Integer, ForeignKey('tq_offset.id'), nullable=False)         # 开平标志

    direction = relationship('TQDirection', back_populates='trade_list')
    offset = relationship('TQOffset', back_populates='trade_list')
    order = relationship('TQOrder', back_populates='trade_list')


class Balance(ModelBase):
    __tablename__ = 'balance'

    id = Column(Integer, primary_key=True)
    datetime = Column(DateTime, nullable=False)
    cash = Column(Float, nullable=False)
    position_long = Column(Integer, nullable=False)
    position_short = Column(Integer, nullable=False)
    order_long = Column(Integer, nullable=False)
    order_short = Column(Integer, nullable=False)
