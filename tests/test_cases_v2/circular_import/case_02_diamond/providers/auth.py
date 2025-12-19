"""Authentication provider with session management."""
from typing import Optional
from core import ResourceManager, Session
# CIRCULAR IMPORT: Auth needs Storage to persist sessions
from providers.storage import StorageProvider


class Authenticator:
    """Handles user authentication and session management."""

    def __init__(self):
        self._manager = ResourceManager()
        # Need storage to persist sessions
        self._storage = StorageProvider()

    def authenticate(self, username: str, password: str) -> Optional[Session]:
        """Authenticate user and create session."""
        # Simple auth logic
        if username and password:
            session = Session(
                session_id=f"sess_{username}",
                user_id=username,
                permissions=["read", "write"]
            )
            # Store session for later retrieval
            self._storage.save_session(session)
            return session
        return None

    def validate_session(self, session_id: str) -> bool:
        """Validate if session is still active."""
        session = self._storage.get_session(session_id)
        return session is not None and session.is_active

    def logout(self, session_id: str) -> None:
        """Logout user and invalidate session."""
        session = self._storage.get_session(session_id)
        if session:
            session.is_active = False
            self._storage.update_session(session)

    def check_permission(self, session_id: str, permission: str) -> bool:
        """Check if session has specific permission."""
        session = self._storage.get_session(session_id)
        return session and session.has_permission(permission)
