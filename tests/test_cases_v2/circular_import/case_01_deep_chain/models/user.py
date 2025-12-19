from typing import List, Optional
from dataclasses import dataclass, field


@dataclass
class User:
    id: str
    name: str
    email: str
    orders: List['Order'] = field(default_factory=list)

    def add_order(self, order: 'Order') -> None:
        self.orders.append(order)

    def get_total_spent(self) -> float:
        return sum(o.total for o in self.orders)
