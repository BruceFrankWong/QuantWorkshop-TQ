# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'


from typing import Dict, List
from datetime import datetime

from . import QWDirection, QWOffset, QWOrderStatus


class QWPosition(object):
    order_id: str
    fill_datetime: datetime
    price: float
    lots: int
    direction: QWDirection


class QWPositionManager(object):
    _position_list: List[QWPosition]

    def __init__(self) -> None:
        self._position_list = []

    def add(self, position: QWPosition) -> None:
        self._position_list.append(position)

    def remove(self, position: QWPosition) -> None:
        self._position_list.remove(position)

    def remove_by_order_id(self, order_id: str) -> None:
        position: QWPosition
        for position in self._position_list:
            if position.order_id == order_id:
                self._position_list.remove(position)
                break

    @property
    def total_lots(self) -> int:
        return self.total_lots_for_buy + self.total_lots_for_sell

    @property
    def total_lots_for_sell(self) -> int:
        lots: int = 0
        position: QWPosition
        for position in self._position_list:
            if position.direction == QWDirection.Sell:
                lots += position.lots
        return lots

    @property
    def total_lots_for_buy(self) -> int:
        lots: int = 0
        position: QWPosition
        for position in self._position_list:
            if position.direction == QWDirection.Buy:
                lots += position.lots
        return lots

    def lots_at_price(self, price: float) -> int:
        lots: int = 0
        position: QWPosition
        for position in self._position_list:
            if position.price == price:
                lots += position.lots
        return lots

    def position_at_price(self, price: float) -> List[QWPosition]:
        result: List[QWPosition] = []
        position: QWPosition
        for position in self._position_list:
            if position.price == price:
                result.append(position)
        return result

    def position_at_price_for_buy(self, price: float) -> List[QWPosition]:
        result: List[QWPosition] = []
        position: QWPosition
        for position in self._position_list:
            if position.price == price and position.direction == QWDirection.Long:
                result.append(position)
        return result

    def position_at_price_for_sell(self, price: float) -> List[QWPosition]:
        result: List[QWPosition] = []
        position: QWPosition
        for position in self._position_list:
            if position.price == price and position.direction == QWDirection.Short:
                result.append(position)
        return result
