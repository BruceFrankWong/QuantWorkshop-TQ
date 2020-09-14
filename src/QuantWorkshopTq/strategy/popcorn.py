# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'


"""
爆米花策略
无脑买入，加一跳卖出。
根据MA判断方向。
"""

from typing import Union, List, Dict
import os
import logging
import math
from datetime import datetime, date, time
from enum import Enum

from pandas import DataFrame
from tqsdk import TqApi, TqBacktest, TqSim, TargetPosTask
from tqsdk.objs import Account, Position, Quote, Order, Entity

from .base import StrategyBase
from ..define import (
    QWDirection,
    QWOffset,
    QWTradingTime,
    QWOrder,
    QWOrderManager,
    QWPosition,
    QWPositionManager
)


MAIN_CONTRACT: list = [
    {'yyyy_mm': '2016-01', 'symbol': '1605'},      # 换月日期：2015-09-18
    {'yyyy_mm': '2016-02', 'symbol': '1605'},
    {'yyyy_mm': '2016-03', 'symbol': '1609'},      # 换月日期：2016-02-22
    {'yyyy_mm': '2016-04', 'symbol': '1701'},      # 换月日期：2016-03-30
    {'yyyy_mm': '2016-05', 'symbol': '1701'},
    {'yyyy_mm': '2016-06', 'symbol': '1701'},
    {'yyyy_mm': '2016-07', 'symbol': '1701'},
    {'yyyy_mm': '2016-08', 'symbol': '1701'},
    {'yyyy_mm': '2016-09', 'symbol': '1701'},
    {'yyyy_mm': '2016-10', 'symbol': '1701'},
    {'yyyy_mm': '2016-11', 'symbol': '1701'},
    {'yyyy_mm': '2016-12', 'symbol': '1705'},      # 换月日期：2016-11-22
    {'yyyy_mm': '2017-01', 'symbol': '1705'},
    {'yyyy_mm': '2017-02', 'symbol': '1705'},
    {'yyyy_mm': '2017-03', 'symbol': '1709'},      # 换月日期：2017-03-14
    {'yyyy_mm': '2017-04', 'symbol': '1709'},
    {'yyyy_mm': '2017-05', 'symbol': '1709'},
    {'yyyy_mm': '2017-06', 'symbol': '1709'},
    {'yyyy_mm': '2017-07', 'symbol': '1709'},
    {'yyyy_mm': '2017-08', 'symbol': '1801'},      # 换月日期：2017-08-03
    {'yyyy_mm': '2017-09', 'symbol': '1801'},
    {'yyyy_mm': '2017-10', 'symbol': '1801'},
    {'yyyy_mm': '2017-11', 'symbol': '1801'},
    {'yyyy_mm': '2017-12', 'symbol': '1805'},      # 换月日期：2017-12-07
    {'yyyy_mm': '2018-01', 'symbol': '1805'},
    {'yyyy_mm': '2018-02', 'symbol': '1805'},
    {'yyyy_mm': '2018-03', 'symbol': '1805'},
    {'yyyy_mm': '2018-04', 'symbol': '1809'},      # 换月日期：2018-03-30
    {'yyyy_mm': '2018-05', 'symbol': '1809'},
    {'yyyy_mm': '2018-06', 'symbol': '1809'},
    {'yyyy_mm': '2018-07', 'symbol': '1901'},      # 换月日期：2018-07-11
    {'yyyy_mm': '2018-08', 'symbol': '1901'},
    {'yyyy_mm': '2018-09', 'symbol': '1901'},
    {'yyyy_mm': '2018-10', 'symbol': '1901'},
    {'yyyy_mm': '2018-11', 'symbol': '1901'},
    {'yyyy_mm': '2018-12', 'symbol': '1905'},      # 换月日期：2018-11-20
    {'yyyy_mm': '2019-01', 'symbol': '1905'},
    {'yyyy_mm': '2019-02', 'symbol': '1905'},
    {'yyyy_mm': '2019-03', 'symbol': '1905'},
    {'yyyy_mm': '2019-04', 'symbol': '1909'},      # 换月日期：2019-03-27
    {'yyyy_mm': '2019-05', 'symbol': '1909'},
    {'yyyy_mm': '2019-06', 'symbol': '1909'},
    {'yyyy_mm': '2019-07', 'symbol': '1909'},
    {'yyyy_mm': '2019-08', 'symbol': '2001'},      # 换月日期：2019-08-06
    {'yyyy_mm': '2019-09', 'symbol': '2001'},
    {'yyyy_mm': '2019-10', 'symbol': '2001'},
    {'yyyy_mm': '2019-11', 'symbol': '2001'},
    {'yyyy_mm': '2019-12', 'symbol': '2005'},      # 换月日期：2019-12-03
    {'yyyy_mm': '2020-01', 'symbol': '2005'},
    {'yyyy_mm': '2020-02', 'symbol': '2005'},
    {'yyyy_mm': '2020-03', 'symbol': '2009'},      # 换月日期：2020-03-11
    {'yyyy_mm': '2020-04', 'symbol': '2009'},
    {'yyyy_mm': '2020-05', 'symbol': '2009'},
    {'yyyy_mm': '2020-06', 'symbol': '2009'},
    {'yyyy_mm': '2020-07', 'symbol': '2009'},
    {'yyyy_mm': '2020-08', 'symbol': '2101'},      # 换月日期：2020-08-07
    {'yyyy_mm': '2020-09', 'symbol': '2101'},
]


