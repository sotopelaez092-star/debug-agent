"""API handler that uses both authentication and storage."""
from typing import Optional, Dict, Any
from core import Session
from providers import Authenticator, StorageProvider


class APIHandler:
    """Handles API requests with authentication and data storage."""

    def __init__(self):
        self._auth = Authenticator()
        self._storage = StorageProvider()

    def login(self, username: str, password: str) -> Optional[str]:
        """Handle login request."""
        session = self._auth.authenticate(username, password)
        if session:
            return session.session_id
        return None

    def save_user_data(self, session_id: str, key: str, value: Any) -> bool:
        """Save user data via API."""
        if self._auth.validate_session(session_id):
            return self._storage.save_data(key, value, session_id)
        return False

    def get_user_data(self, session_id: str, key: str) -> Optional[Any]:
        """Retrieve user data via API."""
        if self._auth.validate_session(session_id):
            return self._storage.get_data(key, session_id)
        return None

    def logout(self, session_id: str) -> None:
        """Handle logout request."""
        self._auth.logout(session_id)
