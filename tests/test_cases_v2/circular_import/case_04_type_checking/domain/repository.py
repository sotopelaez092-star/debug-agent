"""Domain repositories for data access."""
from typing import List, Optional
from domain.models import User, Order


class UserRepository:
    """Repository for User entities."""

    def __init__(self):
        self._users: dict = {}

    def save(self, user: User) -> None:
        """Save user to repository."""
        self._users[user.user_id] = user

    def find_by_id(self, user_id: str) -> Optional[User]:
        """Find user by ID."""
        return self._users.get(user_id)

    def find_all(self) -> List[User]:
        """Get all users."""
        return list(self._users.values())

    def delete(self, user_id: str) -> bool:
        """Delete user from repository."""
        if user_id in self._users:
            del self._users[user_id]
            return True
        return False


class OrderRepository:
    """Repository for Order entities."""

    def __init__(self):
        self._orders: dict = {}

    def save(self, order: Order) -> None:
        """Save order to repository."""
        self._orders[order.order_id] = order

    def find_by_id(self, order_id: str) -> Optional[Order]:
        """Find order by ID."""
        return self._orders.get(order_id)

    def find_by_user(self, user_id: str) -> List[Order]:
        """Find all orders for a user."""
        return [order for order in self._orders.values() if order.user_id == user_id]

    def find_all(self) -> List[Order]:
        """Get all orders."""
        return list(self._orders.values())
