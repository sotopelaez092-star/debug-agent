"""User Data Transfer Objects."""
from typing import Optional, List
from datetime import datetime
# CIRCULAR IMPORT: DTOs need domain models for type hints and conversions
from domain.models import User


class UserDTO:
    """User DTO for API layer."""

    def __init__(self, user_id: str, username: str, email: str,
                 created_at: datetime, is_active: bool = True):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.created_at = created_at
        self.is_active = is_active

    @staticmethod
    def from_model(user: User) -> 'UserDTO':
        """Create DTO from domain model."""
        return UserDTO(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            created_at=user.created_at,
            is_active=user.is_active
        )

    def to_model(self) -> User:
        """Convert DTO to domain model."""
        user = User(
            user_id=self.user_id,
            username=self.username,
            email=self.email
        )
        user.created_at = self.created_at
        user.is_active = self.is_active
        return user

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active
        }


class UserCreateDTO:
    """DTO for creating new users."""

    def __init__(self, user_id: str, username: str, email: str):
        self.user_id = user_id
        self.username = username
        self.email = email

    @staticmethod
    def from_dict(data: dict) -> 'UserCreateDTO':
        """Create DTO from dictionary."""
        return UserCreateDTO(
            user_id=data['user_id'],
            username=data['username'],
            email=data['email']
        )
