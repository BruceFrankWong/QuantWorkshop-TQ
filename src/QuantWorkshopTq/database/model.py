# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'

from typing import Dict, List

from sqlalchemy.orm import relationship

from sqlalchemy import Column, ForeignKey, String, Integer, Float, Date

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
