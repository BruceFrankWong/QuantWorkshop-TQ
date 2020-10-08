# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'

"""
本模块试图分析K线形态。
"""


from typing import Optional, Any, Dict, List, Tuple
import os.path

import pandas as pd
import numpy as np

from . import Trend, PriceType


def get_dataframe_index(df: pd.DataFrame, n: int):
    x: int
    if n < 0:
        x = 0
    elif n > len(pd.index):
        x = len(pd.index)
    else:
        x = n
    print(f'The {x}th data: ', df.iloc[x])
    print(df.index[x])


def trend_on_single_price(df: pd.DataFrame, price_type: PriceType, threshold: float, echo: bool = False) -> list:
    message = '第 {index} 个数据, ' \
              '{p_type}/前{p_type}: {price} / {prev_price}, ' \
              '趋势: {trend}, {status}.'
    status: str = '延续'

    trend: Trend
    index: int
    cursor: int = 0
    value: float    # 阈值比较

    key_point_list: list = []

    if df.iloc[1][price_type.value] >= df.iloc[0][price_type.value]:
        trend = Trend.Up
    else:
        trend = Trend.Down
    for index in range(1, len(df[price_type.value])):
        if trend == Trend.Up:
            if 0 < threshold < 1:
                value = df.iloc[index - 1][price_type.value] * (1 - threshold)
            else:
                value = df.iloc[index - 1][price_type.value] - threshold

            if df.iloc[index][price_type.value] >= df.iloc[index - 1][price_type.value]:
                cursor = index
                status = '延续'

            if df.iloc[index][price_type.value] <= value:
                key_point_list.append((df.index[cursor], df.iloc[cursor][price_type.value]))
                trend = Trend.Down
                cursor = index
                status = '转折'

        if trend == Trend.Down:
            if 0 < threshold < 1:
                value = df.iloc[index - 1][price_type.value] * (1 + threshold)
            else:
                value = df.iloc[index - 1][price_type.value] + threshold

            if df.iloc[index][price_type.value] <= df.iloc[index - 1][price_type.value]:
                cursor = index
                status = '延续'

            if df.iloc[index][price_type.value] >= value:
                key_point_list.append((df.index[cursor], df.iloc[cursor][price_type.value]))
                trend = Trend.Up
                cursor = index
                status = '转折'

        if echo:
            p_type: str
            if price_type == PriceType.Open:
                p_type = '开盘价'
            elif price_type == PriceType.High:
                p_type = '最高价'
            elif price_type == PriceType.Low:
                p_type = '最低价'
            elif price_type == PriceType.Close:
                p_type = '收盘价'
            else:
                p_type = '结算价'
            print(message.format(index=index,
                                 p_type=p_type,
                                 price=df.iloc[index][price_type.value],
                                 prev_price=df.iloc[index - 1][price_type.value],
                                 trend=trend.value,
                                 status=status
                                 )
                  )
        return key_point_list


def trend_on_hl(df: pd.DataFrame, echo: bool = False) -> tuple:
    """
    用最高价和最低价做趋势判断。

    返回一个列表，表中每个元素均为三个字段的元组。
    三个字段依次为：趋势开始的K线index, 趋势结束的K线index, 趋势。
    :return:  List[Tuple[int, int, Trend]]
    """

    message = '第 {index} 个数据, ' \
              '最高价/前最高价: {high} / {prev_high}, Delta = {dh}, ' \
              '最低价/前最低价: {low} / {prev_low}, Delta = {dl}, ' \
              '趋势: {trend}, {status}.'

    key_point_list: list = [(df.index[0], df.iloc[0]['low'])]
    high_list: list = []
    low_list: list = [(df.index[0], df.iloc[0]['low'])]
    cursor: float = df.iloc[0]['low']
    trend: Trend = Trend.Up

    index: int

    for index in range(1, len(df.index)):
        if trend == Trend.Up:
            if df.iloc[index]['high'] >= cursor:
                status = '延续'
                cursor = df.iloc[index]['high']
            else:
                status = '转折'
                key_point_list.append((df.index[index - 1], df.iloc[index - 1]['high']))
                if len(high_list) >= 2 and len(low_list) >= 2 and \
                        high_list[-1][1] <= df.iloc[index - 1]['high'] <= high_list[-2][1]:
                    del high_list[-1]
                    del low_list[-1]
                high_list.append((df.index[index - 1], df.iloc[index - 1]['high']))
                cursor = df.iloc[index]['low']
                trend = Trend.Down
        else:
            if df.iloc[index]['low'] <= cursor:
                status = '延续'
                cursor = df.iloc[index]['low']
            else:
                status = '转折'
                key_point_list.append((df.index[index - 1], df.iloc[index - 1]['low']))
                if len(high_list) >= 2 and len(low_list) >= 2 and \
                        low_list[-2][1] <= df.iloc[index - 1]['low'] <= low_list[-1][1]:
                    del high_list[-1]
                    del low_list[-1]
                low_list.append((df.index[index - 1], df.iloc[index - 1]['low']))
                cursor = df.iloc[index]['high']
                trend = Trend.Up

        if echo:
            print(message.format(index=index,
                                 high=df.iloc[index]['high'],
                                 prev_high=df.iloc[index - 1]['high'],
                                 dh=df.iloc[index]['high'] - df.iloc[index - 1]['high'],
                                 low=df.iloc[index]['low'],
                                 prev_low=df.iloc[index - 1]['low'],
                                 dl=df.iloc[index]['low'] - df.iloc[index - 1]['low'],
                                 trend=trend.value,
                                 status=status
                                 )
                  )

    hl_list: list = low_list + high_list
    hl_list.sort(key=lambda x: x[0])
    return key_point_list, hl_list
