# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'

from typing import Dict, List, Union, Optional
import os
import time
import datetime

from pandas import DataFrame, Series

from tqsdk import TqApi
from tqsdk import BacktestFinished

from . import StrategyBase


KeyPoint = Dict[int, float]


class CandlestickPattern(StrategyBase):
    _strategy_name: str = 'Pattern'

    candlestick: DataFrame
    data: DataFrame
    h1: KeyPoint
    h2: KeyPoint
    h3: KeyPoint
    l1: KeyPoint
    l2: KeyPoint
    l3: KeyPoint
    period: int

    def __init__(self, api: TqApi, symbol: str):
        super().__init__(api=api, symbol=symbol)
        self.period = 60

    def prepare(self):
        self.candlestick = self._api.get_kline_serial(self._symbol, duration_seconds=60, data_length=600)

    def run(self):
        self.prepare()
        try:
            while True:
                if not self._api.wait_update(deadline=time.time() + self._timeout):
                    print('未在超时限制内接收到数据。')

                if self._api.is_changing(self.candlestick.iloc[-1], 'datetime'):
                    # candlestick columns
                    # 'datetime', 'id', 'open', 'high', 'low', 'close', 'volume', 'open_oi', 'close_oi',
                    #       'symbol', 'duration'
                    self.data = self.candlestick.loc[:, ['datetime', 'high', 'low']].iloc[-self.period:]

        except BacktestFinished:
            print(self.candlestick)
            print('='*20)
            print(self.data)
            self._api.close()
            exit()
