# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'


from typing import List, Tuple
from datetime import datetime

from sqlalchemy import Table, Column, ForeignKey, String, Integer, Float, Date, DateTime
from sqlalchemy.orm import mapper

from . import ModelBase, db_metadata


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

    def __init__(self, order_id: str):
        self.order_id = order_id

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


def get_backtest_model(dt: datetime) -> Tuple[ModelBase, ModelBase]:
    datetime_string: str = dt.strftime('%Y-%m-%d_%H-%M-%S')
    table_backtest_order_base = Table(
        f'backtest_{datetime_string}_order',
        db_metadata,
        Column('id', Integer, primary_key=True),
        Column('order_id', String, nullable=False),
        Column('exchange_id', String),                          # 交易所
        Column('exchange_order_id', String),
        Column('instrument_id', String),                        # 交易所内的合约代码
        Column('direction', String, nullable = False),          # 下单方向
        Column('direction', String, nullable = False),          # 开平标志
        Column('volume_orign', Integer, nullable=False),        # 总报单手数
        Column('volume_left', Integer),                         # 未成交手数
        Column('limit_price', Float),                           # 委托价格, 仅当 price_type=LIMIT 时有效
        Column('price_type', String),                           # 价格类型, ANY=市价, LIMIT=限价
        Column('volume_condition', String),                     # 手数条件, ANY=任何数量, MIN=最小数量, ALL=全部数量
        Column('time_condition', String),                       # 时间条件,
                                                                # IOC=立即完成，否则撤销, GFS=本节有效, GFD=当日有效,
                                                                # GTC=撤销前有效, GFA=集合竞价有效
        Column('insert_datetime', DateTime, nullable=False),    # 下单时间
                                                                # 自unix epoch(1970-01-01 00: 00:00 GMT)以来的纳秒数.
        Column('last_msg', String),                             # 委托单状态信息
        Column('status', String),                               # 委托单状态, ALIVE=有效, FINISHED=已完
        Column('last_datetime', DateTime),                      # 最后更新时间。
    )

    table_backtest_trade_base = Table(
        f'backtest_{datetime_string}_trade',
        db_metadata,
        Column('id', Integer, primary_key=True),
        Column('order_id', String, nullable=False),
        Column('exchange_id', String),  # 交易所
        Column('exchange_order_id', String),
        Column('instrument_id', String),  # 交易所内的合约代码
        Column('direction', String, nullable=False),  # 下单方向
        Column('direction', String, nullable=False),  # 开平标志
        Column('volume_orign', Integer, nullable=False),  # 总报单手数
        Column('volume_left', Integer),  # 未成交手数
        Column('limit_price', Float),  # 委托价格, 仅当 price_type=LIMIT 时有效
        Column('price_type', String),  # 价格类型, ANY=市价, LIMIT=限价
        Column('volume_condition', String),         # 手数条件, ANY=任何数量, MIN=最小数量, ALL=全部数量
        Column('time_condition', String),           # 时间条件,
                                                    # IOC=立即完成，否则撤销, GFS=本节有效, GFD=当日有效,
                                                    # GTC=撤销前有效, GFA=集合竞价有效
        Column('insert_datetime', DateTime, nullable=False),  # 下单时间
        # 自unix epoch(1970-01-01 00: 00:00 GMT)以来的纳秒数.
        Column('last_msg', String),  # 委托单状态信息
        Column('status', String),  # 委托单状态, ALIVE=有效, FINISHED=已完
        Column('last_datetime', DateTime),  # 最后更新时间。
    )

