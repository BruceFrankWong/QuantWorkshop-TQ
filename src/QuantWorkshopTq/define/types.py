# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'

from enum import Enum
from datetime import datetime, timezone, timedelta, time


# 北京时间，GMT+8
tz_beijing: timezone = timezone(timedelta(hours=8))

# 结算时间，GMT+11，以北京时间20：00为零点
tz_settlement: timezone = timezone(timedelta(hours=12))


class QWTradingStage(Enum):
    Evening = 0
    Morning = 1
    Afternoon = 2


evening = QWTradingStage.Evening
morning = QWTradingStage.Morning
afternoon = QWTradingStage.Afternoon


class QWDirection(Enum):
    Buy = 'BUY'
    Long = 'BUY'
    Ask = 'BUY'
    Sell = 'SELL'
    Short = 'SELL'
    Bid = 'SELL'


class QWOffset(Enum):
    Open = 'OPEN'
    Close = 'CLOSE'
    CloseToday = 'CLOSETODAY'


class QWOrderStatus(Enum):
    Alive = 'ALIVE'
    Finished = 'FINISHED'
    Canceled = 'CANCELED'


class QWExchange(Enum):
    SHFE = 'SHFE'
    DCE = 'DCE'
    CZCE = 'CZCE'
    CFFEX = 'CFFEX'
    INE = 'INE'


class Product(Enum):
    au = 'au'


product_list: dict = {
    QWExchange.SHFE: [
        'au',   # 黄金
        'ag',   # 白银
        'cu',   # 铜
        'al',   # 铝
        'zn',   # 锌
        'pb',   # 铅
        'ni',   # 镍
        'si',   # 锡
        'rb',   # 螺纹钢
        'wr',   # 线材
        'hc',   # 热轧卷板
        'ss',   # 不锈钢
        'fu',   # 燃油
        'lu',   # 低硫燃料油
        'bu',   # 沥青
        'ru',   # 天然橡胶
        'nr',   # 20号胶
    ],
    QWExchange.DCE: [
        'a',    # 豆一
        'b',    # 豆二
    ],
    QWExchange.CFFEX: [
        'IF',   # 沪深
        'IH',   # 上证
        'IC',   # 中证
        'TS',   # 两年期国债
        'TF',   # 五年期国债
        'T',    # 十年期国债
    ],
    QWExchange.INE: [
        'sc',   # 原油
    ]
}


option_product: dict = {
    QWExchange.SHFE: [
        'au',
        'cu',
        'al',
        'zn',
        'ru',
    ],
}


class QWTradingTime(object):
    _open: time
    _close: time

    def __init__(self, t_open: time, t_close: time):
        self._open = t_open
        self._close = t_close

    @property
    def open(self) -> time:
        return self._open

    @property
    def close(self) -> time:
        return self._close
