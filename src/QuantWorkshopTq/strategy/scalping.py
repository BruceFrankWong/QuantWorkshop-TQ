# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'

from typing import Dict, List, Optional
import logging
import os.path
import time
import datetime

from tqsdk import TqApi, TargetPosTask, BacktestFinished
from tqsdk.objs import Account, Position, Quote, Order
from tqsdk.entity import Entity
from tqsdk.ta import MACD
from pandas import DataFrame

from . import get_logger, get_table_order, db_session, TQDirection, TQOffset, TQOrder, TQTrade


def is_trading_time(t: datetime.time, tt_list: list) -> bool:
    for tt in tt_list:
        if tt['open'] <= t <= tt['close']:
            return True
    return False


def lots_at_price(order: Entity, p: float) -> int:
    order_id: str
    order: Order
    lots: int = 0
    for order_id, order in order.items():
        if order.limit_price == p:
            lots += order.volume_left
    return lots


class StrategyParameters(object):
    max_position: int


class Scalping(object):
    _strategy_name: str = 'Scalping'

    _timeout: int = 5
    _logger: logging.Logger

    # 策略参数
    _symbol: str
    _settings: dict

    _max_position: int

    def __init__(self, api: TqApi, logger: logging.Logger, max_position: int):
        self._api = api
        self._logger = logger

        self._symbol = 'DCE.c2101'

        self._max_position = max_position

    @staticmethod
    def is_trading_time(t: datetime.time) -> bool:
        trading_time_list: List[Dict[str, time]] = [
            {
                'open': datetime.time(hour=21, minute=0, second=0),
                'close': datetime.time(hour=23, minute=0, second=0),
            },
            {
                'open': datetime.time(hour=9, minute=0, second=0),
                'close': datetime.time(hour=11, minute=30, second=0),
            },
            {
                'open': datetime.time(hour=13, minute=30, second=0),
                'close': datetime.time(hour=15, minute=0, second=0),
            },
        ]
        for trading_time in trading_time_list:
            if trading_time['open'] <= t <= trading_time['close']:
                return True
        return False

    def _make_close_order(self, order: Order):
        # 数据库中的委托单
        db_order = db_session.query(TQOrder).filter_by(order_id=order.order_id).one()

        # 计算平仓单参数
        if order.direction == 'BUY':
            new_direction = 'SELL'
            new_price = order.limit_price + close_spread
            new_action = '卖平'
        else:
            new_direction = 'BUY'
            new_price = order.limit_price - close_spread
            new_action = '买平'

        # 下平仓单
        order_close = self._api.insert_order(
            symbol=self._symbol,
            direction=new_direction,
            offset='CLOSE',
            volume=order.volume_orign,
            limit_price=new_price
        )
        # log提示
        logger.info(
            f'【动作】{new_action}, {order_close.limit_price + close_spread}, '
            f'{order_close.volume_orign}手。'
        )
        # 更新数据库
        db_order.status = 'FINISHED'
        db_order.opponent = order_close.order_id
        db_session.add(TQOrder(datetime=current_datetime,
                               order_id=order_close.order_id,
                               direction_id=id_sell,
                               offset_id=id_close,
                               price=order_close.limit_price,
                               volume=order_close.volume_orign,
                               status='ALIVE',
                               opponent=order.order_id
                               )
                       )
        db_session.commit()

    def run(self):
        # 天勤数据
        tq_account: Account = self._api.get_account()
        tq_position: Position = self._api.get_position(self._symbol)
        tq_quote: Quote = self._api.get_quote(self._symbol)
        tq_order: Entity = self._api.get_order()

        try:
            while True:
                if not self._api.wait_update(deadline=time.time() + self._timeout):
                    print('未在超时限制内接收到数据。')

                if self._api.is_changing(tq_quote, ['ask_price1', 'bid_price1']):
                    # tq_quote 中的信息
                    price_ask = tq_quote.ask_price1  # 当前卖一价
                    price_bid = tq_quote.bid_price1  # 当前买一价
                    current_datetime = datetime.datetime.fromisoformat(tq_quote.datetime)  # 当前 datetime
                    current_time = current_datetime.time()  # 当前 time

                    # log 当前状态
                    if not self.is_trading_time(current_time):
                        self._logger.info(f'【状态】时间: {current_datetime}。——非交易时间')
                    else:
                        self._logger.info(
                            '【状态】时间: {dt}, 可用资金: {cash:,.2f}, 持多: {long}, 持空: {short}, 未成交: {lots}'.format(
                                dt=current_datetime,
                                cash=tq_account.available,
                                long=tq_position.pos_long,
                                short=tq_position.pos_short,
                                lots=sum(order.volume_left for order_id, order in tq_order.items() if
                                         order.status == 'ALIVE')
                            )
                        )

                        # 开仓
                        # 1、总持仓（多仓 + 空仓）手数 < 【策略】最大持仓手数；
                        # 2、买一价挂单手数 ＋　卖一价挂单手数　＋　每笔委托手数　<　【策略】每价位手数
                        # 3、根据 均线？MACD？判断多空。
                        if ((tq_position.pos_long + tq_position.pos_short) < max_position and
                                lots_at_price(tq_order, price_ask) + lots_at_price(tq_order,
                                                                                   price_bid) + volume_per_order <
                                volume_per_price):
                            order_open_buy = self._api.insert_order(symbol=symbol,
                                                              direction='BUY',
                                                              offset='OPEN',
                                                              volume=volume_per_order,
                                                              limit_price=price_bid
                                                              )
                            self._logger.info(
                                f'【动作】时间: {current_datetime}, 买开, {order_open_buy.limit_price}, '
                                f'{order_open_buy.volume_orign}手, 编号: {order_open_buy.order_id}。'
                            )
                            db_session.add(
                                TQOrder(
                                    datetime=current_datetime,
                                    order_id=order_open_buy.order_id,
                                    direction_id=id_buy,
                                    offset_id=id_open,
                                    price=order_open_buy.limit_price,
                                    volume=order_open_buy.volume_orign,
                                    status='ALIVE'
                                )
                            )
                            db_session.commit()

                        if self._api.is_changing(tq_order):
                            x_order_id: str
                            x_order: Order

                            for x_order_id, x_order in tq_order.items():
                                if x_order.status == 'FINISHED':
                                    self._logger.info(
                                        f'【成交】{x_order.direction} {x_order.offset},'
                                        f' {x_order.limit_price}, {x_order.volume_orign}手。'
                                    )

                                    db_tq_order = db_session.query(TQOrder).filter_by(order_id=x_order_id).one()

                                    # 已成交的委托单是开仓单且没有对面单
                                    if x_order.offset == 'OPEN' and db_tq_order.opponent is None:
                                        self._make_close_order(x_order)
                                    else:
                                        db_tq_order.status = 'FINISHED'
                                        db_session.commit()

                                        self._logger.info('【反馈】仓位平了。')
        except BacktestFinished:
            self._api.close()
            exit()


