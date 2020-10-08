# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'


from typing import List, Tuple
import os
import os.path
from contextlib import closing

import pandas as pd
from tqsdk import TqApi
from tqsdk.tools import DataDownloader

from ..define import QWPeriodType
from . import get_application_path, get_tq_auth


quote_column_list: List[str] = ['open', 'high', 'low', 'close', 'volume', 'open_oi', 'close_oi']
tick_column_list: List[str] = ['last_price', 'highest', 'lowest',
                               'bid_price1', 'bid_volume1', 'ask_price1', 'ask_volume1',
                               'volume', 'amount', 'open_interest']

git@github.com:BruceFrankWong/QuantWorkshop.git
def get_period_from_file_name(file_name: str) -> Tuple[QWPeriodType, int]:
    filename: str = os.path.basename()


def handle_csv_column(csv_file: str):
    df: pd.DataFrame = pd.read_csv(csv_file)
    if period(request['period']) == 'tick':
        column_list = tick_column_list
    else:
        column_list = quote_column_list
    for column in column_list:
        column_x = ''.join([request['symbol'], '.', column])
        if column_x in df.columns:
            df.rename(columns={column_x: column}, inplace=True)
    df.to_csv(csv_file, index=False)


def download(symbol: str, period: ):
    # Application path
    application_path: str = get_application_path()

    # 天勤API
    tq_api: TqApi = TqApi(auth=get_tq_auth())
    #
    #
    #
    # # 下载需求
    # download_request_list: List[dict] = []
    # csv_path: str = os.path.join(application_path, 'download.csv')
    # with open(csv_path, newline='', encoding='utf-8') as csv_file:
    #     reader = csv.DictReader(csv_file)
    #     for row in reader:
    #         download_request: dict = {
    #             'symbol': row['symbol'],
    #             'start': date(int(row['start'][:4]), int(row['start'][4:6]), int(row['start'][6:8])),
    #             'end': date(int(row['end'][:4]), int(row['end'][4:6]), int(row['end'][6:8])),
    #             'period': int(row['period']),
    #         }
    #         download_request_list.append(download_request)
    #
    # # 运行下载
    # task_name: str
    # task: DataDownloader
    # filename: str
    # today: date = date.today()
    # df: pd.DataFrame
    # quote_column_list: List[str] = ['open', 'high', 'low', 'close', 'volume', 'open_oi', 'close_oi']
    # tick_column_list: List[str] = ['last_price', 'highest', 'lowest',
    #                                'bid_price1', 'bid_volume1', 'ask_price1', 'ask_volume1',
    #                                'volume', 'amount', 'open_interest']
    # column_list: List[str]
    with closing(tq_api):
        for request in download_request_list:
            task_name = request['symbol']
            file_name = os.path.join(application_path,
                                     'data_downloaded',
                                     f'{request["symbol"]}_{period(request["period"])}.csv')
            task = DataDownloader(
                tq_api,
                symbol_list=request['symbol'],
                dur_sec=request['period'],
                start_dt=request['start'],
                end_dt=request['end'] if today > request['end'] else today - timedelta(days=1),
                csv_file_name=file_name
            )

            while not task.is_finished():
                tq_api.wait_update()
                print(f'正在下载 [{task_name}] 的 {period(request["period"])} 数据，已完成： {task.get_progress():,.3f}%。')
    #
    #         # 处理下载好的 csv 文件的 header, 也就是 pandas.DataFrame 的 column.
    #         if task.is_finished():
    #             df = pd.read_csv(file_name)
    #             if period(request['period']) == 'tick':
    #                 column_list = tick_column_list
    #             else:
    #                 column_list = quote_column_list
    #             for column in column_list:
    #                 column_x = ''.join([request['symbol'], '.', column])
    #                 if column_x in df.columns:
    #                     df.rename(columns={column_x: column}, inplace=True)
    #             df.to_csv(file_name, index=False)
