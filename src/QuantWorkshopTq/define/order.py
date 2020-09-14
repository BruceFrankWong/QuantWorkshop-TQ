# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'


from typing import Dict, List

from . import QWDirection, QWOffset, QWOrderStatus


class QWOrder(object):
    _order_id: str
    _direction: QWDirection
    _offset: QWOffset
    _price: float
    _lots: int
    _status: QWOrderStatus
    _close_order_id: str

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


class QWOrderManager(object):
    _order_list: List[QWOrder]
    _order_price_dict: Dict[float, list]

    def __init__(self) -> None:
        self._order_list = []
        self._order_price_dict = {}

    def add(self, order: QWOrder) -> None:
        self._order_list.append(order)

        if order.price in self._order_price_dict.keys():
            self._order_price_dict[order.price].append(order)
        else:
            self._order_price_dict[order.price] = [order]

    def remove(self, order: QWOrder) -> None:
        if len(self._order_price_dict[order.price]) > 1:
            self._order_price_dict[order.price].remove(order)
        else:
            del self._order_price_dict[order.price]

        self._order_list.remove(order)

    def remove_by_order_id(self, order_id: str) -> None:
        order: QWOrder
        for order in self._order_list:
            if order.order_id == order_id:
                self._order_list.remove(order)
                break

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
        return max(self._order_price_dict.keys())

    @property
    def lowest_price(self) -> float:
        return min(self._order_price_dict.keys())

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
        for order in self._order_price_dict[self.highest_bid_price]:
            if order.direction == QWDirection.Sell:
                order_list.append(order)
        return order_list

    @property
    def lowest_ask_order(self) -> List[QWOrder]:
        order: QWOrder
        order_list: list = []
        for order in self._order_price_dict[self.lowest_ask_price]:
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
