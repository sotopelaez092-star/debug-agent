"""
Configuration for authentication system.
"""

import os
from typing import Dict, Any


class AuthConfig:
    """Authentication configuration."""

    def __init__(self):
        self.session_timeout = int(os.getenv('SESSION_TIMEOUT', '3600'))
        self.enable_sso = os.getenv('ENABLE_SSO', 'true').lower() == 'true'
        self.oauth_client_id = os.getenv('OAUTH_CLIENT_ID', 'default_client')
        self.oauth_client_secret = os.getenv('OAUTH_CLIENT_SECRET', 'default_secret')
        self.saml_entity_id = os.getenv('SAML_ENTITY_ID', 'default_entity')
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'session_timeout': self.session_timeout,
            'enable_sso': self.enable_sso,
            'oauth_client_id': self.oauth_client_id,
            'saml_entity_id': self.saml_entity_id,
            'log_level': self.log_level
        }


def setup_logging(config: AuthConfig):
    """Setup logging."""
    import logging

    logging.basicConfig(
        level=getattr(logging, config.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
