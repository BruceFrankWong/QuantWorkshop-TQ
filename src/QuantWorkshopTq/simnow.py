#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'


"""
本模块负责在 SimNow 进行模拟交易。
"""

import os
from datetime import date

from dotenv import find_dotenv, load_dotenv
from tqsdk import TqApi, TqAccount, TqKq

from QuantWorkshopTq.strategy import StrategyBase, PopcornStrategy


if __name__ == '__main__':
    # 自定义变量
    backtest_capital: float = 100000.0
    backtest_start_date: date = date(2020, 8, 1)
    backtest_end_date: date = date(2020, 9, 15)

    # 加载 .env 变量
    load_dotenv(find_dotenv())

    # 天勤账号
    TQ_SIM_ACCOUNT: str = os.environ.get('TQ_SIM_ACCOUNT')
    TQ_SIM_PASSWORD: str = os.environ.get('TQ_SIM_PASSWORD')

    # SimNow账号
    SIMNOW_ACCOUNT: str = os.environ.get('SIMNOW_ACCOUNT')
    SIMNOW_PASSWORD: str = os.environ.get('SIMNOW_PASSWORD')

    # 天勤API (SimNow)
    # tq_api_simnow: TqApi = TqApi(TqAccount('simnow', SIMNOW_ACCOUNT, SIMNOW_PASSWORD),
    #                              auth='%s,%s' % (TQ_SIM_ACCOUNT, TQ_SIM_PASSWORD))
    tq_api_kq: TqApi = TqApi(TqKq(), auth='%s,%s' % (TQ_SIM_ACCOUNT, TQ_SIM_PASSWORD))

    # 模拟交易策略
    sim_strategy: StrategyBase
    sim_strategy = PopcornStrategy(api=tq_api_kq,
                                   capital=backtest_capital,
                                   lots_per_order=3,
                                   lots_per_price=6,
                                   close_fluctuation=1,
                                   closeout=4,
                                   max_fluctuation=5,
                                   safety_rate=0.8
                                   )

    # 运行回测
    sim_strategy.run()
