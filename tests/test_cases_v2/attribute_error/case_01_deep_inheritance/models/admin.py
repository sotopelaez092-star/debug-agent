from typing import List, Tuple
from .user import User


class AdminUser(User):
    """Admin user with elevated privileges."""

    ADMIN_PERMISSIONS = ["users.read", "users.write", "settings.read", "settings.write"]

    def __init__(self, entity_id: str, username: str, email: str, department: str):
        super().__init__(entity_id, username, email)
        self.department = department
        self.managed_users: List[str] = []
        # Grant default admin permissions
        for perm in self.ADMIN_PERMISSIONS:
            self.grant_permission(perm)

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            "department": self.department,
            "managed_users": self.managed_users,
            "is_admin": True,
        })
        return data

    def validate(self) -> Tuple[bool, List[str]]:
        is_valid, errors = super().validate()
        if not self.department:
            errors.append("department is required for admin users")
            is_valid = False
        return is_valid, errors

    def add_managed_user(self, user_id: str) -> None:
        if user_id not in self.managed_users:
            self.managed_users.append(user_id)
            self.log_action("add_managed_user", details=user_id)
            self.touch()

    def remove_managed_user(self, user_id: str) -> None:
        if user_id in self.managed_users:
            self.managed_users.remove(user_id)
            self.log_action("remove_managed_user", details=user_id)
            self.touch()

    def can_manage_user(self, user_id: str) -> bool:
        return user_id in self.managed_users
