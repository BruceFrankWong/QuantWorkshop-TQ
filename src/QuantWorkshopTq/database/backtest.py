# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'


from typing import List, Tuple
from datetime import datetime

from sqlalchemy import Table, Column, ForeignKey, String, Integer, Float, Date, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql import exists

from . import ModelBase, db_engine, db_metadata, db_session


class BacktestRecord(ModelBase):
    __tablename__ = 'backtest_record'
    id = Column(Integer, primary_key=True)
    datetime = Column(DateTime, nullable=False)
    strategy = Column(String(20), nullable=False)
    exchange = Column(String(10), nullable=False)
    instrument = Column(String(20), nullable=False)

    @property
    def backtest_id(self) -> str:
        return f'backtest_record_{self.datetime.strftime("%Y-%m-%d_%H-%M-%S")}'

    @property
    def backtest_order_table_name(self) -> str:
        return ''.join([self.backtest_id, '_order'])

    @property
    def backtest_trade_table_name(self) -> str:
        return ''.join([self.backtest_id, '_trade'])

    def __repr__(self):
        return f'<Backtest(at: {self.datetime}, on: {self.exchange}.{self.instrument}, record: {self.backtest_id})>'


class BacktestOrderBase(ModelBase):
    __tablename__ = 'backtest_order_base'

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

    def __repr__(self):
        return f'<BacktestOrder(order_id={self.order_id}, {self.direction} {self.offset}, {self.volume} @{self.price})>'


class BacktestTradeBase(ModelBase):
    __tablename__ = 'backtest_trade_base'

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

    def __repr__(self):
        return f'<BacktestTrade(order_id={self.order_id}, {self.direction} {self.offset}, {self.volume} @{self.price})>'


# def initialize_database():
#     basic_table_list: List[str] = ['backtest_direction', 'backtest_offset']
#
#     ModelBase.metadata.drop_all(db_engine)
#     ModelBase.metadata.create_all(db_engine)
#
#
# initialize_database()


# table_backtest_order_prototype = Table(
#     'backtest_record_order_prototype',
#     db_metadata,
#     Column('id', Integer, primary_key=True),
#     Column('order_id', String, nullable=False),
#     Column('exchange_id', String, nullable=False),                          # 交易所
#     Column('exchange_order_id', String),
#     Column('instrument_id', String, nullable=False),                        # 交易所内的合约代码
#     Column('direction', String, nullable=False),          # 下单方向
#     Column('offset', String, nullable=False),          # 开平标志
#     Column('volume_orign', Integer, nullable=False),        # 总报单手数
#     Column('volume_left', Integer),                         # 未成交手数
#     Column('limit_price', Float),                           # 委托价格, 仅当 price_type=LIMIT 时有效
#     Column('price_type', String),                           # 价格类型, ANY=市价, LIMIT=限价
#     Column('volume_condition', String),                     # 手数条件, ANY=任何数量, MIN=最小数量, ALL=全部数量
#     Column('time_condition', String),                       # 时间条件,
#                                                             # IOC=立即完成，否则撤销, GFS=本节有效, GFD=当日有效,
#                                                             # GTC=撤销前有效, GFA=集合竞价有效
#     Column('insert_datetime', DateTime, nullable=False),    # 下单时间
#                                                             # 自unix epoch(1970-01-01 00: 00:00 GMT)以来的纳秒数.
#     Column('last_msg', String),                             # 委托单状态信息
#     Column('status', String),                               # 委托单状态, ALIVE=有效, FINISHED=已完
#     Column('last_datetime', DateTime),                      # 最后更新时间。
# )
#
# table_backtest_trade_prototype = Table(
#     'backtest_record_trade_prototype',
#     db_metadata,
#     Column('id', Integer, primary_key=True),
#     Column('order_id', String, nullable=False),
#     Column('exchange_id', String),  # 交易所
#     Column('exchange_order_id', String),
#     Column('instrument_id', String),  # 交易所内的合约代码
#     Column('direction', String, nullable=False),  # 下单方向
#     Column('direction', String, nullable=False),  # 开平标志
#     Column('volume_orign', Integer, nullable=False),  # 总报单手数
#     Column('volume_left', Integer),  # 未成交手数
#     Column('limit_price', Float),  # 委托价格, 仅当 price_type=LIMIT 时有效
#     Column('price_type', String),  # 价格类型, ANY=市价, LIMIT=限价
#     Column('volume_condition', String),         # 手数条件, ANY=任何数量, MIN=最小数量, ALL=全部数量
#     Column('time_condition', String),           # 时间条件,
#                                                 # IOC=立即完成，否则撤销, GFS=本节有效, GFD=当日有效,
#                                                 # GTC=撤销前有效, GFA=集合竞价有效
#     Column('insert_datetime', DateTime, nullable=False),  # 下单时间
#     # 自unix epoch(1970-01-01 00: 00:00 GMT)以来的纳秒数.
#     Column('last_msg', String),  # 委托单状态信息
#     Column('status', String),  # 委托单状态, ALIVE=有效, FINISHED=已完
#     Column('last_datetime', DateTime),  # 最后更新时间。
# )
#
#
# class BacktestOrder(object):
#     order_id: str
#     exchange_id: str
#     exchange_order_id: str
#     instrument_id: str
#     direction: str
#     offset: str
#     volume_orign: int
#     volume_left: int
#
#     status: str
#     insert_datetime: datetime
#     last_datetime: datetime
#
#     price = Column(Float, nullable=False)
#
#     status = Column(String, nullable=False)
#     opponent = Column(String)
#
#     def __init__(self,
#                  order_id: str,
#                  exchange_id: str,
#                  instrument_id: str,
#                  direction: str,
#                  offset: str,
#                  volume_orign: int,
#                  volume_left: int,
#                  insert_datetime: datetime) -> None:
#         self.order_id = order_id
#         self.exchange_id = exchange_id
#         self.instrument_id = instrument_id
#         self.direction = direction
#         self.offset = offset
#         self.volume_orign = volume_orign
#         self.volume_left = volume_left
#
#         self.status = 'ALIVE'
#
#     def set_exchange_order_id(self, value: str, current_datetime: datetime) -> None:
#         self.exchange_order_id = value
#         self.last_datetime = current_datetime
#
#
# class BacktestTrade(object):
#     backtest_order_id = Column(Integer, ForeignKey('backtest_order.id'), nullable=False)
#     #     order_id = Column(String, nullable=False)   # 委托单ID
#     #     trade_id = Column(String, nullable=False)                               # 成交ID
#     #     exchange_trade_id = Column(String, nullable=False)                      # 交易所成交号
#     #     exchange_id = Column(String, nullable=False)                            # 交易所
#     #     instrument_id = Column(String, nullable=False)                          # 交易所内的合约代码
#     #     direction = Column(String, nullable=False)   # 下单方向
#     #     offset = Column(String, nullable=False)         # 开平标志
#     #     price = Column(Float, nullable=False)
#     #     volume = Column(Integer, nullable=False)
#     #     datetime = Column(DateTime, nullable=False)


