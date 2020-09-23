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


class TQDirection(ModelBase):
    """
    天勤量化SDK，下单方向。
        BUY=买
        SELL=卖
    """
    __tablename__ = 'tq_direction'

    id = Column(Integer, primary_key=True)
    value = Column(String, nullable=False, unique=True)
    zh = Column(String, nullable=False, unique=True)

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
    value = Column(String, nullable=False, unique=True)
    zh = Column(String, nullable=False, unique=True)

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


class BacktestOrderBase(AbstractConcreteBase, ModelBase):
    @declared_attr
    def table_name(cls):
        return Column(String, ForeignKey('tq_order.table_name'))


def is_table_exist(table: str) -> bool:
    return table in db_metadata.tables.keys()


def initialize_database():
    basic_table_list: List[str] = ['tq_direction', 'tq_offset']

    ModelBase.metadata.drop_all(db_engine)
    ModelBase.metadata.create_all(db_engine)
    db_session.add_all([
        TQDirection(value='BUY', zh='买'),
        TQDirection(value='SELL', zh='卖'),

        TQOffset(value='OPEN', zh='开'),
        TQOffset(value='CLOSE', zh='平'),
        TQOffset(value='CLOSETODAY', zh='平今'),
    ])
    db_session.commit()


def get_table_order(strategy_name: str) -> object:
    dt: str = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

    table_class = type(
        f'Backtest{strategy_name}Order', (TQOrder,), {
            '__table_args__': {
                'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8', 'extend_existing': True
            },
            '__tablename__': f'backtest_{strategy_name}_order_{dt}'
        }
    )
    return table_class


def make_table_order(strategy_name: str):
    dt: str = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    table_name: str = f'backtest_{strategy_name}_order_{dt}'

    class BacktestOrder(BacktestOrderBase):
        __tablename__ = table_name
        __mapper_args__ = {'polymorphic_identity': table_name, 'concrete': True}

        datetime = Column(DateTime, primary_key=True)
        value = Column(Float)

    return BacktestOrder


initialize_database()
