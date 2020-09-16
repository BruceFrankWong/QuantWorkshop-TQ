#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'


"""
本模块负责回测。
"""

import os
from datetime import date

from dotenv import find_dotenv, load_dotenv
from tqsdk import TqApi, TqBacktest, TqSim

from QuantWorkshopTq.strategy import StrategyBase, PopcornStrategy


if __name__ == '__main__':
    # 自定义变量
    backtest_capital: float = 100000.0
    backtest_start_date: date = date(2020, 8, 1)
    backtest_end_date: date = date(2020, 9, 15)

    # 加载 .env 变量
    load_dotenv(find_dotenv())

    # 天勤账号
    TQ_ACCOUNT: str = os.environ.get('TQ_ACCOUNT')
    TQ_PASSWORD: str = os.environ.get('TQ_PASSWORD')

    # 天勤API
    tq_api: TqApi = TqApi(TqSim(backtest_capital),
                          backtest=TqBacktest(start_dt=backtest_start_date,
                                              end_dt=backtest_end_date
                                              ),
                          web_gui='http://127.0.0.1:8888',
                          auth='%s,%s' % (TQ_ACCOUNT, TQ_PASSWORD))

    # 回测策略
    backtest_strategy: StrategyBase
    backtest_strategy = PopcornStrategy(api=tq_api,
                                        capital=backtest_capital,
                                        lots_per_order=3,
                                        lots_per_price=6,
                                        close_fluctuation=1,
                                        closeout=4,
                                        max_fluctuation=5,
                                        safety_rate=0.8
                                        )

    # 运行回测
    backtest_strategy.run()
