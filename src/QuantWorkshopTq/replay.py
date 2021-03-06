#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'


"""
本模块负责复盘。
"""

import os
from datetime import date

from dotenv import find_dotenv, load_dotenv
from tqsdk import TqApi, TqReplay, TqSim

from QuantWorkshopTq.strategy import StrategyBase, StrategyParameter
from QuantWorkshopTq.strategy.scalping import Scalping, strategy_parameter


if __name__ == '__main__':
    # 自定义变量
    backtest_capital: float = 100000.0
    replay_date: date = date(2020, 9, 24)

    # 加载 .env 变量
    load_dotenv(find_dotenv())

    # 天勤账号
    TQ_ACCOUNT: str = os.environ.get('TQ_ACCOUNT')
    TQ_PASSWORD: str = os.environ.get('TQ_PASSWORD')

    # 天勤API
    tq_api: TqApi = TqApi(TqSim(backtest_capital),
                          backtest=TqReplay(replay_date),
                          web_gui='http://127.0.0.1:8888',
                          auth='%s,%s' % (TQ_ACCOUNT, TQ_PASSWORD))

    # 策略参数
    parameter: StrategyParameter = strategy_parameter
    parameter.set_parameters(
        {
            'max_position': 30,     # 最大持仓手数
            'close_spread': 1,      # 平仓价差
            'order_range': 3,       # 挂单范围
            'closeout_long': 5,     # 多单强平点差
            'closeout_short': 5,    # 空单强平点差
            'volume_per_order': 2,  # 每笔委托手数
            'volume_per_price': 3   # 每价位手数
        }
    )

    # 回测策略
    replay_strategy: StrategyBase = Scalping(api=tq_api, settings=parameter)

    # 运行回测
    replay_strategy.run()
