from typing import Dict, List
from decorators import require_auth, log_call, log_errors, cached, validate_input


class UserHandler:
    """Handler for user operations with decorator chain."""

    def __init__(self):
        self._users: Dict[str, dict] = {}

    @log_call
    @log_errors
    @cached(ttl_seconds=60)
    def get_user(self, user_id: str) -> dict:
        """Get a user by ID."""
        if user_id not in self._users:
            raise KeyError(f"User not found: {user_id}")
        return self._users[user_id]

    @log_call
    @log_errors
    @require_auth
    @validate_input({"username": str, "email": str})
    def create_user(self, user_id: str, username: str, email: str) -> dict:
        """Create a new user."""
        user = {
            "id": user_id,
            "username": username,
            "email": email,
            "roles": ["user"],
        }
        self._users[user_id] = user
        return user

    @log_call
    @log_errors
    @require_auth
    def list_users(self) -> List[dict]:
        """List all users."""
        return list(self._users.values())

    @log_call
    @log_errors
    @require_auth
    def delete_user(self, user_id: str) -> bool:
        """Delete a user."""
        if user_id in self._users:
            del self._users[user_id]
            return True
        return False
