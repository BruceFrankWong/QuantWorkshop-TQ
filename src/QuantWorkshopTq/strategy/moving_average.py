# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'

from typing import Any, Dict
import time

from tqsdk import TqApi, TargetPosTask, tafunc, BacktestFinished
from tqsdk.objs import Account, Position, Quote, Order
from pandas import DataFrame, Series


def double_moving_average(api: TqApi, symbol: str, max_position: int = 10, fast: int = 5, slow: int = 20):
    strategy_name: str = 'DoubleMovingAverage'

    api: TqApi = api
    symbol: str = symbol

    timeout: int = 5

    max_position: int = max_position
    fast: int = fast
    slow: int = slow

    ma: DataFrame = DataFrame()

    tq_account: Account = api.get_account()
    tq_position: Position = api.get_position(symbol)
    tq_candlestick: DataFrame = api.get_kline_serial(symbol=symbol, duration_seconds=24 * 60 * 60)
    tq_target_pos = TargetPosTask(api, symbol)

    deadline: float

    try:
        while True:
            deadline = time.time() + timeout
            if not api.wait_update(deadline=deadline):
                raise RuntimeError('没有在规定时间内获得数据！')
            # api.wait_update()

            if api.is_changing(tq_candlestick):
                ma['fast'] = tafunc.ma(tq_candlestick.close, fast)
                ma['slow'] = tafunc.ma(tq_candlestick.close, slow)

                tq_candlestick['ma_fast'] = ma['fast']
                tq_candlestick['ma_fast.color'] = 'green'
                tq_candlestick['ma_slow'] = ma['slow']
                tq_candlestick['ma_slow.color'] = 0xFF9933CC

                # 最新的快均线数值 > 最新的慢均线数值，且 前一根快均线数值 < 前一根慢均线数值
                # 即快均线从下向上穿过慢均线
                if (ma['fast'].iloc[-1] > ma['slow'].iloc[-1] and
                        ma['fast'].iloc[-2] < ma['slow'].iloc[-2]):
                    # # 如果有空仓，平空仓
                    # if tq_position.pos_short > 0:
                    #     api.insert_order(symbol=symbol,
                    #                           direction='BUY',
                    #                           offset='CLOSE',
                    #                           limit_price=tq_candlestick.close.iloc[-1],
                    #                           volume=tq_position.pos_short
                    #                           )
                    # # 开多仓
                    # api.insert_order(symbol=symbol,
                    #                       direction='BUY',
                    #                       offset='OPEN',
                    #                       limit_price=tq_candlestick.close.iloc[-1],
                    #                       volume=max_position
                    #                       )
                    tq_target_pos.set_target_volume(max_position)

                # 最新的快均线数值 < 最新的慢均线数值，且 前一根快均线数值 > 前一根慢均线数值
                # 即快均线从上向下穿过慢均线
                if (ma['fast'].iloc[-1] < ma['slow'].iloc[-1] and
                        ma['fast'].iloc[-2] > ma['slow'].iloc[-2]):
                    # # 如果有多仓，平多仓
                    # if tq_position.pos_short > 0:
                    #     api.insert_order(symbol=symbol,
                    #                           direction='SELL',
                    #                           offset='CLOSE',
                    #                           limit_price=tq_candlestick.close.iloc[-1],
                    #                           volume=tq_position.pos_short
                    #                           )
                    # # 开空仓
                    # api.insert_order(symbol=symbol,
                    #                       direction='SELL',
                    #                       offset='OPEN',
                    #                       limit_price=tq_candlestick.close.iloc[-1],
                    #                       volume=max_position
                    #                       )
                    tq_target_pos.set_target_volume(-max_position)
    except BacktestFinished:
        api.close()
        print(f'参数: fast={fast}, slow={slow}, 最终权益={tq_account["balance"]}')
