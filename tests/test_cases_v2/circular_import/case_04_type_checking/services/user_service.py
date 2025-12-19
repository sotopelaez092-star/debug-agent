"""User service with DTO transformations."""
from typing import List, Optional
from domain import User, UserRepository
# CIRCULAR IMPORT: Service needs DTOs for API layer
from dto import UserDTO, UserCreateDTO


class UserService:
    """Business logic for user operations."""

    def __init__(self):
        self._repository = UserRepository()

    def create_user(self, create_dto: UserCreateDTO) -> UserDTO:
        """Create a new user from DTO."""
        user = User(
            user_id=create_dto.user_id,
            username=create_dto.username,
            email=create_dto.email
        )
        self._repository.save(user)
        return user.to_dto()

    def get_user(self, user_id: str) -> Optional[UserDTO]:
        """Get user by ID and return as DTO."""
        user = self._repository.find_by_id(user_id)
        if user:
            return user.to_dto()
        return None

    def get_all_users(self) -> List[UserDTO]:
        """Get all users as DTOs."""
        users = self._repository.find_all()
        return [user.to_dto() for user in users]

    def deactivate_user(self, user_id: str) -> bool:
        """Deactivate a user account."""
        user = self._repository.find_by_id(user_id)
        if user:
            user.deactivate()
            return True
        return False

    def update_user(self, user_id: str, update_dto: UserDTO) -> Optional[UserDTO]:
        """Update user from DTO."""
        user = self._repository.find_by_id(user_id)
        if user:
            user.username = update_dto.username
            user.email = update_dto.email
            return user.to_dto()
        return None
