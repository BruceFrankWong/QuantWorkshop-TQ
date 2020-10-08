# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'


from typing import Optional, List
import os.path

import pandas as pd

from ..define import QWPeriodType
from . import get_application_path


def load_csv(csv_file: str) -> pd.pandas:
    # 可能会有异常抛出
    df_temp: pd.DataFrame = pd.read_csv(os.path.join(get_application_path(), 'data_downloaded', csv_file))
    prefix: str = csv_file.split('_')[0]
    column_list: List[str] = ['open', 'high', 'low', 'close', 'volume', 'open_oi', 'close_oi']
    for column in column_list:
        assert_column = ''.join([prefix, '.', column])
        if assert_column in df_temp.columns:
            df_temp.rename(columns={assert_column: column}, inplace=True)

    df = df_temp.loc[:, column_list]
    df.index = pd.to_datetime(df_temp['datetime'])
    return df


def load_symbol(symbol: str, period: QWPeriodType, n: Optional[int] = 1, mc: Optional[bool] = False) -> pd.pandas:
    csv_file: str
    if n < 0:
        raise ValueError('Parameter <n> should be 0 or positive integer.')
    elif period == QWPeriodType.Tick or n == 0:
        csv_file = f'{symbol}_tick.csv'
    elif n == 1:
        csv_file = f'{symbol}_{period.value}.csv'
    else:
        csv_file = f'{symbol}_{str(n)}{period.value}.csv'
    if mc:
        csv_file = f'KQ.m@{csv_file}'

    # 可能会有异常抛出
    df_temp: pd.DataFrame = pd.read_csv(os.path.join(get_application_path(), 'data_downloaded', csv_file))
    prefix: str = csv_file.split('_')[0]
    column_list: List[str] = ['open', 'high', 'low', 'close', 'volume', 'open_oi', 'close_oi']
    for column in column_list:
        assert_column = ''.join([prefix, '.', column])
        if assert_column in df_temp.columns:
            df_temp.rename(columns={assert_column: column}, inplace=True)

    df = df_temp.loc[:, column_list]
    df.index = pd.to_datetime(df_temp['datetime'])
    return df
