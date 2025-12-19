"""Core resource manager that coordinates authentication and storage."""
from typing import Dict, Any


class ResourceManager:
    """Central manager for coordinating system resources."""

    def __init__(self):
        self._resources: Dict[str, Any] = {}

    def register_resource(self, name: str, resource: Any) -> None:
        """Register a new resource."""
        self._resources[name] = resource

    def get_resource(self, name: str) -> Any:
        """Get a registered resource."""
        return self._resources.get(name)

    def validate_access(self, user_id: str, resource: str) -> bool:
        """Validate if user can access resource."""
        # Simple validation logic
        return user_id is not None and resource in self._resources


class Session:
    """User session data."""

    def __init__(self, session_id: str, user_id: str, permissions: list):
        self.session_id = session_id
        self.user_id = user_id
        self.permissions = permissions
        self.is_active = True

    def has_permission(self, permission: str) -> bool:
        """Check if session has specific permission."""
        return permission in self.permissions
