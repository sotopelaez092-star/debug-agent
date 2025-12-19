"""
Staging environment configuration.
"""

import os
from .base_config import BaseConfig


class StagingConfig(BaseConfig):
    """Staging configuration - similar to production but with some debugging."""

    DEBUG = True  # Enable debug mode in staging
    TESTING = False
    DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://staging-db:5432/app')
    SECRET_KEY = os.getenv('SECRET_KEY', 'staging-secret-key')
    LOG_LEVEL = "INFO"

    # Staging-specific settings
    SSL_REQUIRED = False  # Optional SSL in staging
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True

    # More relaxed security for testing
    CORS_ENABLED = True
    ALLOWED_HOSTS = ["*.staging.example.com", "localhost"]

    # Use Redis but with shorter timeout
    CACHE_TYPE = "redis"
    CACHE_REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
    CACHE_DEFAULT_TIMEOUT = 60

    def __init__(self):
        super().__init__()
        print("Loading staging configuration")
