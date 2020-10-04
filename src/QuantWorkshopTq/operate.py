# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'

"""
本模块负责记录操作，核算收益。
"""

from typing import Dict, List, Tuple, Optional
from datetime import date, time, datetime, timedelta
import platform
import os
import re
from pathlib import Path
import os.path
import json


data_trade = [
    'TradeDate',
    'TradeTime',
    'Product',
    'Contract',
    'Direction',
    'OC',
    'Price',
    'Lots',
    'Fee',
    'OrderNo',
    'Account',
]


data_order = [
    'OrderDate',
    'OrderTime',
    'Product',
    'Contract',
    'Direction',
    'OC',
    'Price',
    'Lots',
    'OrderNo',
    'Status',
    'Account',
]


def get_dropbox_path() -> str:
    """
    <https://help.dropbox.com/zh-cn/installs-integrations/desktop/locate-dropbox-folder>
    :return:
    """
    if platform.system() == 'Windows':
        try:
            json_path = (Path(os.getenv('LOCALAPPDATA')) / 'Dropbox' / 'info.json').resolve()
        except FileNotFoundError:
            json_path = (Path(os.getenv('APPDATA')) / 'Dropbox' / 'info.json').resolve()
        with open(str(json_path)) as f:
            j = json.load(f)

        return Path(j['personal']['path'])
    else:
        with open('~/.dropbox/info.json') as f:
            j = json.load(f)
        return Path(j['personal']['path'])


def str_to_date(source: str) -> date:
    return date(int(source[0:4]), int(source[4:6]), int(source[6:]))


def str_to_time(source: str) -> time:
    return time(int(source[0:2]), int(source[3:5]), int(source[6:]))


def str_to_product_and_contract(source: str) -> Tuple[str, str]:
    pattern: re.Pattern = re.compile(r'^([a-zA-Z]+)(\d+)$')
    result = pattern.match(source)
    return result.group(1), result.group(2)


def read_order(f_order: str) -> list:
    content: List[dict] = []
    source: List[str]
    line: str
    temp: List[str]
    p: str
    c: str

    with open(f_order, 'r') as txt_file:
        source = txt_file.readlines()

    del (source[0])

    for i in range(len(source)):
        temp = source[i].split()
        p, c = str_to_product_and_contract(temp[2])
        order_item = {
            data_order[0]: str_to_date(temp[0]),
            data_order[1]: str_to_time(temp[1]),
            data_order[2]: p,
            data_order[3]: c,
            data_order[4]: temp[4],
            data_order[5]: temp[5],
            data_order[6]: float(temp[6]),
            data_order[7]: int(temp[7]),
            data_order[8]: temp[11],
            data_order[9]: temp[3],
            data_order[10]: temp[-1],
        }
        content.append(order_item)
    return content
# '交易日', '委托时间', '合约号', '状态', '买卖', '开平', '委托价', '委托量', '成交量', '撤单量', '投保', '合同号', '主场号', '账号'


def read_trade(f_trade: str) -> list:
    content: List[dict] = []
    source: List[str]
    line: str
    temp: List[str]
    p: str
    c: str

    with open(f_trade, 'r') as txt_file:
        source = txt_file.readlines()

    del(source[0])
    del(source[-1])

    for i in range(len(source)):
        temp1 = source[i].split()
        temp2 = source[i][107:].split()
        p, c = str_to_product_and_contract(temp1[2])
        trade_item = {
            data_trade[0]: str_to_date(temp1[0]),    # 交易日
            data_trade[1]: str_to_time(temp1[1]),    # 交易时间
            data_trade[2]: p,                       # 品种
            data_trade[3]: c,                       # 合约
            data_trade[4]: temp1[3],                 # 方向，买卖
            data_trade[5]: temp1[4],                 # 开/平
            data_trade[6]: float(temp1[5]),          # 成交价
            data_trade[7]: int(temp1[6]),            # 成交量
            data_trade[8]: float(temp2[0]),          # 手续费
            data_trade[9]: temp2[1],                 # 合同号
            data_trade[10]: temp2[-1]                # 账号
        }
        content.append(trade_item)
    return content


if __name__ == '__main__':
    pass
