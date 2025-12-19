"""
Testing environment configuration.
"""

from .base_config import BaseConfig


class TestingConfig(BaseConfig):
    """Testing configuration for running tests."""

    DEBUG = True
    TESTING = True
    DATABASE_URI = "sqlite:///:memory:"
    SECRET_KEY = "test-secret-key"
    LOG_LEVEL = "DEBUG"

    # Testing-specific settings
    WTF_CSRF_ENABLED = False
    PRESERVE_CONTEXT_ON_EXCEPTION = False

    # Fast cache for tests
    CACHE_TYPE = "simple"
    CACHE_DEFAULT_TIMEOUT = 0

    # Disable external services in tests
    DISABLE_EMAIL = True
    DISABLE_ANALYTICS = True

    def __init__(self):
        super().__init__()
        print("Loading testing configuration")

    def validate(self):
        """Skip validation in test mode."""
        pass
