# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'


from typing import List
import logging
import os.path
from datetime import datetime, date, time, timezone, timedelta

from pandas import DataFrame
from tqsdk import TqApi

from QuantWorkshopTq.define import tz_beijing, tz_settlement, TradingTime


class StrategyBase(object):
    _name: str = 'Unnamed Strategy'
    _symbol: str
    _capital: float
    _safety_rate: float

    _tz_beijing: timezone
    _tz_settlement: timezone
    _trading_time_list: List[TradingTime]

    _logger: logging.Logger

    _api: TqApi
    _ticks: DataFrame
    _klines: DataFrame

    _message_open_buy: str = '{datetime}, 买开, {volume}手, 价格：{price}, 委托单号：{order_id}'
    _message_open_sell: str = '{datetime}, 卖开, {volume}手, 价格：{price}, 委托单号：{order_id}'
    _message_close_buy: str = '{datetime}, 卖平, {volume}手, 价格：{price}, 委托单号：{order_id}'
    _message_close_sell: str = '{datetime}, 买平, {volume}手, 价格：{price}, 委托单号：{order_id}'
    _message_fill: str = '{datetime}, 成交, {volume}手, 价格：{price}, 委托单号：{order_id}'

    def __init__(self, api: TqApi, symbol: str, capital: float, safety_rate: float = 0.6):
        self._tz_settlement = tz_settlement
        self._api = api
        self._logger = self._get_logger()
        self._symbol = symbol
        self._capital = capital

        self._ticks = self._api.get_tick_serial(self._symbol)
        self._klines = self._api.get_kline_serial(self._symbol, 60)

    @property
    def name(self) -> str:
        return self._name

    def _get_logger(self) -> logging.Logger:
        logger = logging.getLogger(f'Strategy-{self._name}')

        logger.setLevel(logging.DEBUG)
        # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s: - %(message)s',
        #                               datefmt='%Y-%m-%d %H:%M:%S')
        formatter = logging.Formatter('%(asctime)s - %(name)s: %(message)s',
                                      datefmt='%Y-%m-%d %H:%M:%S')

        # 使用FileHandler输出到文件
        log_path: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'log')
        if not os.path.exists(log_path):
            os.mkdir(log_path)
        logger_file = logging.FileHandler(f'{log_path}/Strategy_{self._name}_.txt')
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

    def is_trading_time(self) -> bool:
        settlement: int = 17    # 北京时间17:00为期货结算日新的一天
        schedule_1 = ['if', 'ih', 'ic']     # 股指期货
        schedule_2 = ['c']

        open_time_1: time = time(hour=9, minute=15, second=0, tzinfo=tz_settlement)   # 股市开盘
        close_time_1: time = time(hour=15, minute=0, second=0)  # 股市收盘
        now: time = datetime.now(tz=self._tz_settlement).time()
        if self._symbol in schedule_1 and now:
            return True
        else:
            return False

    @property
    def trading_time(self) -> List[TradingTime]:
        return self._trading_time_list

    def is_valid_trading_time(self, t: time) -> bool:
        tt: TradingTime
        for tt in self._trading_time_list:
            if tt.open <= t <= tt.close:
                return True
        return False

    def load_status(self):
        pass

    def save_status(self):
        pass

    def run(self):
        pass
