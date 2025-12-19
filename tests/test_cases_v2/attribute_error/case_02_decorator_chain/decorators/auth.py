from functools import wraps
from typing import Callable, List, Optional


class AuthContext:
    _current_user: Optional[dict] = None

    @classmethod
    def set_user(cls, user: dict) -> None:
        cls._current_user = user

    @classmethod
    def get_user(cls) -> Optional[dict]:
        return cls._current_user

    @classmethod
    def clear(cls) -> None:
        cls._current_user = None


def require_auth(func: Callable) -> Callable:
    """Decorator that requires authentication."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = AuthContext.get_user()
        if user is None:
            raise PermissionError("Authentication required")
        return func(*args, **kwargs)
    wrapper._requires_auth = True
    return wrapper


def require_role(roles: List[str]) -> Callable:
    """Decorator that requires specific roles."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = AuthContext.get_user()
            if user is None:
                raise PermissionError("Authentication required")
            user_roles = user.get("roles", [])
            if not any(role in user_roles for role in roles):
                raise PermissionError(f"Required roles: {roles}")
            return func(*args, **kwargs)
        wrapper._required_roles = roles
        return wrapper
    return decorator
