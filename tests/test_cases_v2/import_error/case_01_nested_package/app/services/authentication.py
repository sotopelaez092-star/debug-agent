"""
Authentication service module.
"""

import hashlib
import secrets


class AuthService:
    """Handles user authentication and token management."""

    def __init__(self):
        self.active_sessions = {}

    def generate_token(self, user_id):
        """Generate a secure authentication token."""
        token = secrets.token_hex(32)
        self.active_sessions[token] = user_id
        return token

    def validate_token(self, token):
        """Validate an authentication token."""
        return token in self.active_sessions

    def hash_password(self, password):
        """Hash a password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