def scalping(api: TqApi, max_position: int = 10):
    strategy_name: str = 'Scalping'

    # 品种合约
    symbol: str = 'DCE.c2101'

    # 策略参数
    max_position: int = max_position    # 最大持仓手数
    close_spread: int = 1               # 平仓价差
    order_range: int = 3                # 挂单范围
    closeout_long: int = 5              # 多单强平点差
    closeout_short: int = 5             # 空单强平点差
    volume_per_order: int = 2           # 每笔委托手数
    volume_per_price: int = volume_per_order * 3    # 每价位手数

    # 品种合约交易时间
    # TODO: 应该改成从数据库查询
    trading_time_list: List[Dict[str, time]] = [
        {
            'open': datetime.time(hour=21, minute=0, second=0),
            'close': datetime.time(hour=23, minute=0, second=0),
        },
        {
            'open': datetime.time(hour=9, minute=0, second=0),
            'close': datetime.time(hour=11, minute=30, second=0),
        },
        {
            'open': datetime.time(hour=13, minute=30, second=0),
            'close': datetime.time(hour=15, minute=0, second=0),
        },
    ]

    # 天勤量化参数
    # 超时 5 秒
    timeout: int = 5

    logger: logging.Logger = get_logger(strategy_name)

    # 策略相关
    tq_account: Account = api.get_account()
    tq_position: Position = api.get_position(symbol)
    tq_quote: Quote = api.get_quote(symbol)
    tq_order: Entity = api.get_order()

    # 临时变量

    klines = api.get_kline_serial(symbol=symbol, duration_seconds=60)
    macd = MACD(klines, 12, 26, 9)

    id_open: int = db_session.query(TQOffset).filter_by(value='OPEN').one().id
    id_close: int = db_session.query(TQOffset).filter_by(value='CLOSE').one().id
    id_close_today: int = db_session.query(TQOffset).filter_by(value='CLOSETODAY').one().id
    id_buy: int = db_session.query(TQDirection).filter_by(value='BUY').one().id
    id_sell: int = db_session.query(TQDirection).filter_by(value='SELL').one().id

    db_tq_order: TQOrder

    # 策略
    try:
        while True:
            deadline: float = time.time() + timeout
            if not api.wait_update(deadline=deadline):
                print('未在超时限制内接收到数据。')

            if api.is_changing(tq_quote, ['ask_price1', 'bid_price1']):
                # tq_quote 中的信息
                price_ask = tq_quote.ask_price1  # 当前卖一价
                price_bid = tq_quote.bid_price1  # 当前买一价
                current_datetime = datetime.datetime.fromisoformat(tq_quote.datetime)  # 当前 datetime
                current_time = current_datetime.time()  # 当前 time

                # log 当前状态
                if not is_trading_time(current_time, trading_time_list):
                    logger.info(f'【状态】时间: {current_datetime}。——非交易时间')
                else:
                    logger.info(
                        '【状态】时间: {dt}, 可用资金: {cash:,.2f}, 持多: {long}, 持空: {short}, 未成交: {lots}'.format(
                            dt=current_datetime,
                            cash=tq_account.available,
                            long=tq_position.pos_long,
                            short=tq_position.pos_short,
                            lots=sum(order.volume_left for order_id, order in tq_order.items() if order.status == 'ALIVE')
                        )
                    )

                    # 开仓
                    # 1、总持仓（多仓 + 空仓）手数 < 【策略】最大持仓手数；
                    # 2、买一价挂单手数 ＋　卖一价挂单手数　＋　每笔委托手数　<　【策略】每价位手数
                    # 3、根据 均线？MACD？判断多空。
                    if ((tq_position.pos_long + tq_position.pos_short) < max_position and
                            lots_at_price(tq_order, price_ask) + lots_at_price(tq_order, price_bid) + volume_per_order <
                            volume_per_price):
                        order_open_buy = api.insert_order(symbol=symbol,
                                                          direction='BUY',
                                                          offset='OPEN',
                                                          volume=volume_per_order,
                                                          limit_price=price_bid
                                                          )
                        logger.info(
                            f'【动作】时间: {current_datetime}, 买开, {order_open_buy.limit_price}, '
                            f'{order_open_buy.volume_orign}手, 编号: {order_open_buy.order_id}。'
                        )
                        db_session.add(
                            TQOrder(
                                datetime=current_datetime,
                                order_id=order_open_buy.order_id,
                                direction_id=id_buy,
                                offset_id=id_open,
                                price=order_open_buy.limit_price,
                                volume=order_open_buy.volume_orign,
                                status='ALIVE'
                            )
                        )
                        db_session.commit()

                    if api.is_changing(tq_order):
                        x_order_id: str
                        x_order: Order

                        for x_order_id, x_order in tq_order.items():
                            if x_order.status == 'FINISHED':
                                logger.info(
                                    f'【成交】{x_order.direction} {x_order.offset},'
                                    f' {x_order.limit_price}, {x_order.volume_orign}手。'
                                )

                                db_tq_order = db_session.query(TQOrder).filter_by(order_id=x_order_id).one()

                                # 已成交的委托单是开仓单且没有对面单
                                if x_order.offset == 'OPEN' and db_tq_order.opponent is None:
                                    make_close_order(x_order)


                                else:
                                    db_tq_order.status = 'FINISHED'
                                    db_session.commit()

                                    logger.info('【反馈】仓位平了。')
    except BacktestFinished:
        api.close()
        exit()
