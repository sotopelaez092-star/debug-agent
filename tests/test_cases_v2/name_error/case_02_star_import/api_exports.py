"""
Public API exports for the authentication module.
This module defines what gets exported with star imports.
"""

from typing import Optional, Dict, Any


# Public API - only these are exported with star import
__all__ = [
    'authenticate_user',
    'validate_token',
    'refresh_token',
    'UserSession',
    # NOTE: 'create_session' was removed from public API in v2.0
    # It's now an internal implementation detail
]


class UserSession:
    """Represents an authenticated user session."""

    def __init__(self, user_id: int, token: str, metadata: Dict[str, Any]):
        self.user_id = user_id
        self.token = token
        self.metadata = metadata
        self.is_active = True

    def invalidate(self):
        """Invalidate this session."""
        self.is_active = False


def authenticate_user(username: str, password: str) -> Optional[UserSession]:
    """Authenticate a user with username and password."""
    # Simplified authentication logic
    if not username or not password:
        return None

    # Simulate successful authentication
    user_id = hash(username) % 1000
    token = f"token_{username}_{hash(password)}"

    session = _create_session_internal(user_id, token, {'username': username})
    return session


def validate_token(token: str) -> bool:
    """Validate an authentication token."""
    if not token or not token.startswith('token_'):
        return False
    return True


def refresh_token(old_token: str) -> Optional[str]:
    """Refresh an authentication token."""
    if not validate_token(old_token):
        return None

    # Generate new token
    import time
    new_token = f"{old_token}_refreshed_{int(time.time())}"
    return new_token


def _create_session_internal(user_id: int, token: str, metadata: Dict[str, Any]) -> UserSession:
    """
    Internal function to create sessions.
    This was previously named 'create_session' and was public,
    but has been made internal in v2.0 refactoring.
    """
    return UserSession(user_id, token, metadata)


# Internal helpers not exported
def _hash_password(password: str) -> str:
    """Internal password hashing."""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()


def _verify_password(password: str, password_hash: str) -> bool:
    """Internal password verification."""
    return _hash_password(password) == password_hash
