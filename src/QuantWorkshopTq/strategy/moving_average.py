# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'

from tqsdk import TqApi, TargetPosTask
from tqsdk.tafunc import ma
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


def double_ma(tq_api: TqApi):
    """
    双均线策略
    注: 该示例策略仅用于功能示范, 实盘时请根据自己的策略/经验进行修改
    """
    SHORT = 30  # 短周期
    LONG = 60  # 长周期
    SYMBOL = "SHFE.bu2012"  # 合约代码

    print("策略开始运行")

    data_length = LONG + 2  # k线数据长度
    # "duration_seconds=60"为一分钟线, 日线的duration_seconds参数为: 24*60*60
    klines = tq_api.get_kline_serial(SYMBOL, duration_seconds=60, data_length=data_length)
    target_pos = TargetPosTask(tq_api, SYMBOL)

    while True:
        tq_api.wait_update()

        if tq_api.is_changing(klines.iloc[-1], "datetime"):  # 产生新k线:重新计算SMA
            short_avg = ma(klines["close"], SHORT)  # 短周期
            long_avg = ma(klines["close"], LONG)  # 长周期

            # 均线下穿，做空
            if long_avg.iloc[-2] < short_avg.iloc[-2] and long_avg.iloc[-1] > short_avg.iloc[-1]:
                target_pos.set_target_volume(-3)
                print("均线下穿，做空")

            # 均线上穿，做多
            if short_avg.iloc[-2] < long_avg.iloc[-2] and short_avg.iloc[-1] > long_avg.iloc[-1]:
                target_pos.set_target_volume(3)
                print("均线上穿，做多")
