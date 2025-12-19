"""Storage provider with access control."""
from typing import Optional, Dict, Any
from core import ResourceManager, Session
# CIRCULAR IMPORT: Storage needs Auth to verify access permissions
from providers.auth import Authenticator


class StorageProvider:
    """Provides persistent storage with authentication checks."""

    def __init__(self):
        self._manager = ResourceManager()
        self._sessions: Dict[str, Session] = {}
        self._data: Dict[str, Any] = {}
        # Need auth to verify access rights
        self._auth = Authenticator()

    def save_session(self, session: Session) -> None:
        """Save user session to storage."""
        self._sessions[session.session_id] = session

    def get_session(self, session_id: str) -> Optional[Session]:
        """Retrieve session from storage."""
        return self._sessions.get(session_id)

    def update_session(self, session: Session) -> None:
        """Update existing session."""
        if session.session_id in self._sessions:
            self._sessions[session.session_id] = session

    def save_data(self, key: str, value: Any, session_id: str) -> bool:
        """Save data with authentication check."""
        # Verify user has write permission
        if self._auth.check_permission(session_id, "write"):
            self._data[key] = value
            return True
        return False

    def get_data(self, key: str, session_id: str) -> Optional[Any]:
        """Retrieve data with authentication check."""
        # Verify user has read permission
        if self._auth.check_permission(session_id, "read"):
            return self._data.get(key)
        return None

    def delete_data(self, key: str, session_id: str) -> bool:
        """Delete data with authentication check."""
        if self._auth.check_permission(session_id, "write"):
            if key in self._data:
                del self._data[key]
                return True
        return False
