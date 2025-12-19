"""Order service with DTO transformations."""
from typing import List, Optional
from domain import Order, OrderRepository, User, UserRepository
from dto import OrderDTO, OrderCreateDTO


class OrderService:
    """Business logic for order operations."""

    def __init__(self):
        self._order_repository = OrderRepository()
        self._user_repository = UserRepository()

    def create_order(self, create_dto: OrderCreateDTO) -> OrderDTO:
        """Create a new order from DTO."""
        order = Order(
            order_id=create_dto.order_id,
            user_id=create_dto.user_id,
            items=create_dto.items
        )
        self._order_repository.save(order)

        # Update user's order list
        user = self._user_repository.find_by_id(create_dto.user_id)
        if user:
            user.add_order(order)

        return order.to_dto()

    def get_order(self, order_id: str) -> Optional[OrderDTO]:
        """Get order by ID and return as DTO."""
        order = self._order_repository.find_by_id(order_id)
        if order:
            return order.to_dto()
        return None

    def get_user_orders(self, user_id: str) -> List[OrderDTO]:
        """Get all orders for a user as DTOs."""
        orders = self._order_repository.find_by_user(user_id)
        return [order.to_dto() for order in orders]

    def confirm_order(self, order_id: str) -> bool:
        """Confirm an order."""
        order = self._order_repository.find_by_id(order_id)
        if order:
            order.confirm()
            return True
        return False

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        order = self._order_repository.find_by_id(order_id)
        if order:
            order.cancel()
            return True
        return False
