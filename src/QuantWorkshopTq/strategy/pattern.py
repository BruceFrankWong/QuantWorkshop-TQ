# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'

from typing import Dict, List, Union, Optional
from enum import Enum
import os
import time
import datetime

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import mplfinance as mpf
from tqsdk import TqApi, BacktestFinished
from tqsdk.tafunc import time_to_datetime, time_to_s_timestamp

from . import StrategyBase


KeyPoint = Dict[datetime.datetime, float]


class Trend(Enum):
    Up = 'UP'
    Down = 'DOWN'


class CandlestickPattern(StrategyBase):
    """
    熊颖华的策略。
    1、三角形
    2、突破回踩
    """
    _strategy_name: str = 'Pattern'

    candlestick: pd.DataFrame
    data: pd.DataFrame
    h1: KeyPoint
    h2: KeyPoint
    h3: KeyPoint
    l1: KeyPoint
    l2: KeyPoint
    l3: KeyPoint
    period: int
    keypoint: dict

    def __init__(self, api: TqApi, symbol: str):
        super().__init__(api=api, symbol=symbol)
        self.period = 30
        self.trend_turing_point = {}
        self.candlestick = self._api.get_kline_serial(self._symbol, duration_seconds=60, data_length=600)

    def draw(self):
        intraday: pd.DataFrame

        intraday = self.candlestick.loc[:, ['open', 'high', 'low', 'close', 'volume']]
        intraday.index = pd.to_datetime(self.candlestick['datetime'])

        color = mpf.make_marketcolors(up='red', down='cyan', inherit=True)
        style = mpf.make_mpf_style(marketcolors=color)

        # # 设置外观效果
        # plt.rc('font', family='Microsoft YaHei')  # 用中文字体，防止中文显示不出来
        # plt.rc('figure', fc='k')  # 绘图对象背景图
        # plt.rc('text', c='#800000')  # 文本颜色
        # plt.rc('axes', axisbelow=True, xmargin=0, fc='k', ec='#800000', lw=1.5, labelcolor='#800000',
        #        unicode_minus=False)  # 坐标轴属性(置底，左边无空隙，背景色，边框色，线宽，文本颜色，中文负号修正)
        # plt.rc('xtick', c='#d43221')  # x轴刻度文字颜色
        # plt.rc('ytick', c='#d43221')  # y轴刻度文字颜色
        # plt.rc('grid', c='#800000', alpha=0.9, ls=':', lw=0.8)  # 网格属性(颜色，透明值，线条样式，线宽)
        # plt.rc('lines', lw=0.8)  # 全局线宽
        #
        # # 创建绘图对象和4个坐标轴
        # figure = plt.figure(figsize=(16, 8))
        # left, width = 0.01, 0.98
        # ax1 = figure.add_axes([left, 0.6, width, 0.35])  # left, bottom, width, height
        # ax2 = figure.add_axes([left, 0.45, width, 0.15], sharex=ax1)  # 共享ax1轴
        # ax3 = figure.add_axes([left, 0.25, width, 0.2], sharex=ax1)  # 共享ax1轴
        # ax4 = figure.add_axes([left, 0.05, width, 0.2], sharex=ax1)  # 共享ax1轴
        # plt.setp(ax1.get_xticklabels(), visible=False)  # 使x轴刻度文本不可见，因为共享，不需要显示
        # plt.setp(ax2.get_xticklabels(), visible=False)  # 使x轴刻度文本不可见，因为共享，不需要显示
        # plt.setp(ax3.get_xticklabels(), visible=False)  # 使x轴刻度文本不可见，因为共享，不需要显示
        #
        # # 绘制蜡烛图
        # mpf.c(ax, data['open'], data['close'], data['high'], data['low'],
        #                       width=0.5, colorup='r', colordown='green',
        #                       alpha=0.6)

        mpf.plot(intraday, type='candle', style=style, mav=(5, 10), volume=True)
        mpf.show()

    def trend(self):
        trend: Trend
        ZIG_STATE_START = 0
        ZIG_STATE_RISE = 1
        ZIG_STATE_FALL = 2

        threshold: float = 0.055
        peer_i = 0
        candidate_i = None
        scan_i = 0
        peers = [0]
        k = self.candlestick['close']
        z = np.zeros(len(k))
        state = ZIG_STATE_START

        while True:
            # print(peers)
            scan_i += 1
            if scan_i == len(k) - 1:
                # 扫描到尾部
                if candidate_i is None:
                    peer_i = scan_i
                    peers.append(peer_i)
                else:
                    if state == ZIG_STATE_RISE:
                        if k[scan_i] >= k[candidate_i]:
                            peer_i = scan_i
                            peers.append(peer_i)
                        else:
                            peer_i = candidate_i
                            peers.append(peer_i)
                            peer_i = scan_i
                            peers.append(peer_i)
                    elif state == ZIG_STATE_FALL:
                        if k[scan_i] <= k[candidate_i]:
                            peer_i = scan_i
                            peers.append(peer_i)
                        else:
                            peer_i = candidate_i
                            peers.append(peer_i)
                            peer_i = scan_i
                            peers.append(peer_i)
                break

            if state == ZIG_STATE_START:
                if k[scan_i] >= k[peer_i] * (1 + threshold):
                    candidate_i = scan_i
                    state = ZIG_STATE_RISE
                elif k[scan_i] <= k[peer_i] * (1 - threshold):
                    candidate_i = scan_i
                    state = ZIG_STATE_FALL
            elif state == ZIG_STATE_RISE:
                if k[scan_i] >= k[candidate_i]:
                    candidate_i = scan_i
                elif k[scan_i] <= k[candidate_i] * (1 - threshold):
                    peer_i = candidate_i
                    peers.append(peer_i)
                    state = ZIG_STATE_FALL
                    candidate_i = scan_i
            elif state == ZIG_STATE_FALL:
                if k[scan_i] <= k[candidate_i]:
                    candidate_i = scan_i
                elif k[scan_i] >= k[candidate_i] * (1 + threshold):
                    peer_i = candidate_i
                    peers.append(peer_i)
                    state = ZIG_STATE_RISE
                    candidate_i = scan_i

    def triangle(self, data: pd.DataFrame):
        data.sort_values(by='high', ascending=False)
        self.keypoint['high'] = {
            1: {'value': data.iloc[0]['high'],
                'dt': time_to_datetime(data.iloc[0]['datetime'])
                },
            2: {'value': data.iloc[1]['high'],
                'dt': time_to_datetime(data.iloc[1]['datetime'])
                },
            3: {'value': data.iloc[3]['high'],
                'dt': time_to_datetime(data.iloc[3]['datetime'])
                },
        }

    def run(self):
        try:
            while True:
                if not self._api.wait_update(deadline=time.time() + self._timeout):
                    print('未在超时限制内接收到数据。')

                if self._api.is_changing(self.candlestick.iloc[-1], 'datetime'):
                    # candlestick columns
                    # 'datetime', 'id', 'open', 'high', 'low', 'close', 'volume', 'open_oi', 'close_oi',
                    #       'symbol', 'duration'
                    self._logger.info(time_to_datetime(self.candlestick.iloc[-1]['datetime']))
                    self.data = self.candlestick.loc[:, ['datetime', 'high', 'low']].iloc[-self.period:]
                    # self.triangle(self.data)

        except BacktestFinished:
            print(self.candlestick)
            print('='*20)
            # print(self.keypoint)
            print('=' * 20)
            self.draw()

            self._api.close()
            exit()
