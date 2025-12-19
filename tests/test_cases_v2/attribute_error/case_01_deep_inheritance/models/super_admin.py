from typing import List, Tuple
from .admin import AdminUser


class SuperAdmin(AdminUser):
    """Super admin with full system access."""

    SUPER_PERMISSIONS = ["system.admin", "audit.read", "audit.write", "users.delete"]

    def __init__(self, entity_id: str, username: str, email: str):
        # Super admins belong to the System department
        super().__init__(entity_id, username, email, department="System")
        self.access_level = "full"
        # Grant super admin permissions
        for perm in self.SUPER_PERMISSIONS:
            self.grant_permission(perm)

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            "access_level": self.access_level,
            "is_super_admin": True,
        })
        return data

    def get_system_audit_log(self) -> List[dict]:
        """Get system-wide audit log (super admin only)."""
        # BUG: Typo - should be get_audit_trail() not get_audit_trial()
        return [
            {"entry": entry, "source": "super_admin"}
            for entry in self.get_audit_trial()
        ]

    def elevate_to_admin(self, user_id: str) -> bool:
        """Elevate a user to admin status."""
        self.log_action("elevate_user", details=f"Elevated {user_id} to admin")
        return True

    def revoke_admin(self, user_id: str) -> bool:
        """Revoke admin status from a user."""
        self.log_action("revoke_admin", details=f"Revoked admin from {user_id}")
        return True
