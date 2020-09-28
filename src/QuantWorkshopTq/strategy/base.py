# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'


from typing import Any, Optional, Dict, List
import logging
import os.path
from datetime import datetime, date, time, timezone, timedelta

from tqsdk import TqApi
from tqsdk.objs import Account, Position, Quote, Order
from tqsdk.entity import Entity
from tqsdk.tafunc import time_to_datetime
from pandas import DataFrame

from QuantWorkshopTq.define import tz_beijing, tz_settlement


class StrategyParameter(object):
    """
    策略参数。
    """
    _parameter_name: List[str]
    _parameters: dict

    def __init__(self, parameter_name: List[str]):
        self._parameter_name = parameter_name
        self._parameters = {}

    @property
    def parameter_name(self) -> List[str]:
        return self._parameter_name

    def get_parameter(self, name: str) -> Any:
        if name not in self._parameter_name:
            raise ValueError(f'Parameter name <{name}> is invalid.')
        return self._parameters[name]

    def set_parameter(self, name: str, value: Any):
        if name not in self._parameter_name:
            raise ValueError(f'Parameter name <{name}> is invalid.')
        self._parameters[name] = value

    def set_parameters(self, parameters: Dict[str, Any]):
        for item in parameters.keys():
            if item not in self._parameter_name:
                raise ValueError(f'Parameter name <{item}> is invalid.')
            self._parameters[item] = parameters[item]

    def show(self):
        for item in self._parameter_name:
            print(self._parameters[item])


class StrategyBase(object):
    strategy_name: str = 'Unnamed Strategy'
    api: TqApi
    logger: logging.Logger

    symbol: str
    settings: dict
    timeout: int = 5

    _tz_beijing: timezone
    _tz_settlement: timezone

    local_datetime: datetime     # 本机时间
    remote_datetime: datetime    # 远端时间

    price_ask: float = 0.0      # 卖一价
    price_bid: float = 0.0      # 买一价

    tq_account: Account
    tq_position: Position
    tq_tick: DataFrame
    tq_quote: Quote
    tq_order: Entity

    def __init__(self, api: TqApi, symbol: str, settings: Optional[StrategyParameter] = None):
        self._tz_settlement = tz_settlement
        self.api = api
        self.logger = self._get_logger()
        self.symbol = symbol

        self._settings = {}
        if settings:
            for k in settings.parameter_name:
                self._settings[k] = settings.get_parameter(k)

        # 天勤数据
        self.tq_account = self.api.get_account()
        self.tq_position = self.api.get_position(self.symbol)
        self.tq_tick = self.api.get_tick_serial(self.symbol)
        self.tq_quote = self.api.get_quote(self.symbol)
        self.tq_order = self.api.get_order()

    def _get_logger(self) -> logging.Logger:
        logger = logging.getLogger(f'Strategy-{self.strategy_name}')

        logger.setLevel(logging.DEBUG)
        # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s: - %(message)s',
        #                               datefmt='%Y-%m-%d %H:%M:%S')
        formatter = logging.Formatter('%(message)s')

        # 当前日期时间
        now: datetime = datetime.now()
        dt: str = now.strftime('%Y-%m-%d_%H-%M-%S')

        # 使用FileHandler输出到文件
        log_path: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'log')
        if not os.path.exists(log_path):
            os.mkdir(log_path)
        logger_file = logging.FileHandler(f'{log_path}/Strategy_{self.strategy_name}_{dt}.txt', encoding='utf-8')
        logger_file.setLevel(logging.DEBUG)
        logger_file.setFormatter(formatter)

        # 使用StreamHandler输出到屏幕
        logger_screen = logging.StreamHandler()
        logger_screen.setLevel(logging.DEBUG)
        logger_screen.setFormatter(formatter)

        # 添加两个Handler
        logger.addHandler(logger_screen)
        logger.addHandler(logger_file)

        return logger

    def log_status(self) -> None:
        cash: float = self.tq_account.available
        long: int = self.tq_position.pos_long
        short: int = self.tq_position.pos_short
        lots: int = sum(order.volume_left for _, order in self.tq_order.items() if order.status == 'ALIVE')
        self.logger.info(f'{self.remote_datetime}, 【状态】, 可用资金: {cash:,.2f}, '
                         f'持多: {long}, 持空: {short}, 未成交: {lots}, '
                         f'当前买一价: {self.price_bid}, 当前卖一价: {self.price_ask}')

    def log_order(self, order: Order) -> None:
        self.logger.info(f'{self.remote_datetime}, 【下单】, '
                         f'{"买" if order.direction == "BUY" else "卖"}'
                         f'{"开" if order.offset == "OPEN" else ("平" if order.offset == "CLOSE" else "平今")}, '
                         f'{order.volume_orign}手 @{order.limit_price}, '
                         f'委托时间: {time_to_datetime(order.insert_date_time)}, '
                         f'委托单号：{order.order_id}')

    def log_cancel(self, order: Order) -> None:
        self.logger.info(f'{self.remote_datetime}, 【撤单】, '
                         f'{"买" if order.direction == "BUY" else "卖"}'
                         f'{"开" if order.offset == "OPEN" else ("平" if order.offset == "CLOSE" else "平今")}, '
                         f'撤销{order.volume_left}手 @{order.limit_price}, '
                         f'委托时间: {time_to_datetime(order.insert_date_time)}, '
                         f'委托单号：{order.order_id}')

    def log_fill(self, order: Order, trade_id: str) -> None:
        self.logger.info(f'{self.remote_datetime}, 【成交】, '
                         f'{"买" if order.direction == "BUY" else "卖"}'
                         f'{"开" if order.offset == "OPEN" else ("平" if order.offset == "CLOSE" else "平今")}, '
                         f'成交{order.volume_orign-order.volume_left}手 @{order.limit_price}, '
                         f'委托时间: {time_to_datetime(order.insert_date_time)}, '
                         f'委托单号：{order.order_id}, '
                         f'成交编号: {trade_id}')

    def log_accept(self, order: Order) -> None:
        self.logger.info(f'{self.remote_datetime}, 【报单】, '
                         f'委托时间: {time_to_datetime(order.insert_date_time)}, '
                         f'委托单号：{order.order_id}')

    def log_no_data(self) -> None:
        self.logger.info(f'{self.remote_datetime}, 未在 timeout 时间内收到数据。')

    def is_open_condition(self) -> bool:
        pass

    def is_close_condition(self) -> bool:
        pass

    def load_status(self):
        pass

    def save_status(self):
        pass

    def run(self):
        pass
