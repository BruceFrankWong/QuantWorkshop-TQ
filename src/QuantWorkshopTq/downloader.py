#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'


"""
本模块负责下载数据。
"""

import os
from datetime import datetime, date, timedelta
from contextlib import closing

from dotenv import find_dotenv, load_dotenv
from tqsdk import TqApi, TqAuth
from tqsdk.tools import DataDownloader

from QuantWorkshopTq.strategy import StrategyBase, StrategyParameter
from QuantWorkshopTq.strategy.scalping import Scalping, strategy_parameter

tick: int = 0
second: int = 1
minute: int = 60
hour: int = 3660
day: int = 86400    # 一天 86400 秒（60*60*24）


def period(n: int) -> str:
    if n == 0:
        return 'tick'
    elif n == 86400 or n % 86400 == 0:
        return 'day' if n == 86400 else f'{n % 86400}day'
    elif n == 3600 or n % 3600 == 0:
        return 'hour' if n == 3600 else f'{n % 3600}hour'
    elif n == 60 or n % 60 == 0:
        return 'minute' if n == 60 else f'{n % 60}minute'
    else:
        return 'second' if n == 1 else f'{n}second'


if __name__ == '__main__':
    # 加载 .env 变量
    load_dotenv(find_dotenv())

    # 天勤账号
    TQ_ACCOUNT: str = os.environ.get('TQ_ACCOUNT')
    TQ_PASSWORD: str = os.environ.get('TQ_PASSWORD')

    # 天勤API
    tq_api: TqApi = TqApi(auth=TqAuth(TQ_ACCOUNT, TQ_PASSWORD))

    # 下载需求
    download_request_list: list = [
        {
            'symbol': 'KQ.m@SHFE.au',
            'listing': date(2016, 1, 1),
            'expiration': date(2021, 1, 15),
            'period': day
        },
        {
            'symbol': 'KQ.m@SHFE.au',
            'listing': date(2016, 1, 1),
            'expiration': date(2021, 1, 15),
            'period': minute
        },
    ]

    # # 下载任务
    # download_tasks: dict = {'AG2012': DataDownloader(tq_api,
    #                                                  symbol_list='SHFE.ag2012',
    #                                                  dur_sec=0,
    #                                                  start_dt=date(2019, 12, 17),
    #                                                  end_dt=date(2020, 9, 25),
    #                                                  csv_file_name='T1809_tick.csv')
    #                         }

    # 运行下载
    task_name: str
    task: DataDownloader
    today: date = date.today()
    with closing(tq_api):
        for request in download_request_list:
            task_name = request['symbol']
            task = DataDownloader(
                tq_api,
                symbol_list=request['symbol'],
                dur_sec=request['period'],
                start_dt=request['listing'],
                end_dt=request['expiration'] if today > request['expiration'] else today - timedelta(days=1),
                csv_file_name=f'{request["symbol"]}_{period(request["period"])}.csv'
            )
            while not task.is_finished():
                tq_api.wait_update()
                print(f'正在下载 [{task_name}] 的 {period(request["period"])} 数据，已完成： {task.get_progress():,.3f}%。')
