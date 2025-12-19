from typing import List, Optional
from dataclasses import dataclass, field


@dataclass
class Order:
    id: str
    user_id: str
    items: List['OrderItem'] = field(default_factory=list)

    @property
    def total(self) -> float:
        return sum(item.subtotal for item in self.items)


@dataclass
class OrderItem:
    product_id: str
    quantity: int
    price: float

    @property
    def subtotal(self) -> float:
        return self.quantity * self.price
