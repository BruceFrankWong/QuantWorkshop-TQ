# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'


from typing import Any, Dict, List
import logging
import os.path
from datetime import datetime, date, time, timezone, timedelta

from tqsdk import TqApi

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
    _strategy_name: str = 'Unnamed Strategy'
    _api: TqApi
    _logger: logging.Logger

    _symbol: str
    _settings: dict
    _timeout: int = 5

    _tz_beijing: timezone
    _tz_settlement: timezone

    _message_trade: str = '{datetime}, 资金: {capital}, 挂单: {lots}手, {D}{O}, {volume}手, 价格：{price}, 委托单号：{order_id}'
    _message_open_buy: str = '{datetime}, 【下单】买开, 委托单号：{order_id}, {volume}手, 价格：{price}'
    _message_open_sell: str = '{datetime}, 【下单】卖开, 委托单号：{order_id}, {volume}手, 价格：{price}'
    _message_close_buy: str = '{datetime}, 【下单】卖平, 委托单号：{order_id}, {volume}手, 价格：{price}'
    _message_close_sell: str = '{datetime}, 【下单】买平, 委托单号：{order_id}, {volume}手, 价格：{price}'
    _message_fill: str = '{datetime}, 【成交】成交, 委托单号：{order_id}, {volume}手, 价格：{price}'

    def __init__(self, api: TqApi, symbol: str, settings: StrategyParameter):
        self._tz_settlement = tz_settlement
        self._api = api
        self._logger = self._get_logger()
        self._symbol = symbol

        self._settings = {}
        for k in settings.parameter_name:
            self._settings[k] = settings.get_parameter(k)

    @property
    def strategy_name(self) -> str:
        return self._strategy_name

    def _get_logger(self) -> logging.Logger:
        logger = logging.getLogger(f'Strategy-{self._strategy_name}')

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
        logger_file = logging.FileHandler(f'{log_path}/Strategy_{self._strategy_name}_{dt}.txt')
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

    def log_status(self, dt: datetime) -> None:
        cash: float = self._tq_account.available
        long: int = self._tq_position.pos_long
        short: int = self._tq_position.pos_short
        lots: int = sum(order.volume_left for order_id, order in self._tq_order.items() if order.status == "ALIVE")
        self._logger.info(f'【当前状态】时间: {dt}, 可用资金: {cash:,.2f}, 持多: {long}, 持空: {short}, 未成交: {lots}')

    def load_status(self):
        pass

    def save_status(self):
        pass

    def run(self):
        pass
