# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'


from typing import Dict, List
from datetime import datetime

from tqsdk.objs import Order

from . import QWDirection, QWOffset, QWOrderStatus


class QWOrder(object):
    """委托单对象。
    """
    _order_id: str              # 委托单编号
    _datetime: datetime         # 委托单发出日期和时间
    _direction: QWDirection     # 买/卖
    _offset: QWOffset           # 开/平/平今
    _price: float               # 价格
    _lots: int                  # 手数
    _status: QWOrderStatus      # 状态
    _close_order_id: str        # 平仓委托单编号，如果状态不是取消。

    def __init__(self, order_id: str, price: float, lots: int, direction: QWDirection, offset: QWOffset):
        self._price = price
        self._lots = lots
        self._direction = direction
        self._offset = offset
        self._order_id = order_id
        self._close_order_id = ''

    @property
    def order_id(self) -> str:
        return self._order_id

    @property
    def price(self) -> float:
        return self._price

    @property
    def lots(self) -> int:
        return self._lots

    @property
    def value(self) -> float:
        return self._price * self._lots

    @property
    def direction(self) -> QWDirection:
        return self._direction

    @property
    def offset(self) -> QWOffset:
        return self._offset

    @property
    def status(self) -> QWOrderStatus:
        return self._status

    @status.setter
    def status(self, new_status: QWOrderStatus):
        self.status = new_status

    @property
    def close_order_id(self) -> str:
        return self._close_order_id

    def from_tq_order(self, tq_order: Order):
        self._order_id = tq_order.exchange_order_id
        self._datetime = datetime.fromtimestamp(tq_order.insert_date_time)
        self._price = tq_order.limit_price
        self._lots = tq_order.volume_orign


class QWOrderManager(object):
    """委托单管理器
    所谓盈亏，即已完成平仓的委托单，其开平点差。
    所谓持仓，即未完成平仓的委托单（仅开仓单，买卖不限）。
    所谓挂单，即为完成交易的委托单（开仓单平仓单都有）。

    对委托单进行分类：
        交易流程——开仓单、平仓单、完结单（已平仓的委托单）
        交易状态——未成交、部分成交、完全成交、已撤销
    """
    _order_dict: Dict[str, Order]
    _finished_order_list: List[str]             # 完结委托单
    _position_order_list: List[str]             # 开仓委托单，未平仓，所以持仓
    _unfilled_order_list: List[str]             # 未成交委托单，包括开仓单和平仓单
    _unfilled_order_price_dict: Dict[float, List[str]]      # 未成交委托单的价格索引

    def __init__(self) -> None:
        self._order_dict = {}
        self._finished_order_list = []
        self._position_order_list = []
        self._unfilled_order_list = []
        self._unfilled_order_price_dict = {}

    @staticmethod
    def _make_unique_id(order: Order) -> str:
        """生成唯一的委托单编号
        日期 + 交易所 + 交易所编号，即 YYYY-MM-DD_{e}_{order_id}
        其中 e 代表:
            S, 上期所
            D, 大商所
            Z, 郑商所
            C, 中金所
            E, 能源所
        """
        return datetime.today().isoformat() + '_' + order.exchange_id + '_' + order.exchange_order_id

    def add(self, order: Order) -> None:
        """增加一张委托单
        该委托单可能是开仓单或者平仓单。
        该委托单初始状态必然是未成交。
        """
        unique_id: str = self._make_unique_id(order)
        self._order_dict[unique_id] = order

        # 在 unfilled_order_list 中增加记录
        self._unfilled_order_list.append(unique_id)

        # 在 order_price_dict 中增加记录
        if order.limit_price in self._unfilled_order_price_dict.keys():
            self._unfilled_order_price_dict[order.limit_price].append(unique_id)
        else:
            self._unfilled_order_price_dict[order.limit_price] = [unique_id]

    def fill(self, order: Order) -> None:
        """成交一张委托单
        该委托单可能是开仓单或者平仓单。
        该委托单初始状态必然是已成交。
        """
        unique_id: str = self._make_unique_id(order)

        # 在 unfilled_order_list 中去除记录
        self._unfilled_order_list.remove(unique_id)

        # 在 order_price_dict 中去除记录
        if len(self._unfilled_order_price_dict[order.limit_price]) > 1:
            self._unfilled_order_price_dict[order.limit_price].remove(unique_id)
        else:
            del self._unfilled_order_price_dict[order.limit_price]

        # 如果 order 是平仓单
        if order.offset == 'CLOSE' or order.offset == 'CLOSETODAY':
            self._finished_order_list.append(unique_id)
        else:
            self._position_order_list.append(unique_id)

    def cancel(self, order: Order) -> None:
        """撤销一张委托单
        该委托单可能是开仓单或者平仓单。
        该委托单初始状态必然是已撤销。
        """
        unique_id: str = self._make_unique_id(order)

        # 在 unfilled_order_list 中去除记录
        self._unfilled_order_list.remove(unique_id)

        if len(self._unfilled_order_price_dict[order.price]) > 1:
            self._unfilled_order_price_dict[order.price].remove(order)
        else:
            del self._unfilled_order_price_dict[order.price]

        self._order_list.remove(order)

    @property
    def order_list(self) -> list:
        return self._order_list

    @property
    def total_lots(self) -> int:
        lots: int = 0
        for order in self._order_list:
            lots += order.lots
        return lots

    @property
    def total_lots_for_buy(self) -> int:
        lots: int = 0
        for order in self._order_list:
            if order.direction == 'BUY':
                lots += order.lots
        return lots

    @property
    def total_lots_for_sell(self) -> int:
        lots: int = 0
        for order in self._order_list:
            if order.direction == 'SELL':
                lots += order.lots
        return lots

    @property
    def highest_price(self) -> float:
        return max(self._unfilled_order_price_dict.keys())

    @property
    def lowest_price(self) -> float:
        return min(self._unfilled_order_price_dict.keys())

    @property
    def highest_bid_price(self) -> float:
        price: float = self._order_list[0].price
        order: QWOrder
        for order in self._order_list:
            if order.price > price and order.direction == 'SELL':
                price = order.price
        return price

    @property
    def lowest_ask_price(self) -> float:
        price: float = self._order_list[0].price
        order: QWOrder
        for order in self._order_list:
            if order.price < price and order.direction == 'BUY':
                price = order.price
        return price

    @property
    def highest_bid_order(self) -> List[QWOrder]:
        order: QWOrder
        order_list: list = []
        for order in self._unfilled_order_price_dict[self.highest_bid_price]:
            if order.direction == QWDirection.Sell:
                order_list.append(order)
        return order_list

    @property
    def lowest_ask_order(self) -> List[QWOrder]:
        order: QWOrder
        order_list: list = []
        for order in self._unfilled_order_price_dict[self.lowest_ask_price]:
            if order.direction == QWDirection.Buy:
                order_list.append(order)
        return order_list

    @property
    def unclosed_order(self) -> list:
        result: list = []
        for order in self._order_list:
            if order.close_order_id is '':
                result.append(order.order_id)
        return result

    def unfilled_lots_at_price(self, p: float) -> int:
        pass

    def save(self) -> None:
        pass

    def load(self) -> None:
        pass
