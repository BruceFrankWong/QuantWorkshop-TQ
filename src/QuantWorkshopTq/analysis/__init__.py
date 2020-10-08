# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'


from enum import Enum


class Trend(Enum):
    Up = 'UP'
    Down = 'DOWN'
    Sideways = 'Sideways'


class PriceType(Enum):
    Open = 'open'
    High = 'high'
    Low = 'low'
    Close = 'close'
    Settlement = 'settlement'


from .trend_line import (
    get_dataframe_index,
    trend_on_single_price,
    trend_on_hl
)
