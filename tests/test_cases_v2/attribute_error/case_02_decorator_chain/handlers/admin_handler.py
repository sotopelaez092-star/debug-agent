from typing import Dict, List
from decorators import require_auth, require_role, log_call, log_errors, cache_invalidate
from decorators.logging import CallLogger


class AdminHandler:
    """Handler for admin operations with complex decorator chains."""

    def __init__(self, user_handler):
        self.user_handler = user_handler

    @log_call
    @log_errors
    @require_auth
    @require_role(["admin", "super_admin"])
    def grant_role(self, user_id: str, role: str) -> dict:
        """Grant a role to a user."""
        user = self.user_handler.get_user(user_id)
        if role not in user["roles"]:
            user["roles"].append(role)
        return user

    @log_call
    @log_errors
    @require_auth
    @require_role(["admin", "super_admin"])
    @cache_invalidate("get_user")
    def revoke_role(self, user_id: str, role: str) -> dict:
        """Revoke a role from a user."""
        user = self.user_handler.get_user(user_id)
        if role in user["roles"]:
            user["roles"].remove(role)
        return user

    @log_call
    @log_errors
    @require_auth
    @require_role(["super_admin"])
    def get_audit_logs(self) -> List[dict]:
        """Get all audit logs (super admin only)."""
        # BUG: Typo - should be get_logs() not get_log()
        return CallLogger.get_log()

    @log_call
    @log_errors
    @require_auth
    @require_role(["super_admin"])
    def clear_audit_logs(self) -> None:
        """Clear all audit logs (super admin only)."""
        CallLogger.clear()

    @log_call
    @log_errors
    @require_auth
    @require_role(["admin", "super_admin"])
    def bulk_update_roles(self, updates: Dict[str, List[str]]) -> Dict[str, dict]:
        """Bulk update roles for multiple users."""
        results = {}
        for user_id, roles in updates.items():
            user = self.user_handler.get_user(user_id)
            user["roles"] = roles
            results[user_id] = user
        return results