def get_backtest_model(dt: datetime, strategy: str, exchange: str, instrument: str) -> Tuple[type, type]:
    msg_exception: str = 'Backtest record found in table <backtest>, but {table} record not.'
    backtest_record: BacktestRecord
    table_name_backtest_order: str
    table_name_backtest_trade: str
    table_backtest_order: Table
    table_backtest_trade: Table
    BacktestOrder: type
    BacktestTrade: type

    if db_session.query(exists().where(BacktestRecord.datetime == dt)).scalar():
        # 如果在数据库中找到记录
        backtest_record = db_session.query(BacktestRecord).filter_by(datetime=dt).one()

        # 委托单数据表不在数据库中，引发异常
        table_name_backtest_order = backtest_record.backtest_order_table_name
        if table_name_backtest_order not in db_metadata.tables.keys():
            raise RuntimeError(msg_exception.format(table='ORDER'))

        # table_backtest_order = db_metadata.tables[table_name_backtest_order]

        # 成交记录数据表不在数据库中，引发异常
        table_name_backtest_trade = backtest_record.backtest_trade_table_name
        if table_name_backtest_trade not in db_metadata.tables.keys():
            raise RuntimeError(msg_exception.format(table='TRADE'))

        # table_backtest_trade = db_metadata.tables[table_name_backtest_trade]

    else:
        # 如果没有在数据库中找到记录，新建记录
        backtest_record = BacktestRecord(
            datetime=dt,
            strategy=strategy,
            exchange=exchange,
            instrument=instrument
        )
        db_session.add(backtest_record)
        db_session.commit()

    backtest_order_table_name = backtest_record.backtest_order_table_name
    backtest_trade_table_name = backtest_record.backtest_trade_table_name
    BacktestOrder = type('BacktestOrder',
                         (BacktestOrderBase,),
                         dict(__tablename__=backtest_order_table_name,
                              __mapper_args__={'polymorphic_identity': backtest_order_table_name,
                                               'concrete': True
                                               },
                              # trade_list=relationship('BacktestTrade', back_populates='order')
                              )
                         )
    BacktestTrade = type('BacktestTrade',
                         (BacktestTradeBase,),
                         dict(__tablename__=backtest_trade_table_name,
                              __mapper_args__={'polymorphic_identity': backtest_record.backtest_trade_table_name,
                                               'concrete': True
                                               },
                              # backtest_order_id=Column(Integer,
                              #                          ForeignKey(f'{backtest_order_table_name}.id'),
                              #                          nullable=False
                              #                          ),
                              # order=relationship('BacktestOrder', back_populates='trade_list')
                              )
                         )
    BacktestOrder.create(db_engine, checkfirst=True)
    BacktestTrade.create(db_engine, checkfirst=True)
    return BacktestOrder, BacktestTrade
