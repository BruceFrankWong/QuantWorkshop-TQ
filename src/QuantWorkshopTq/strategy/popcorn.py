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
from tqsdk.objs import Account, Position, Quote, Order
from tqsdk.entity import Entity

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
    {'yyyy_mm': '2016-01', 'symbol': '1605'},  # 换月日期：2015-09-18
    {'yyyy_mm': '2016-02', 'symbol': '1605'},
    {'yyyy_mm': '2016-03', 'symbol': '1609'},  # 换月日期：2016-02-22
    {'yyyy_mm': '2016-04', 'symbol': '1701'},  # 换月日期：2016-03-30
    {'yyyy_mm': '2016-05', 'symbol': '1701'},
    {'yyyy_mm': '2016-06', 'symbol': '1701'},
    {'yyyy_mm': '2016-07', 'symbol': '1701'},
    {'yyyy_mm': '2016-08', 'symbol': '1701'},
    {'yyyy_mm': '2016-09', 'symbol': '1701'},
    {'yyyy_mm': '2016-10', 'symbol': '1701'},
    {'yyyy_mm': '2016-11', 'symbol': '1701'},
    {'yyyy_mm': '2016-12', 'symbol': '1705'},  # 换月日期：2016-11-22
    {'yyyy_mm': '2017-01', 'symbol': '1705'},
    {'yyyy_mm': '2017-02', 'symbol': '1705'},
    {'yyyy_mm': '2017-03', 'symbol': '1709'},  # 换月日期：2017-03-14
    {'yyyy_mm': '2017-04', 'symbol': '1709'},
    {'yyyy_mm': '2017-05', 'symbol': '1709'},
    {'yyyy_mm': '2017-06', 'symbol': '1709'},
    {'yyyy_mm': '2017-07', 'symbol': '1709'},
    {'yyyy_mm': '2017-08', 'symbol': '1801'},  # 换月日期：2017-08-03
    {'yyyy_mm': '2017-09', 'symbol': '1801'},
    {'yyyy_mm': '2017-10', 'symbol': '1801'},
    {'yyyy_mm': '2017-11', 'symbol': '1801'},
    {'yyyy_mm': '2017-12', 'symbol': '1805'},  # 换月日期：2017-12-07
    {'yyyy_mm': '2018-01', 'symbol': '1805'},
    {'yyyy_mm': '2018-02', 'symbol': '1805'},
    {'yyyy_mm': '2018-03', 'symbol': '1805'},
    {'yyyy_mm': '2018-04', 'symbol': '1809'},  # 换月日期：2018-03-30
    {'yyyy_mm': '2018-05', 'symbol': '1809'},
    {'yyyy_mm': '2018-06', 'symbol': '1809'},
    {'yyyy_mm': '2018-07', 'symbol': '1901'},  # 换月日期：2018-07-11
    {'yyyy_mm': '2018-08', 'symbol': '1901'},
    {'yyyy_mm': '2018-09', 'symbol': '1901'},
    {'yyyy_mm': '2018-10', 'symbol': '1901'},
    {'yyyy_mm': '2018-11', 'symbol': '1901'},
    {'yyyy_mm': '2018-12', 'symbol': '1905'},  # 换月日期：2018-11-20
    {'yyyy_mm': '2019-01', 'symbol': '1905'},
    {'yyyy_mm': '2019-02', 'symbol': '1905'},
    {'yyyy_mm': '2019-03', 'symbol': '1905'},
    {'yyyy_mm': '2019-04', 'symbol': '1909'},  # 换月日期：2019-03-27
    {'yyyy_mm': '2019-05', 'symbol': '1909'},
    {'yyyy_mm': '2019-06', 'symbol': '1909'},
    {'yyyy_mm': '2019-07', 'symbol': '1909'},
    {'yyyy_mm': '2019-08', 'symbol': '2001'},  # 换月日期：2019-08-06
    {'yyyy_mm': '2019-09', 'symbol': '2001'},
    {'yyyy_mm': '2019-10', 'symbol': '2001'},
    {'yyyy_mm': '2019-11', 'symbol': '2001'},
    {'yyyy_mm': '2019-12', 'symbol': '2005'},  # 换月日期：2019-12-03
    {'yyyy_mm': '2020-01', 'symbol': '2005'},
    {'yyyy_mm': '2020-02', 'symbol': '2005'},
    {'yyyy_mm': '2020-03', 'symbol': '2009'},  # 换月日期：2020-03-11
    {'yyyy_mm': '2020-04', 'symbol': '2009'},
    {'yyyy_mm': '2020-05', 'symbol': '2009'},
    {'yyyy_mm': '2020-06', 'symbol': '2009'},
    {'yyyy_mm': '2020-07', 'symbol': '2009'},
    {'yyyy_mm': '2020-08', 'symbol': '2101'},  # 换月日期：2020-08-07
    {'yyyy_mm': '2020-09', 'symbol': '2101'},
]


