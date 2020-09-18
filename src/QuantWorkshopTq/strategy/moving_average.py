# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'

from tqsdk import TqApi
from pandas import DataFrame

from .base import StrategyBase


class DoubleMovingAverage(StrategyBase):
    _tq_klines: DataFrame

    def __init__(self, api: TqApi, symbol: str, capital: float) -> None:
        super().__init__(api=api, symbol=symbol)

    def available_position(self) -> int:
        pass

    def try_open(self) -> None:
        # 判断开仓条件
        while True:
            self._api.wait_update()
            if self._api.is_changing(self._klines):
                ma = sum(self._klines.close.iloc[-15:]) / 15
                print('最新价', self._klines.close.iloc[-1], 'MA', ma)
                if self._klines.close.iloc[-1] > ma:
                    print('最新价大于MA: 市价开仓')
                    self._api.insert_order(symbol=self._symbol, direction='BUY', offset='OPEN', volume=5)
                    break

    def try_close(self) -> None:
        # 判断平仓条件
        while True:
            self._api.wait_update()
            if self._api.is_changing(self._klines):
                ma = sum(self._klines.close.iloc[-15:]) / 15
                print('最新价', self._klines.close.iloc[-1], 'MA', ma)
                if self._klines.close.iloc[-1] < ma:
                    print('最新价小于MA: 市价平仓')
                    self._api.insert_order(symbol=self._symbol, direction='SELL', offset='CLOSE', volume=5)
                    break

    def run(self):
        self._klines = self._api.get_kline_serial(self._symbol)
        while True:
            self.try_open()
            self.try_close()
        self._api.close()
