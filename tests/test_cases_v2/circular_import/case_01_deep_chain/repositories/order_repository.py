from typing import Dict, Optional, List
from models import Order


class OrderRepository:
    def __init__(self):
        self._orders: Dict[str, Order] = {}

    def save(self, order: Order) -> None:
        self._orders[order.id] = order

    def find_by_id(self, order_id: str) -> Optional[Order]:
        return self._orders.get(order_id)

    def find_by_user_id(self, user_id: str) -> List[Order]:
        return [o for o in self._orders.values() if o.user_id == user_id]

    def find_all(self) -> List[Order]:
        return list(self._orders.values())
