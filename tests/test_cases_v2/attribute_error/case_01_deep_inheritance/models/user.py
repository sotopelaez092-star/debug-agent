from typing import List, Tuple, Optional
from .base import BaseEntity


class User(BaseEntity):
    """Standard user entity."""

    def __init__(self, entity_id: str, username: str, email: str):
        super().__init__(entity_id)
        self.username = username
        self.email = email
        self.is_active = True
        self.permissions: List[str] = []

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            "username": self.username,
            "email": self.email,
            "is_active": self.is_active,
            "permissions": self.permissions,
        })
        return data

    def validate(self) -> Tuple[bool, List[str]]:
        is_valid, errors = super().validate()
        if not self.username:
            errors.append("username is required")
            is_valid = False
        if not self.email or "@" not in self.email:
            errors.append("valid email is required")
            is_valid = False
        return is_valid, errors

    def grant_permission(self, permission: str) -> None:
        if permission not in self.permissions:
            self.permissions.append(permission)
            self.log_action("grant_permission", details=permission)
            self.touch()

    def revoke_permission(self, permission: str) -> None:
        if permission in self.permissions:
            self.permissions.remove(permission)
            self.log_action("revoke_permission", details=permission)
            self.touch()

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions
