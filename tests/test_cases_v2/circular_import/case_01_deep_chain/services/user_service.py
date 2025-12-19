from typing import Optional, List
from models import User
from repositories import UserRepository
# CIRCULAR IMPORT: UserService needs OrderService for order history
from services.order_service import OrderService


class UserService:
    def __init__(self):
        self._repo = UserRepository()
        self._order_service = OrderService()

    def create_user(self, user_id: str, name: str, email: str) -> User:
        user = User(id=user_id, name=name, email=email)
        self._repo.save(user)
        return user

    def get_user(self, user_id: str) -> Optional[User]:
        return self._repo.find_by_id(user_id)

    def get_user_with_orders(self, user_id: str) -> Optional[User]:
        user = self._repo.find_by_id(user_id)
        if user:
            orders = self._order_service.get_orders_for_user(user_id)
            user.orders = orders
        return user

    def list_users(self) -> List[User]:
        return self._repo.find_all()
