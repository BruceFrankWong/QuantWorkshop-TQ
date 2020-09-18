# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'


from typing import Dict, List

from QuantWorkshopTq.define import QWExchange


MAIN_CONTRACT: list = [
    {'yyyy_mm': '2016-01', 'symbol': '1605'},      # 换月日期：2015-09-18
    {'yyyy_mm': '2016-02', 'symbol': '1605'},
    {'yyyy_mm': '2016-03', 'symbol': '1609'},      # 换月日期：2016-02-22
    {'yyyy_mm': '2016-04', 'symbol': '1701'},      # 换月日期：2016-03-30
    {'yyyy_mm': '2016-05', 'symbol': '1701'},
    {'yyyy_mm': '2016-06', 'symbol': '1701'},
    {'yyyy_mm': '2016-07', 'symbol': '1701'},
    {'yyyy_mm': '2016-08', 'symbol': '1701'},
    {'yyyy_mm': '2016-09', 'symbol': '1701'},
    {'yyyy_mm': '2016-10', 'symbol': '1701'},
    {'yyyy_mm': '2016-11', 'symbol': '1701'},
    {'yyyy_mm': '2016-12', 'symbol': '1705'},      # 换月日期：2016-11-22
    {'yyyy_mm': '2017-01', 'symbol': '1705'},
    {'yyyy_mm': '2017-02', 'symbol': '1705'},
    {'yyyy_mm': '2017-03', 'symbol': '1709'},      # 换月日期：2017-03-14
    {'yyyy_mm': '2017-04', 'symbol': '1709'},
    {'yyyy_mm': '2017-05', 'symbol': '1709'},
    {'yyyy_mm': '2017-06', 'symbol': '1709'},
    {'yyyy_mm': '2017-07', 'symbol': '1709'},
    {'yyyy_mm': '2017-08', 'symbol': '1801'},      # 换月日期：2017-08-03
    {'yyyy_mm': '2017-09', 'symbol': '1801'},
    {'yyyy_mm': '2017-10', 'symbol': '1801'},
    {'yyyy_mm': '2017-11', 'symbol': '1801'},
    {'yyyy_mm': '2017-12', 'symbol': '1805'},      # 换月日期：2017-12-07
    {'yyyy_mm': '2018-01', 'symbol': '1805'},
    {'yyyy_mm': '2018-02', 'symbol': '1805'},
    {'yyyy_mm': '2018-03', 'symbol': '1805'},
    {'yyyy_mm': '2018-04', 'symbol': '1809'},      # 换月日期：2018-03-30
    {'yyyy_mm': '2018-05', 'symbol': '1809'},
    {'yyyy_mm': '2018-06', 'symbol': '1809'},
    {'yyyy_mm': '2018-07', 'symbol': '1901'},      # 换月日期：2018-07-11
    {'yyyy_mm': '2018-08', 'symbol': '1901'},
    {'yyyy_mm': '2018-09', 'symbol': '1901'},
    {'yyyy_mm': '2018-10', 'symbol': '1901'},
    {'yyyy_mm': '2018-11', 'symbol': '1901'},
    {'yyyy_mm': '2018-12', 'symbol': '1905'},      # 换月日期：2018-11-20
    {'yyyy_mm': '2019-01', 'symbol': '1905'},
    {'yyyy_mm': '2019-02', 'symbol': '1905'},
    {'yyyy_mm': '2019-03', 'symbol': '1905'},
    {'yyyy_mm': '2019-04', 'symbol': '1909'},      # 换月日期：2019-03-27
    {'yyyy_mm': '2019-05', 'symbol': '1909'},
    {'yyyy_mm': '2019-06', 'symbol': '1909'},
    {'yyyy_mm': '2019-07', 'symbol': '1909'},
    {'yyyy_mm': '2019-08', 'symbol': '2001'},      # 换月日期：2019-08-06
    {'yyyy_mm': '2019-09', 'symbol': '2001'},
    {'yyyy_mm': '2019-10', 'symbol': '2001'},
    {'yyyy_mm': '2019-11', 'symbol': '2001'},
    {'yyyy_mm': '2019-12', 'symbol': '2005'},      # 换月日期：2019-12-03
    {'yyyy_mm': '2020-01', 'symbol': '2005'},
    {'yyyy_mm': '2020-02', 'symbol': '2005'},
    {'yyyy_mm': '2020-03', 'symbol': '2009'},      # 换月日期：2020-03-11
    {'yyyy_mm': '2020-04', 'symbol': '2009'},
    {'yyyy_mm': '2020-05', 'symbol': '2009'},
    {'yyyy_mm': '2020-06', 'symbol': '2009'},
    {'yyyy_mm': '2020-07', 'symbol': '2009'},
    {'yyyy_mm': '2020-08', 'symbol': '2101'},      # 换月日期：2020-08-07
    {'yyyy_mm': '2020-09', 'symbol': '2101'},
]


def get_main_contract(exchange: QWExchange) -> list:
    pass


def get_exchange_futures(exchange: QWExchange) -> list:
    pass


def get_exchange_options(exchange: QWExchange) -> list:
    pass


product_list: dict = {
    'options':
        [
            '玉米',
            '豆粕',
            '铁矿石',
            '液化石油气',
            '聚乙烯',
            '聚氯乙烯',
            '聚丙烯',
            '棉花',
            '白糖',
            '菜粕',
            'PTA',
            '甲醇',
            '动力煤',
        ],

    'futures':
        [
            '玉米',
        ],
}


product_details: dict = {
    '玉米': 'c',
}


futures_SHFE: List[str] = [
    '黄金',
    '白银',
    '铜',
    '铝',
    '锌',
    '铅',
    '镍',
    '锡',
    '螺纹钢',
    '线材',
    '热轧卷板',
    '不锈钢',
]


futures_INE: List[str] = [
    '原油',
    '低硫燃料油',
    '20号胶',
]

futures_DCE: List[str] = [
    '',
]

futures_CZCE: List[str] = [
    '',
]

futures_CFFEX: List[str] = [
    '',
]

# 各交易所的期货产品
futures_exchange: Dict[QWExchange, List[str]] = {
    QWExchange.SHFE: futures_SHFE,
    QWExchange.INE: futures_INE,
    QWExchange.DCE: futures_CZCE,
    QWExchange.CZCE: futures_CZCE,
    QWExchange.CFFEX: futures_CFFEX,
}