class PopcornStrategy(StrategyBase):
    _name: str = 'Popcorn'

    _margin_per_lot: float = 2000.0     # 每手保证金（大约）

    _close_fluctuation: int
    _closeout: int
    _lots_per_order: int
    _max_fluctuation: int

    _position: Position
    _quote: Quote
    _realtime_order: Entity

    _position_manager: QWPositionManager
    _order_manager: QWOrderManager

    def __init__(self,
                 api: TqApi,
                 capital: float,
                 safety_rate: float,
                 close_fluctuation: int,    # 获利价差
                 max_fluctuation: int,      # 报价范围
                 closeout: int,             # 强平价差
                 lots_per_order: int,       # 每笔委托手数
                 lots_per_price: int
                 ):
        super().__init__(api=api, symbol='DCE.c2101', capital=capital, safety_rate=safety_rate)
        self._closeout = closeout
        self._close_fluctuation = close_fluctuation
        self._lots_per_order = lots_per_order
        self._lots_per_price = lots_per_price
        self._max_fluctuation = max_fluctuation

        self._position_manager = QWPositionManager()
        self._order_manager = QWOrderManager()

        self._trading_time_list = [
            QWTradingTime(time(hour=21, minute=0, second=0), time(hour=23, minute=0, second=0)),
            QWTradingTime(time(hour=9, minute=0, second=0), time(hour=11, minute=30, second=0)),
            QWTradingTime(time(hour=13, minute=30, second=0), time(hour=15, minute=0, second=0)),
        ]

    @property
    def position_max(self) -> int:
        """最大持仓。
        最大持仓 = (账户资金 × 安全比例 ) / 每手保证金
        """
        return math.floor(self._capital * self._safety_rate / self._margin_per_lot)

    @property
    def position_filled(self) -> int:
        """已有持仓。

        :return:
        """
        return self._position_manager.total_lots

    @property
    def position_ordered(self) -> int:
        """挂单持仓。
        挂单持仓 即已发出但尚未成交的指令单，同样占用资金。
        :return:
        """
        return self._order_manager.total_lots

    @property
    def position_available(self) -> int:
        """可用持仓。
        可用持仓 = 最大持仓 - 已有持仓 - 挂单持仓
        """
        return self.position_max - self.position_filled - self.position_ordered

    def run(self):
        current_time: time
        order: Order
        order_reverse: Order
        order_to_be_closed: List[Order] = []

        # self._ticks = self._api.get_tick_serial(self._symbol)
        # self._klines = self._api.get_kline_serial(self._symbol, 60)
        self._quote = self._api.get_quote(self._symbol)
        self._position = self._api.get_position()
        self._realtime_order = self._api.get_order()

        self._logger.info(f'资金: {self._capital}, 最大持仓: {self.position_max}')
        while True:
            self._api.wait_update()

            # 尝试开仓
            if self._api.is_changing(self._quote, 'ask_price1'):
                current_ask_price1 = self._quote.ask_price1
                current_bid_price1 = self._quote.bid_price1

                current_time = datetime.fromisoformat(self._quote.datetime).time()

                # 尝试开仓
                if (self.is_valid_trading_time(current_time) and
                        self.position_available > 0 and
                        self._position_manager.lots_at_price(current_ask_price1) < self._lots_per_price):
                    order = self._api.insert_order(symbol=self._symbol,
                                                   direction='BUY',
                                                   offset='OPEN',
                                                   volume=self._lots_per_order,
                                                   limit_price=current_ask_price1
                                                   )
                    self._api.wait_update()     # 等待生成 order_id
                    self._order_manager.add(QWOrder(order_id=order.exchange_order_id,
                                                    price=order.limit_price,
                                                    lots=order.volume_orign,
                                                    direction=QWDirection.Buy,
                                                    offset=QWOffset.Open
                                                    )
                                            )
                    order_to_be_closed.append(order)
                    self._logger.info(self._message_open_buy.format(datetime=self._quote.datetime,
                                                                    volume=self._lots_per_order,
                                                                    price=current_ask_price1,
                                                                    order_id=order.exchange_order_id
                                                                    )
                                      )

                # 尝试撤单
                # if self.is_open_condition(self._ticks.iloc[-1]['ask_price1']):
                #     order = self._api.insert_order(symbol=self._symbol,
                #                                    direction='BUY',
                #                                    offset='OPEN',
                #                                    volume=self._lots_per_order,
                #                                    limit_price=self._ticks.iloc[-1]['ask_price1']
                #                                    )
                #     self._order_manager.add(order)

            # 尝试平仓
            for order in order_to_be_closed:
                if order.status == 'FINISHED':
                    if order.direction == 'BUY':
                        order_reverse = self._api.insert_order(symbol=self._symbol,
                                                               direction='SELL',
                                                               offset='CLOSE',
                                                               volume=order.volume_orign,
                                                               limit_price=order.limit_price + 1
                                                               )
                        # self._order_manager.add(order)
                        order_to_be_closed.remove(order)
                        self._logger.info(self._message_close_buy.format(datetime=self._quote.datetime,
                                                                         volume=order.volume_orign,
                                                                         price=order.limit_price + 1,
                                                                         order_id=order.exchange_order_id)
                                          )
                    else:
                        order_reverse = self._api.insert_order(symbol=self._symbol,
                                                               direction='BUY',
                                                               offset='CLOSE',
                                                               volume=order.volume_orign,
                                                               limit_price=order.limit_price - 1
                                                               )
                        # self._order_manager.add(order)
                        order_to_be_closed.remove(order)

            self._api.wait_update()
            # if self._api.is_changing(self._realtime_order):
            #     self._logger.info('order变化', self._realtime_order.items())

        # while self._status['position'] == 0:
        #     self._api.wait_update()
        #
        #     if self._api.is_changing(self.quote, 'last_price'):
        #         print("最新价: %f" % self.quote.last_price)
        #         if self.quote.last_price > self.donchian_channel_high:  # 当前价>唐奇安通道上轨，买入1个Unit；(持多仓)
        #             print("当前价>唐奇安通道上轨，买入1个Unit(持多仓): %d 手" % self.unit)
        #             self.set_position(self.state["position"] + self.unit)
        #         elif self.quote.last_price < self.donchian_channel_low:  # 当前价<唐奇安通道下轨，卖出1个Unit；(持空仓)
        #             print("当前价<唐奇安通道下轨，卖出1个Unit(持空仓): %d 手" % self.unit)
        #             self.set_position(self.state["position"] - self.unit)
