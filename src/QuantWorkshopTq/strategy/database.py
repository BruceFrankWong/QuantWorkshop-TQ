# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'


from typing import List
from datetime import datetime

from sqlalchemy.ext.declarative import declarative_base, declared_attr, AbstractConcreteBase
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine, event, MetaData, inspect
from sqlalchemy import Column, ForeignKey, String, Integer, Float, DateTime

from . import get_application_path


@event.listens_for(Engine, 'connect')
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute('PRAGMA foreign_keys=ON')
    cursor.close()


ModelBase = declarative_base()

db_engine = create_engine(f'sqlite:///{get_application_path()}/backtest.sqlite')
db_session = sessionmaker(bind=db_engine)()
db_metadata = MetaData(bind=db_engine)
db_inspect = inspect(db_engine)


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

    trade_list = relationship('BacktestTrade', back_populates='order')

    def __repr__(self):
        return f'<BacktestOrder(order_id={self.order_id}, {self.direction} {self.offset}, {self.volume} @{self.price})>'


class BacktestTrade(ModelBase):
    __tablename__ = 'backtest_trade'

    id = Column(Integer, primary_key=True)
    backtest_order_id = Column(Integer, ForeignKey('backtest_order.id'), nullable=False)
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

    order = relationship('BacktestOrder', back_populates='trade_list')

    def __repr__(self):
        return f'<BacktestTrade(order_id={self.order_id}, {self.direction} {self.offset}, {self.volume} @{self.price})>'


def is_table_exist(table: str) -> bool:
    return table in db_metadata.tables.keys()


def initialize_database():
    basic_table_list: List[str] = ['backtest_direction', 'backtest_offset']

    ModelBase.metadata.drop_all(db_engine)
    ModelBase.metadata.create_all(db_engine)


initialize_database()
