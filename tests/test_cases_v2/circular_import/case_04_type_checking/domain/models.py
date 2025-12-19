"""Domain models with business logic."""
from typing import List, Optional
from datetime import datetime
# CIRCULAR IMPORT: Models need DTOs for serialization
from dto import UserDTO, OrderDTO


class User:
    """User domain model."""

    def __init__(self, user_id: str, username: str, email: str):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.created_at = datetime.now()
        self.orders: List['Order'] = []
        self.is_active = True

    def to_dto(self) -> UserDTO:
        """Convert to DTO for serialization."""
        return UserDTO.from_model(self)

    def deactivate(self) -> None:
        """Deactivate user account."""
        self.is_active = False

    def add_order(self, order: 'Order') -> None:
        """Add an order to user's order list."""
        self.orders.append(order)

    def get_total_spent(self) -> float:
        """Calculate total amount spent by user."""
        return sum(order.total for order in self.orders)


class Product:
    """Product domain model."""

    def __init__(self, product_id: str, name: str, price: float, stock: int):
        self.product_id = product_id
        self.name = name
        self.price = price
        self.stock = stock

    def is_available(self) -> bool:
        """Check if product is available."""
        return self.stock > 0

    def reserve(self, quantity: int) -> bool:
        """Reserve product stock."""
        if self.stock >= quantity:
            self.stock -= quantity
            return True
        return False


class Order:
    """Order domain model."""

    def __init__(self, order_id: str, user_id: str, items: List[dict]):
        self.order_id = order_id
        self.user_id = user_id
        self.items = items
        self.created_at = datetime.now()
        self.status = "pending"
        self.total = self._calculate_total()

    def _calculate_total(self) -> float:
        """Calculate order total."""
        return sum(item.get('price', 0) * item.get('quantity', 0) for item in self.items)

    def to_dto(self) -> OrderDTO:
        """Convert to DTO for serialization."""
        return OrderDTO.from_model(self)

    def confirm(self) -> None:
        """Confirm the order."""
        self.status = "confirmed"

    def cancel(self) -> None:
        """Cancel the order."""
        self.status = "cancelled"
