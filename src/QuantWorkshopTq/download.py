#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'


"""
本模块负责下载数据。
"""


from typing import List
import csv
import os.path
from datetime import datetime, date, timedelta
from contextlib import closing

from dotenv import find_dotenv, load_dotenv
from tqsdk import TqApi, TqAuth
from tqsdk.tools import DataDownloader

from QuantWorkshopTq.utility import get_application_path
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
    download_request_list: List[dict] = []
    csv_path: str = os.path.join(get_application_path(), 'download.csv')
    with open(csv_path, newline='', encoding='utf-8') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            download_request: dict = {
                'symbol': row['symbol'],
                'start': date(int(row['start'][:4]), int(row['start'][4:6]), int(row['start'][6:8])),
                'end': date(int(row['end'][:4]), int(row['end'][4:6]), int(row['end'][6:8])),
                'period': int(row['period']),
            }
            download_request_list.append(download_request)

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
                start_dt=request['start'],
                end_dt=request['end'] if today > request['end'] else today - timedelta(days=1),
                csv_file_name=f'{request["symbol"]}_{period(request["period"])}.csv'
            )
            while not task.is_finished():
                tq_api.wait_update()
                print(f'正在下载 [{task_name}] 的 {period(request["period"])} 数据，已完成： {task.get_progress():,.3f}%。')
