"""
Session management for the application.
Handles user sessions, caching, and lifecycle.
"""

from typing import Dict, Optional
from api_exports import *  # Star import - uses public API
import logging

logger = logging.getLogger(__name__)


class SessionCache:
    """Cache for active user sessions."""

    def __init__(self):
        self._sessions: Dict[str, UserSession] = {}
        logger.info("Session cache initialized")

    def add(self, token: str, session: UserSession):
        """Add a session to the cache."""
        self._sessions[token] = session
        logger.debug(f"Session added to cache: {token}")

    def get(self, token: str) -> Optional[UserSession]:
        """Get a session from the cache."""
        return self._sessions.get(token)

    def remove(self, token: str):
        """Remove a session from the cache."""
        if token in self._sessions:
            del self._sessions[token]
            logger.debug(f"Session removed from cache: {token}")

    def clear_inactive(self):
        """Clear all inactive sessions from cache."""
        inactive = [token for token, session in self._sessions.items() if not session.is_active]

        for token in inactive:
            self.remove(token)

        logger.info(f"Cleared {len(inactive)} inactive sessions")


class SessionManager:
    """Manages user sessions for the application."""

    def __init__(self):
        self.cache = SessionCache()
        logger.info("Session manager initialized")

    def login(self, username: str, password: str) -> Optional[str]:
        """Login a user and return a session token."""
        logger.info(f"Login attempt for user: {username}")

        session = authenticate_user(username, password)

        if session:
            self.cache.add(session.token, session)
            logger.info(f"Login successful for user: {username}")
            return session.token

        logger.warning(f"Login failed for user: {username}")
        return None

    def create_direct_session(self, user_id: int, metadata: Dict[str, any]) -> Optional[str]:
        """
        Create a session directly without authentication.
        Used for SSO and trusted integrations.
        """
        logger.info(f"Creating direct session for user_id: {user_id}")

        # Generate a token for the direct session
        import time
        token = f"direct_token_{user_id}_{int(time.time())}"

        # Use the public API to create session
        # This uses the function that was removed from __all__
        session = create_session(user_id, token, metadata)

        self.cache.add(token, session)
        logger.info(f"Direct session created for user_id: {user_id}")

        return token

    def logout(self, token: str):
        """Logout a user by invalidating their session."""
        session = self.cache.get(token)

        if session:
            session.invalidate()
            self.cache.remove(token)
            logger.info(f"User logged out: {token}")
        else:
            logger.warning(f"Logout attempted for unknown token: {token}")

    def get_session(self, token: str) -> Optional[UserSession]:
        """Get an active session by token."""
        if not validate_token(token):
            return None

        return self.cache.get(token)

    def refresh_session(self, old_token: str) -> Optional[str]:
        """Refresh a session and return new token."""
        session = self.cache.get(old_token)

        if not session:
            return None

        new_token = refresh_token(old_token)

        if new_token:
            self.cache.remove(old_token)
            self.cache.add(new_token, session)
            logger.info(f"Session refreshed: {old_token} -> {new_token}")

        return new_token
