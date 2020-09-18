# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'


from typing import Dict, List, Tuple, NewType
from datetime import datetime, date

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
    _unfilled_order_list: List[str]     # 未成交委托单，包括开仓单和平仓单
    _position_order_list: List[str]     # 未平仓委托单（所以持仓）
    _finished_order_list: List[str]     # 完结委托单
    _canceled_order_list: List[str]     # 已撤销委托单
    _paired_order_dict: Dict[str, str]  # 配对委托单
    _unfilled_order_price_dict: Dict[float, List[str]]      # 未成交委托单的价格索引

    def __init__(self) -> None:
        self._order_dict = {}
        self._finished_order_list = []
        self._position_order_list = []
        self._unfilled_order_list = []
        self._canceled_order_list = []
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
        if len(order.exchange_order_id) > 0:
            return date.today().isoformat() + '_' + order.exchange_id + '_' + order.exchange_order_id
        else:
            return date.today().isoformat() + '_' + order.exchange_id + '_' + order.order_id

    def add(self, order: Order) -> None:
        """增加一张委托单
        该委托单可能是开仓单或者平仓单。
        """
        unique_id: str = self._make_unique_id(order)

        # 在 order_dict 中增加记录
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
        """
        unique_id: str = self._make_unique_id(order)

        # 在 unfilled_order_list 中去除记录
        try:
            self._unfilled_order_list.remove(unique_id)
        except ValueError:
            print(f'unique_id: {unique_id}')
            print('unique_id in self._unfilled_order_list:')
            for item in self._unfilled_order_list:
                print(item)

        # 在 order_price_dict 中去除记录
        if len(self._unfilled_order_price_dict[order.limit_price]) > 1:
            self._unfilled_order_price_dict[order.limit_price].remove(unique_id)
        else:
            del self._unfilled_order_price_dict[order.limit_price]

        # 如果 order 是平仓单，在 finished_order_list 中增加记录；否则在 position_order_list 中增加记录。
        if order.offset == 'CLOSE' or order.offset == 'CLOSETODAY':
            self._finished_order_list.append(unique_id)
        else:
            self._position_order_list.append(unique_id)

    def cancel(self, order: Order) -> None:
        """撤销一张委托单
        该委托单可能是开仓单或者平仓单。
        """
        unique_id: str = self._make_unique_id(order)

        # 在 unfilled_order_list 中去除记录
        self._unfilled_order_list.remove(unique_id)

        # 在 order_price_dict 中去除记录
        if len(self._unfilled_order_price_dict[order.limit_price]) > 1:
            self._unfilled_order_price_dict[order.limit_price].remove(unique_id)
        else:
            del self._unfilled_order_price_dict[order.limit_price]

        # 在 canceled_order_list 中增加记录
        self._canceled_order_list.append(unique_id)

    @property
    def unfilled_order_list(self) -> List[Order]:
        """
        未成交委托单列表。
        :return:
        """
        result: List[Order] = []
        unique_id: str
        for unique_id in self._unfilled_order_list:
            result.append(self._order_dict[unique_id])
        return result

    @property
    def unfilled_lots(self) -> int:
        """
        未成交手数。
        :return:
        """
        lots: int = 0
        order: Order
        for order in self.unfilled_order_list:
            lots += order.volume_orign
        return lots

    @property
    def unfilled_lots_for_buy(self) -> int:
        lots: int = 0
        order: Order
        for order in self.unfilled_order_list:
            if order.direction == 'BUY':
                lots += order.volume_orign
        return lots

    @property
    def unfilled_lots_for_sell(self) -> int:
        lots: int = 0
        order: Order
        for order in self.unfilled_order_list:
            if order.direction == 'SELL':
                lots += order.volume_orign
        return lots

    @property
    def unfilled_lots_for_open(self) -> int:
        """
        未成交开仓手数。
        :return:
        """
        lots: int = 0
        order: Order
        for order in self.unfilled_order_list:
            if order.offset == 'OPEN':
                lots += order.volume_orign
        return lots

    @property
    def unfilled_lots_for_close(self) -> int:
        """
        未成交平仓手数。
        :return:
        """
        lots: int = 0
        order: Order
        for order in self.unfilled_order_list:
            if order.offset == 'CLOSE' or order.offset == 'CLOSETODAY':
                lots += order.volume_orign
        return lots

    @property
    def highest_price(self) -> float:
        """最高价
        """
        return max(self._unfilled_order_price_dict.keys())

    @property
    def lowest_price(self) -> float:
        """最低价
        """
        return min(self._unfilled_order_price_dict.keys())

    @property
    def lowest_bid_price(self) -> float:
        """最低买价
        """
        unique_id: str
        price_list: list = list(self._unfilled_order_price_dict.keys())
        price_list.sort(reverse=False)
        for price in price_list:
            for unique_id in self._unfilled_order_price_dict[price]:
                if self._order_dict[unique_id].direction == 'BUY':
                    return price

    @property
    def highest_ask_price(self) -> float:
        """最高卖价
        """
        unique_id: str
        price_list: list = list(self._unfilled_order_price_dict.keys())
        price_list.sort(reverse=True)
        for price in price_list:
            for unique_id in self._unfilled_order_price_dict[price]:
                if self._order_dict[unique_id].direction == 'SELL':
                    return price

    @property
    def lowest_bid_order(self) -> List[str]:
        """最低买开委托单
        """
        result: List[str] = []
        unique_id: str
        price_list: list = list(self._unfilled_order_price_dict.keys())
        price_list.sort(reverse=False)
        for price in price_list:
            for unique_id in self._unfilled_order_price_dict[price]:
                if self._order_dict[unique_id].direction == 'BUY':
                    result.append(unique_id)
            if len(result) > 0:
                break
        return result

    @property
    def highest_ask_order(self) -> List[str]:
        """
        最高价卖单（包括卖开、卖平）。
        :return:
        """
        result: List[str] = []
        unique_id: str
        price_list: list = list(self._unfilled_order_price_dict.keys())
        price_list.sort(reverse=True)
        for price in price_list:
            for unique_id in self._unfilled_order_price_dict[price]:
                if self._order_dict[unique_id].direction == 'SELL':
                    result.append(unique_id)
            if len(result) > 0:
                break
        return result

    def unfilled_lots_at_price(self, p: float) -> int:
        if p not in self._unfilled_order_price_dict.keys():
            return 0
        lots: int = 0
        unique_id: str
        for unique_id in self._unfilled_order_price_dict[p]:
            lots += self._order_dict[unique_id].volume_orign
        return lots

    def save(self) -> None:
        pass

    def load(self) -> None:
        pass
