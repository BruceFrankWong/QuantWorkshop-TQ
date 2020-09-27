# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'


"""
本策略是所谓“刮头皮”策略。


"""


from typing import Dict, List, Optional
import time
import datetime

from tqsdk import TqApi, BacktestFinished
from tqsdk.objs import Account, Position, Quote, Order, Trade
from tqsdk.entity import Entity
from tqsdk.ta import MACD
from pandas import DataFrame
from sqlalchemy.orm.exc import NoResultFound

from . import (
    StrategyBase,
    StrategyParameter,
    db_session,
    BacktestOrder,
    BacktestTrade
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

    tq_account: Account
    tq_position: Position
    tq_quote: Quote
    tq_order: Entity

    price_ask: float
    price_bid: float

    def __init__(self, api: TqApi, settings: StrategyParameter):
        super().__init__(api=api, symbol='DCE.c2101', settings=settings)

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

        # 天勤数据
        self.tq_account = self.api.get_account()
        self.tq_position = self.api.get_position(self.symbol)
        self.tq_quote = self.api.get_quote(self.symbol)
        self.tq_order = self.api.get_order()

        self.price_ask = 0.0
        self.price_bid = 0.0

    def is_trading_time(self, t: datetime.datetime) -> bool:
        trading_time: Dict[str, datetime.time]
        for trading_time in self.trading_time:
            if trading_time['open'] <= t.time() <= trading_time['close']:
                return True
        return False

    def is_about_to_close(self, t: datetime.datetime) -> bool:
        """
        是否快要闭市。
        :param t: 当前日期时间。
        :return:
        """
        trading_time: Dict[str, datetime.time]
        seconds_current: int = t.hour * 3600 + t.minute * 60 + t.second
        seconds_close: int
        for trading_time in self.trading_time:
            seconds_close = trading_time['close'].hour * 3600 + trading_time['close'].minute * 60
            if trading_time['open'] < t.time() < trading_time['close'] and seconds_close - seconds_current < 120:
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
        order_close = self.api.insert_order(
            symbol=self.symbol,
            direction=new_direction,
            offset='CLOSE',
            volume=order.volume_orign,
            limit_price=new_price
        )
        # log提示
        self.logger.info(
            self._message_order.format(
                dt=datetime.datetime.now(),
                d='买' if order_close.direction == 'BUY' else '卖',
                o='开' if order_close.offset == 'OPEN' else '平',
                volume=order_close.volume_orign,
                price=order_close.limit_price,
                order_id=order_close.order_id
            )
        )
        # 更新数据库
        db_order = db_session.query(BacktestOrder).filter_by(order_id=order.order_id).one()
        db_order.status = 'FINISHED'
        db_order.opponent = order_close.order_id
        db_session.add(
            BacktestOrder(
                datetime=datetime.datetime.now(),
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
            db_order = db_session.query(BacktestOrder).filter_by(order_id=opponent_order_id).one()
            if db_order.opponent:
                raise ValueError(f'Order with id <{opponent_order_id}> already has opponent order.')
            else:
                db_order.opponent = order.order_id
        new_order: BacktestOrder = BacktestOrder(datetime=datetime.datetime.now(),
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
        return db_session.query(BacktestOrder).filter_by(status='ALIVE').all()

    @staticmethod
    def get_trade(trade_id: str) -> Optional[BacktestTrade]:
        try:
            return db_session.query(BacktestTrade).filter_by(trade_id=trade_id).one()
        except NoResultFound:
            return None

    def close_before_market_close(self):
        """
        收盘前平仓。
        :return:
        """
        order: Order
        # 撤单
        for order in self.get_unfilled_order():
            self.api.cancel_order(order.order_id)
            db_order = db_session.query(BacktestOrder).filter_by(order_id=order.order_id).one()
            db_order.status = '撤单'
        db_session.commit()

        if self.tq_position.pos_long > 0:
            # 在 买一价 上 卖平。
            order = self.api.insert_order(
                symbol=self.symbol,
                direction='SELL',
                offset='CLOSE',
                volume=self.tq_position.pos_long,
                limit_price=self.price_bid
            )
            db_session.add(
                BacktestOrder(
                    datetime=self._remote_dt,
                    order_id=order.order_id,
                    direction=order.direction,
                    offset=order.offset,
                    price=order.limit_price,
                    volume=order.volume_orign,
                    status='ALIVE',
                    opponent=order.order_id
                )
            )
            db_session.commit()

        if self.tq_position.pos_short > 0:
            # 在 卖一价 上 买平。
            order = self.api.insert_order(
                symbol=self.symbol,
                direction='BUY',
                offset='CLOSE',
                volume=self.tq_position.pos_short,
                limit_price=self.price_ask
            )
            db_session.add(
                BacktestOrder(
                    datetime=self._remote_dt,
                    order_id=order.order_id,
                    direction=order.direction,
                    offset=order.offset,
                    price=order.limit_price,
                    volume=order.volume_orign,
                    status='ALIVE',
                    opponent=order.order_id
                )
            )
            db_session.commit()

    def handle_orders(self, order: Order):
        """
        处理委托单回报。
        根据 Order.status， Order.volume_orign 和 Order.volume_left 判断:
            1, status = FINISHED
                1A, volume_left = volume_orign
                    全部撤单
                1B, 0 < volume_left < volume_orign
                    部分撤单
                1C, volume_left = 0
                    全部成交
            2, status = ALIVE
                2A, volume_left = volume_orign
                    报单
                2B, 0 < volume_left < volume_orign
                    部分成交
        :param order:
        :return:
        """
        db_order: BacktestOrder
        new_status: str

        if order.status == 'FINISHED':
            if order.volume_left > 0:
                if order.volume_left == order.volume_orign:
                    new_status = '全部撤单'
                else:
                    new_status = '全部撤单'

                try:
                    db_order = db_session.query(BacktestOrder).filter_by(order_id=order.order_id).one()
                    db_order.status = new_status
                    db_order.volume_left = order.volume_left
                    db_session.commit()
                except NoResultFound:
                    print('ERROR', order.order_id)
                    self.api.close()
                    exit()

                self.logger.info(
                    self._message_cancel.format(
                        dt=self._remote_dt,
                        d='买' if order.direction == 'BUY' else '卖',
                        o='开' if order.offset == 'OPEN' else '平',
                        volume=order.volume_left,
                        price=order.limit_price,
                        order_id=order.order_id
                    )
                )
            else:
                new_status = '全部成交'
        else:
            if order.volume_left == order.volume_orign:
                new_status = '报单'
                try:
                    db_order = db_session.query(BacktestOrder).filter_by(order_id=order.order_id).one()
                    if db_order:
                        raise RuntimeError('新报单不应该在数据库中有记录')
                except NoResultFound:
                    db_session.add(
                        BacktestOrder(
                            datetime=self._remote_dt,
                            order_id=order.order_id,
                            direction=order.direction,
                            offset=order.offset,
                            price=order.limit_price,
                            volume=order.volume_orign,
                            status='ALIVE'
                        )
                    )
                    db_session.commit()

            else:
                new_status = '部分成交'

        try:
            db_order = db_session.query(BacktestOrder).filter_by(order_id=order.order_id).one()

            # 撤单
            if order.status == 'FINISHED' and order.volume_left > 0:
                # 全部撤单
                if order.volume_left == order.volume_orign:
                    new_status = '全部撤单'

                # 部分撤单
                # order.volume_left < order.volume_orign
                else:
                    new_status = '部分撤单'

                db_order.status = new_status
                db_order.volume_left = order.volume_left
                db_session.commit()
                self.logger.info(
                    self._message_cancel.format(
                        dt=self._remote_dt,
                        d='买' if order.direction == 'BUY' else '卖',
                        o='开' if order.offset == 'OPEN' else '平',
                        volume=order.volume_left,
                        price=order.limit_price,
                        order_id=order.order_id
                    )
                )

            # 全部成交
            elif order.status == 'FINISHED' and order.volume_left == 0:
                self.logger.info(
                    self._message_fill.format(
                        dt=self._remote_dt,
                        o='买' if order.direction == 'BUY' else '卖',
                        d='开' if order.offset == 'OPEN' else '平',
                        volume=order.volume_orign,
                        price=order.limit_price,
                        order_id=order.order_id
                    )
                )

                # 已成交的委托单是开仓单且没有对面单
                if order.offset == 'OPEN' and db_order.opponent is None:
                    self._make_close_order(order)
                else:
                    db_order.status = 'FINISHED'
                    db_session.commit()

                    self.logger.info('【反馈】仓位平了。')

            # 部分成交
            elif order.status == 'ALIVE' and 0 < order.volume_left < order.volume_orign:
                # 如果委托单的 volume_left < volume_orign，即表示有成交。
                # 搜索该委托单的 trade_records，有新的（不在数据库中）的成交记录即确认成交。
                if order.volume_left < order.volume_orign:
                    for _, trade in order.trade_records.items():
                        if not self.get_trade(trade.trade_id):
                            # 向数据库添加新的成交记录
                            db_session.add(
                                BacktestTrade(
                                    order_id=order.order_id,
                                    trade_id=trade.trade_id,
                                    datetime=trade.trade_date_time,
                                    exchange_trade_id=trade.exchange_trade_id,
                                    exchange_id=trade.exchange_id,
                                    instrument_id=trade.instrument_id,
                                    direction=trade.direction,
                                    offset=trade.offset,
                                    price=trade.price,
                                    volume=trade.volume
                                )
                            )
                            db_session.commit()
                            # log
                            self._logger.info(
                                self._message_fill.format(
                                    dt=trade.trade_date_time,
                                    o='买' if trade.direction == 'BUY' else '卖',
                                    d='开' if trade.offset == 'OPEN' else '平',
                                    volume=trade.volume,
                                    price=trade.price,
                                    order_id=order.order_id,
                                    trade_id=trade.trade_id
                                )
                            )
                if order.status == 'FINISHED':
                    self.logger.info(
                        self._message_fill.format(
                            dt=self._remote_dt,
                            o='买' if order.direction == 'BUY' else '卖',
                            d='开' if order.offset == 'OPEN' else '平',
                            volume=order.volume_orign,
                            price=order.limit_price,
                            order_id=order.order_id
                        )
                    )

                    try:
                        db_tq_order = db_session.query(BacktestOrder).filter_by(order_id=order.order_id).one()

                        # 已成交的委托单是开仓单且没有对面单
                        if order.offset == 'OPEN' and db_tq_order.opponent is None:
                            self._make_close_order(order)
                        else:
                            db_tq_order.status = 'FINISHED'
                            db_session.commit()

                            self._logger.info('【反馈】仓位平了。')
                    except NoResultFound:
                        print('ERROR', order.order_id)
                        self.api.close()
                        exit()
                else:
                    self._logger.info(f'委托单编号: {order.order_id}, 状态: {order.status}, {order.last_msg}')

            # 超出判断的分支, 出错了.
            else:
                raise RuntimeError('委托单状态和手数超出认知')

        except NoResultFound:
            print('ERROR', order.order_id)
            self.api.close()
            exit()

    def run(self):
        # 局部变量
        open_order: Order       # 开仓委托单
        close_order: Order      # 平仓委托单
        remote_order: Order     # 经天勤从服务器发来的委托单
        remote_order_id: str
        remote_trade: Trade     # 成交记录，来自远端
        remote_trade_id: str

        try:
            while True:
                if not self.api.wait_update(deadline=time.time() + self._timeout):
                    print('未在超时限制内接收到数据。')

                if self.api.is_changing(self.tq_quote, ['ask_price1', 'bid_price1']):
                    # tq_quote 中的信息
                    self.price_ask = self.tq_quote.ask_price1  # 当前卖一价
                    self.price_bid = self.tq_quote.bid_price1  # 当前买一价
                    self._remote_dt = datetime.datetime.fromisoformat(self.tq_quote.datetime)  # 当前 datetime

                    # 非交易时间
                    if not self.is_trading_time(self._remote_dt):
                        self.logger.info(f'{self._remote_dt}, 【状态】, ——非交易时间')
                        continue

                    # log 当前状态
                    self.logger.info(
                        self._message_status.format(
                            dt=self._remote_dt,
                            cash=self.tq_account.available,
                            long=self.tq_position.pos_long,
                            short=self.tq_position.pos_short,
                            lots=sum(
                                order.volume_left for order_id, order in self.tq_order.items() if order.status == 'ALIVE'
                            )
                        )
                    )

                    # 临近收盘，平仓
                    if self.is_about_to_close(self._remote_dt):
                        self.close_before_market_close()

                    # 处理委托单回报
                    if self.api.is_changing(self.tq_order):
                        for remote_order_id, remote_order in self.tq_order.items():
                            self.handle_orders(remote_order)

                    # 开仓
                    # 1、总持仓（多仓 + 空仓）手数 < 【策略】最大持仓手数；
                    # 2、买一价挂单手数 ＋　卖一价挂单手数　＋　每笔委托手数　<　【策略】每价位手数
                    # 3、根据 均线？MACD？判断多空。
                    if ((self.tq_position.pos_long + self.tq_position.pos_short) < self._settings['max_position'] and
                            lots_at_price(self.tq_order, self.price_ask) + lots_at_price(self.tq_order,
                                                                               self.price_bid) + self._settings['volume_per_order'] <
                            self._settings['volume_per_price']):
                        order_open = self.api.insert_order(symbol=self.symbol,
                                                            direction='BUY',
                                                            offset='OPEN',
                                                            volume=self._settings['volume_per_order'],
                                                            limit_price=self.price_bid
                                                            )
                        self.logger.info(
                            self._message_order.format(
                                dt=self._remote_dt,
                                d='买' if order_open.direction == 'BUY' else '卖',
                                o='开' if order_open.offset == 'OPEN' else '平',
                                volume=order_open.volume_orign,
                                price=order_open.limit_price,
                                order_id=order_open.order_id
                            )
                        )
                        db_session.add(
                            BacktestOrder(
                                datetime=self._remote_dt,
                                order_id=order_open.order_id,
                                direction='BUY',
                                offset='OPEN',
                                price=order_open.limit_price,
                                volume=order_open.volume_orign,
                                status='ALIVE'
                            )
                        )
                        db_session.commit()

        except BacktestFinished:
            self.api.close()
            exit()