class PopcornStrategy(StrategyBase):
    _name: str = 'Popcorn'

    _margin_per_lot: float = 2000.0  # 每手保证金（大约）

    _close_fluctuation: int
    _closeout: int
    _lots_per_order: int
    _max_fluctuation: int

    _order_manager: QWOrderManager

    def __init__(self,
                 api: TqApi,
                 capital: float,
                 safety_rate: float,
                 close_fluctuation: int,  # 获利价差
                 max_fluctuation: int,  # 报价范围
                 closeout: int,  # 强平价差
                 lots_per_order: int,  # 每笔委托手数
                 lots_per_price: int
                 ):
        super().__init__(api=api, symbol='DCE.c2101', capital=capital, safety_rate=safety_rate)
        self._closeout = closeout
        self._close_fluctuation = close_fluctuation
        self._lots_per_order = lots_per_order
        self._lots_per_price = lots_per_price
        self._max_fluctuation = max_fluctuation

        self._order_manager = QWOrderManager()

        self._tq_position = self._api.get_position(self._symbol)

        self._trading_time_list = [
            QWTradingTime(time(hour=21, minute=0, second=0), time(hour=23, minute=0, second=0)),
            QWTradingTime(time(hour=9, minute=0, second=0), time(hour=11, minute=30, second=0)),
            QWTradingTime(time(hour=13, minute=30, second=0), time(hour=15, minute=0, second=0)),
        ]

    @property
    def max_lots(self) -> int:
        """最大手数。
        最大手数 = (账户资金 × 安全比例 ) / 每手保证金
        """
        return math.floor(self._capital * self._safety_rate / self._margin_per_lot)

    @property
    def available_lots(self) -> int:
        """可用手数。
        可用手数 = 最大手数 - 持仓手数 - 挂单手数
        """
        return self.max_lots - self._tq_position.pos_long - self._tq_position.pos_short

    def is_open_condition_met(self, t: time, p: float) -> bool:
        """开仓条件是否满足
        开仓条件：
        1、在交易时间段内；
        2、可用手数 > 0；
        3、当前价位上手数 < 最大价位手数；
        """
        if (self.is_valid_trading_time(t) and
                self.available_lots > 0 and
                self._order_manager.unfilled_lots_at_price(p) < self._lots_per_price):
            return True
        else:
            return False

    def run(self):
        current_datetime: datetime
        current_time: time
        order_open: Order
        order_close: Order
        ordered_lots: int

        self._logger.info(f'资金: {self._capital}, 最大持仓: {self.max_lots}')
        while True:
            self._api.wait_update()

            # 当盘口行情发生变化
            if self._api.is_changing(self._tq_quote, ['ask_price1', 'bid_price1']):

                # tq_quote 中的信息
                current_ask_price1 = self._tq_quote.ask_price1  # 当前卖一价
                current_bid_price1 = self._tq_quote.bid_price1  # 当前买一价
                current_datetime = datetime.fromisoformat(self._tq_quote.datetime)  # 当前 datetime
                current_time = current_datetime.time()                              # 当前 time

                # log 当前状态
                self.log_status(datetime.fromisoformat(self._tq_quote.datetime))

                # 开仓条件满足时，开仓

                ordered_lots: int = (self._order_manager.unfilled_lots_at_price(current_ask_price1) +
                                     self._order_manager.unfilled_lots_at_price(current_bid_price1))
                self._logger.info(f'计算已开仓手数: {ordered_lots}')
                if (self.is_valid_trading_time(current_time) and
                        (self._tq_position.pos_long + self._tq_position.pos_short) < self.max_lots and
                        ordered_lots < self._lots_per_price):
                    order_open = self._api.insert_order(symbol=self._symbol,
                                                        direction='BUY',
                                                        offset='OPEN',
                                                        volume=self._lots_per_order,
                                                        limit_price=current_ask_price1
                                                        )
                    self._api.wait_update()  # 等待生成 order_id
                    self._order_manager.add(order_open)
                    # print(self._tq_ticks.iloc[-1])
                    self._logger.info(
                        self._message_trade.format(datetime=self._tq_quote.datetime,
                                                   capital=self._tq_account.available,
                                                   lots=self._order_manager.unfilled_lots,
                                                   D=order_open.direction,
                                                   O=order_open.offset,
                                                   volume=order_open.volume_orign,
                                                   price=order_open.limit_price,
                                                   order_id=order_open.exchange_order_id
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

            # TODO: 为什么 tq_order 内部数据类型是 tqsdk.objs.Quote？ 不应该是 tqsdk.objs.Order 吗？
            # if self._api.is_changing(self._tq_order):
            #     tq_order_id: str
            #
            #     for tq_order_id in self._tq_order:
            #         print('TQ order id :', tq_order_id, '; object type: ', type(self._tq_quote))
            #         print(self._tq_quote.items())

            # 尝试平仓
            for order in self._order_manager.unfilled_order_list:
                if order.status == 'FINISHED':
                    self._logger.info(self._message_fill.format(datetime=self._tq_quote.datetime,
                                                                volume=order.volume_orign,
                                                                price=order.limit_price,
                                                                order_id=order.exchange_order_id)
                                      )
                    self._order_manager.fill(order)
                    if order.offset == 'OPEN':
                        if order.direction == 'BUY':
                            order_close = self._api.insert_order(symbol=self._symbol,
                                                                 direction='SELL',
                                                                 offset='CLOSE',
                                                                 volume=order.volume_orign,
                                                                 limit_price=order.limit_price + self._close_fluctuation
                                                                 )
                            self._api.wait_update()  # 等待生成 order_id
                            self._order_manager.add(order_close)
                            self._logger.info(self._message_close_buy.format(datetime=self._tq_quote.datetime,
                                                                             volume=order_close.volume_orign,
                                                                             price=order_close.limit_price,
                                                                             order_id=order_close.exchange_order_id)
                                              )
                        else:
                            order_close = self._api.insert_order(symbol=self._symbol,
                                                                 direction='BUY',
                                                                 offset='CLOSE',
                                                                 volume=order.volume_orign,
                                                                 limit_price=order.limit_price - self._close_fluctuation
                                                                 )
                            self._api.wait_update()  # 等待生成 order_id
                            self._order_manager.add(order_close)
                            self._logger.info(self._message_close_sell.format(datetime=self._tq_quote.datetime,
                                                                              volume=order_close.volume_orign,
                                                                              price=order_close.limit_price,
                                                                              order_id=order_close.exchange_order_id)
                                              )
                    else:
                        self._logger.info(self._message_close_buy.format(datetime=self._tq_quote.datetime,
                                                                         volume=order.volume_orign,
                                                                         price=order.limit_price,
                                                                         order_id=order.exchange_order_id)
                                          )

            # self._api.wait_update()
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
