"""DTO mapper utilities."""
from typing import List
from domain.models import User, Order
from dto.user_dto import UserDTO
from dto.order_dto import OrderDTO


class DTOMapper:
    """Utility class for mapping between domain models and DTOs."""

    @staticmethod
    def user_to_dto(user: User) -> UserDTO:
        """Convert User model to DTO."""
        return UserDTO.from_model(user)

    @staticmethod
    def users_to_dtos(users: List[User]) -> List[UserDTO]:
        """Convert list of User models to DTOs."""
        return [DTOMapper.user_to_dto(user) for user in users]

    @staticmethod
    def dto_to_user(dto: UserDTO) -> User:
        """Convert UserDTO to model."""
        return dto.to_model()

    @staticmethod
    def order_to_dto(order: Order) -> OrderDTO:
        """Convert Order model to DTO."""
        return OrderDTO.from_model(order)

    @staticmethod
    def orders_to_dtos(orders: List[Order]) -> List[OrderDTO]:
        """Convert list of Order models to DTOs."""
        return [DTOMapper.order_to_dto(order) for order in orders]

    @staticmethod
    def dto_to_order(dto: OrderDTO) -> Order:
        """Convert OrderDTO to model."""
        return dto.to_model()
