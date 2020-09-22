# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'

from typing import Dict, List, Optional
import logging
import os.path
import time
import datetime

from tqsdk import TqApi, TargetPosTask
from tqsdk.objs import Account, Position, Quote, Order
from tqsdk.entity import Entity
from tqsdk.tafunc import ema
from pandas import DataFrame

from .base import StrategyBase


def _get_logger() -> logging.Logger:
    logger = logging.getLogger(f'Strategy')

    logger.setLevel(logging.DEBUG)
    # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s: - %(message)s',
    #                               datefmt='%Y-%m-%d %H:%M:%S')
    formatter = logging.Formatter('%(message)s')

    # 当前日期时间
    now: datetime.datetime = datetime.datetime.now()
    dt: str = now.strftime('%Y-%m-%d_%H-%M-%S')

    # 使用FileHandler输出到文件
    log_path: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'log')
    if not os.path.exists(log_path):
        os.mkdir(log_path)
    logger_file = logging.FileHandler(f'{log_path}/Strategy_{dt}.txt')
    logger_file.setLevel(logging.DEBUG)
    logger_file.setFormatter(formatter)

    # 使用StreamHandler输出到屏幕
    logger_screen = logging.StreamHandler()
    logger_screen.setLevel(logging.DEBUG)
    logger_screen.setFormatter(formatter)

    # 添加两个Handler
    logger.addHandler(logger_screen)
    logger.addHandler(logger_file)

    return logger


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


class OrderRecordItem(object):
    order: Order
    opponent: Optional[str]

    def __init__(self, order: Order, opponent: Optional[str] = None):
        self.order = order
        self.opponent = opponent


OrderRecord = Dict[str, OrderRecordItem]


def get_macd(df: DataFrame, fast: int = 12, slow: int = 26):
    df['diff'] = df['close'].ewm(adjust=False, alpha=2 / (short_ + 1), ignore_na=True).mean() - \
                   df['close'].ewm(adjust=False, alpha=2 / (long_ + 1), ignore_na=True).mean()
    df['dea'] = df['diff'].ewm(adjust=False, alpha=2 / (m + 1), ignore_na=True).mean()
    df['macd'] = 2 * (df['diff'] - df['dea'])


def scalping(api: TqApi):
    # 品种合约
    symbol: str = 'DCE.c2101'

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

    # 策略参数
    # 最大持仓 30 手
    max_position: int = 30
    # 平仓价差
    close_spread: int = 1
    # 挂单范围
    order_range: int = 3
    # 强平
    closeout: int = 5
    # 每笔委托手数
    lots_per_order: int = 2
    # 每价位手数
    lots_per_price: int = lots_per_order * 3

    # 天勤量化参数
    # 超时 5 秒
    timeout: int = 5

    logger: logging.Logger = _get_logger()

    # 策略相关
    tq_account: Account = api.get_account()
    tq_position: Position = api.get_position(symbol)
    tq_quote: Quote = api.get_quote(symbol)
    tq_order: Entity = api.get_order()

    order_record: OrderRecord = {}

    # 临时变量
    order_record_item: OrderRecordItem

    klines = api.get_kline_serial(symbol=symbol, duration_seconds=60)
    macd = get_macd(klines)
    # 策略
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
                        lots_at_price(tq_order, price_ask) + lots_at_price(tq_order, price_bid) + lots_per_order <
                        lots_per_price):
                    order = api.insert_order(symbol=symbol,
                                             direction='BUY',
                                             offset='OPEN',
                                             volume=lots_per_order,
                                             limit_price=price_bid
                                             )
                    order_record[order.order_id] = OrderRecordItem(order=order)
                    logger.info(
                        f'【动作】时间: {current_datetime}, 买开, {price_bid}, {lots_per_order}手, 编号: {order.order_id}。'
                    )

                if api.is_changing(tq_order):
                    order_id: str
                    order_item: Order

                    for order_id, order_item in tq_order.items():
                        if order_id not in order_record.keys():
                            raise RuntimeError('发现未监管委托单！')

                        if order_item.status == 'FINISHED':
                            logger.info(
                                f'【成交】{order_item.direction} {order_item.offset},'
                                f' {order_item.limit_price}, {order_item.volume_orign}手。'
                            )
                            if order_item.offset == 'OPEN' and order_record[order_id].opponent is None:
                                if order_item.direction == 'BUY':
                                    order = api.insert_order(symbol=symbol,
                                                             direction='SELL',
                                                             offset='CLOSE',
                                                             volume=order_item.volume_orign,
                                                             limit_price=order_item.limit_price + close_spread
                                                             )
                                    order_record[order_item.order_id].opponent = order.order_id
                                    order_record[order.order_id] = OrderRecordItem(order=order,
                                                                                   opponent=order_item.order_id
                                                                                   )
                                    logger.info(
                                        f'【动作】卖平, {order.limit_price + close_spread}, {order.volume_orign}手。'
                                    )
                                else:
                                    order = api.insert_order(symbol=symbol,
                                                             direction='BUY',
                                                             offset='CLOSE',
                                                             volume=order_item.volume_orign,
                                                             limit_price=order_item.limit_price - close_spread
                                                             )
                                    order_record[order_item.order_id].opponent = order.order_id
                                    order_record[order.order_id] = OrderRecordItem(order=order,
                                                                                   opponent=order_item.order_id
                                                                                   )
                                    logger.info(
                                        f'【动作】买平, {order.limit_price - close_spread}, {order.volume_orign}手。'
                                    )
                            else:
                                logger.info('【反馈】仓位平了。')

                        # # 如果:
                        # #     1, order 状态是已成交
                        # #     2, order id 不在 order_pair_list 中
                        # #     3, order 的 offset 是 open
                        # # 把 order id 加入 order_record 的 open 分支中。
                        # if order_id not in order_record:
                        #     # if o_item.status == 'ALIVE':
                        #     #     record_item = {'status': o_item.status, 'opponent': ''}
                        #     #     order_record[o_id] = record_item
                        #     # else:
                        #     #     raise RuntimeError('未监管委托单已终结！')
                        #     record_item = {'status': order_item.status, 'opponent': ''}
                        #     order_record[order_id] = record_item
                        #     # logger.info(f'【成交】, {o_item.limit_price}, {o_item.volume_orign}手。')
                        #     # if o_item.direction == 'BUY':
                        #     #     api.insert_order(symbol=symbol,
                        #     #                      direction='BUY',
                        #     #                      offset='OPEN',
                        #     #                      volume=lots_per_order,
                        #     #                      limit_price=price_bid
                        #     #                      )
