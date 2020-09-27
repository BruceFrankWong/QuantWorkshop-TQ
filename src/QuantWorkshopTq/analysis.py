#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'


"""
本模块负责数据分析。
"""


from typing import Optional, Generator, List, Set
import os.path
from datetime import datetime, date, time, timedelta

import pandas as pd

from QuantWorkshopTq.utility import get_application_path


TQ_DATA_BEGIN = date(2016, 1, 1)
holidays: dict = {
    2016: {
        '元旦': ['2016-01-01', '2016-01-03'],
        '春节': ['2016-02-07', '2016-02-13'],
        '清明': ['2016-04-02', '2016-04-03'],
        '劳动': ['2016-04-30', '2016-05-02'],
        '端午': ['2016-06-09', '2016-06-11'],
        '中秋': ['2016-09-15', '2016-09-17'],
        '国庆': ['2016-10-01', '2016-10-07'],
    },
    2017: {
        '元旦': ['2017-01-01', '2017-01-02'],
        '春节': ['2017-01-27', '2017-02-02'],
        '清明': ['2017-04-02', '2017-04-04'],
        '劳动': ['2017-04-29', '2017-05-01'],
        '端午': ['2017-05-28', '2017-05-30'],
        '中秋国庆': ['2017-10-01', '2017-10-08'],
    },
    2018: {
        '元旦': ['2018-01-01', '2018-01-01'],
        '春节': ['2018-02-15', '2018-02-21'],
        '清明': ['2018-04-05', '2018-04-07'],
        '劳动': ['2018-04-29', '2018-05-01'],
        '端午': ['2018-06-18', '2018-06-18'],
        '中秋': ['2018-09-24', '2018-09-24'],
        '国庆': ['2018-10-01', '2018-10-07'],
    },
    2019: {
        '元旦': ['2018-12-30', '2019-01-01'],
        '春节': ['2019-02-04', '2019-02-10'],
        '清明': ['2019-04-05', '2019-04-05'],
        '劳动': ['2019-05-01', '2019-05-01'],
        '端午': ['2019-06-07', '2019-06-07'],
        '中秋': ['2019-09-13', '2019-09-13'],
        '国庆': ['2019-10-01', '2019-10-07'],
    },
    2020: {
        '元旦': ['2020-01-01', '2020-01-01'],
        '春节': ['2020-01-24', '2020-01-30'],
        '清明': ['2020-04-04', '2020-04-06'],
        '劳动': ['2020-05-01', '2020-05-05'],
        '端午': ['2020-06-25', '2020-06-27'],
        '中秋国庆': ['2020-10-01', '2020-10-08'],
    },
}


def generate_holiday() -> Set[date]:
    result: Set[date] = set()

    for year in holidays:
        for item in holidays[year].values():
            if item[1] == item[0]:
                result.add(date.fromisoformat(item[0]))
            else:
                d1 = date.fromisoformat(item[0])
                d2 = date.fromisoformat(item[1])
                while d1 <= d2:
                    result.add(d1)
                    d1 += timedelta(days=1)
    return result


def generate_trading_date(until_day: date) -> Generator:
    day = TQ_DATA_BEGIN
    while day < min(date.today(), until_day):
        if 1 <= day.isoweekday() <= 5 and day not in generate_holiday():
            yield day
        day = day + timedelta(days=1)


def do_analysis(csv_path: str):
    source: pd.DataFrame = pd.read_csv(os.path.join(f'{get_application_path()}', csv_path))
    data: pd.DataFrame = source.copy()
    data['date'] = pd.to_datetime(source['datetime'])
    data.drop(columns=['datetime'], inplace=True)
    data = data[['date', 'open', 'high', 'low', 'close', 'volume', 'open_oi', 'close_oi']]
    data['range_max'] = data['high'] - data['low']
    data['range_up'] = data['high'] - data['open']
    data['range_down'] = data['low'] - data['open']
    print(data)
    # if data.columns[0] == 'datetime':
    #     data[date] = pd.


def do_analysis_on_daily():
    pass


def minute_to_section(symbol: str):
    columns: List[str] = ['date', 'section', 'open', 'high', 'low', 'close', 'volume', 'open_oi', 'close_oi']
    source: pd.DataFrame = pd.read_csv(os.path.join(f'{get_application_path()}', f'KQ.m@{symbol}_minute.csv'))
    result: pd.DataFrame = pd.DataFrame(columns=columns)
    print(source)
    source['dt'] = pd.to_datetime(source['datetime'])
    source.drop(columns=['datetime'], inplace=True)
    source.rename(columns={'dt': 'datetime'}, inplace=True)
    print(source['datetime'].dtypes)


def merge():
    pass


def merge_as_section():
    pass


def merge_as_15_minutes():
    pass


def handle_csv_header():
    pass


if __name__ == '__main__':
    # do_analysis('KQ.m@DCE.c_day.csv')
    # minute_to_section('DCE.c')
    # for holiday in generate_holiday():
    #     print(holiday)
    for x in generate_trading_date(date(2020, 9, 10)):
        print(x, x.isoweekday())
