"""Order Data Transfer Objects."""
from typing import List
from datetime import datetime
from domain.models import Order


class OrderDTO:
    """Order DTO for API layer."""

    def __init__(self, order_id: str, user_id: str, items: List[dict],
                 total: float, status: str, created_at: datetime):
        self.order_id = order_id
        self.user_id = user_id
        self.items = items
        self.total = total
        self.status = status
        self.created_at = created_at

    @staticmethod
    def from_model(order: Order) -> 'OrderDTO':
        """Create DTO from domain model."""
        return OrderDTO(
            order_id=order.order_id,
            user_id=order.user_id,
            items=order.items,
            total=order.total,
            status=order.status,
            created_at=order.created_at
        )

    def to_model(self) -> Order:
        """Convert DTO to domain model."""
        order = Order(
            order_id=self.order_id,
            user_id=self.user_id,
            items=self.items
        )
        order.status = self.status
        order.created_at = self.created_at
        return order

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'order_id': self.order_id,
            'user_id': self.user_id,
            'items': self.items,
            'total': self.total,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }


class OrderCreateDTO:
    """DTO for creating new orders."""

    def __init__(self, order_id: str, user_id: str, items: List[dict]):
        self.order_id = order_id
        self.user_id = user_id
        self.items = items

    @staticmethod
    def from_dict(data: dict) -> 'OrderCreateDTO':
        """Create DTO from dictionary."""
        return OrderCreateDTO(
            order_id=data['order_id'],
            user_id=data['user_id'],
            items=data['items']
        )
