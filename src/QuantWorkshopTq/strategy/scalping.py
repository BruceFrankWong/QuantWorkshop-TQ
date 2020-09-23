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

from . import (
    StrategyBase,
    StrategyParameter,
    get_logger,
    get_table_order,
    db_session,
    TQOrder,
    TQTrade
)


__all__ = 'strategy_parameter', 'Scalping'


parameter: List[str] = [
    'max_position',         # 最大持仓手数
    'close_spread',         # 平仓价差
    'order_range',          # 挂单范围
    'closeout_long',        # 多单强平点差
    'closeout_short',       # 空单强平点差
    'volume_per_order',     # 每笔委托手数
    'volume_per_price',     # 每价位手数
]
strategy_parameter = StrategyParameter(parameter)


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


class Scalping(StrategyBase):
    _strategy_name: str = 'Scalping'

    def __init__(self, api: TqApi, settings: StrategyParameter):
        super(Scalping, self).__init__(api=api, symbol='DCE.c2101', settings=settings)

        self.trading_time: List[Dict[str, datetime.time]] = [
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

    def is_trading_time(self, t: datetime.time) -> bool:
        trading_time: Dict[str, datetime.time]
        for trading_time in self.trading_time:
            if trading_time['open'] <= t <= trading_time['close']:
                return True
        return False

    def is_near_close(self, t: datetime.time) -> bool:
        trading_time: Dict[str, datetime.time]
        seconds_current: int = t.hour * 3600 + t.minute * 60 + t.second
        seconds_close: int
        for trading_time in self.trading_time:
            seconds_close = trading_time['close'].hour * 3600 + trading_time['close'].minute * 60
            if trading_time['open'] < t < trading_time['close'] and seconds_close - seconds_current < 60:
                return True
        return False

    def _make_close_order(self, order: Order):
        # 计算平仓单参数
        if order.direction == 'BUY':
            new_direction = 'SELL'
            new_price = order.limit_price + self._settings['close_spread']
            new_action = '卖平'
        else:
            new_direction = 'BUY'
            new_price = order.limit_price - self._settings['close_spread']
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
        self._logger.info(
            f'【动作】{new_action}, {order_close.limit_price + self._settings["close_spread"]}, '
            f'{order_close.volume_orign}手。'
        )
        # 更新数据库
        db_order = db_session.query(TQOrder).filter_by(order_id=order.order_id).one()
        db_order.status = 'FINISHED'
        db_order.opponent = order_close.order_id
        db_session.add(TQOrder(datetime=datetime.datetime.now(),
                               order_id=order_close.order_id,
                               direction=order_close.direction,
                               offset=order_close.offset,
                               price=order_close.limit_price,
                               volume=order_close.volume_orign,
                               status='ALIVE',
                               opponent=order.order_id
                               )
                       )
        db_session.commit()

    @staticmethod
    def db_add_order(order: Order, opponent_order_id: Optional[str] = None):
        if opponent_order_id:
            db_order = db_session.query(TQOrder).filter_by(order_id=opponent_order_id).one()
            if db_order.opponent:
                raise ValueError(f'Order with id <{opponent_order_id}> already has opponent order.')
            else:
                db_order.opponent = order.order_id
        new_order: TQOrder = TQOrder(datetime=datetime.datetime.now(),
                                     order_id=order.order_id,
                                     direction=order.direction,
                                     offset=order.offset,
                                     price=order.limit_price,
                                     volume=order.volume_orign,
                                     status='ALIVE',
                                     opponent=opponent_order_id
                                     )
        db_session.add(new_order)
        db_session.commit()

    @staticmethod
    def get_unfilled_order() -> List[Order]:
        return db_session.query(TQOrder).filter_by(status='ALIVE').all()

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
                        continue

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

                    # 临近收盘，平仓
                    if self.is_near_close(current_time):
                        # 撤单
                        for order in self.get_unfilled_order():
                            self._api.cancel_order(order.order_id)
                        if tq_position.pos_long > 0:
                            # 在 买一价 上 卖平。
                            self._api.insert_order(symbol=self._symbol,
                                                   direction='SELL',
                                                   offset='CLOSE',
                                                   volume=tq_position.pos_long,
                                                   limit_price=price_bid
                                                   )
                        if tq_position.pos_short > 0:
                            # 在 卖一价 上 买平。
                            self._api.insert_order(symbol=self._symbol,
                                                   direction='BUY',
                                                   offset='CLOSE',
                                                   volume=tq_position.pos_short,
                                                   limit_price=price_ask
                                                   )
                    # 委托单情况
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
                            else:
                                self._logger.info(f'委托单编号: {x_order.order_id}, 状态: {x_order.status}, {x_order.last_msg}')

                    # 开仓
                    # 1、总持仓（多仓 + 空仓）手数 < 【策略】最大持仓手数；
                    # 2、买一价挂单手数 ＋　卖一价挂单手数　＋　每笔委托手数　<　【策略】每价位手数
                    # 3、根据 均线？MACD？判断多空。
                    if ((tq_position.pos_long + tq_position.pos_short) < self._settings['max_position'] and
                            lots_at_price(tq_order, price_ask) + lots_at_price(tq_order,
                                                                               price_bid) + self._settings['volume_per_order'] <
                            self._settings['volume_per_price']):
                        order_open_buy = self._api.insert_order(symbol=self._symbol,
                                                                direction='BUY',
                                                                offset='OPEN',
                                                                volume=self._settings['volume_per_order'],
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
                                direction='BUY',
                                offset='OPEN',
                                price=order_open_buy.limit_price,
                                volume=order_open_buy.volume_orign,
                                status='ALIVE'
                            )
                        )
                        db_session.commit()

        except BacktestFinished:
            self._api.close()
            exit()
