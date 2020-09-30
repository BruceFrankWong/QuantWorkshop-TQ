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
    stock_list = relationship('Stock', back_populates='exchange')
    futures_list = relationship('Futures', back_populates='exchange')
    option_list = relationship('Option', back_populates='exchange')

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


class MainContract(ModelBase):
    __tablename__ = 'main_contract'

    id = Column(Integer, primary_key=True)
    datetime = Column(DateTime, nullable=False)
    cash = Column(Float, nullable=False)
    position_long = Column(Integer, nullable=False)
    position_short = Column(Integer, nullable=False)
    order_long = Column(Integer, nullable=False)
    order_short = Column(Integer, nullable=False)
