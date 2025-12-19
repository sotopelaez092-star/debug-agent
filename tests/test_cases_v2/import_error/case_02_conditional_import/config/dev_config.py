"""
Development environment configuration.
"""

from .base_config import BaseConfig


class DevelopmentConfig(BaseConfig):
    """Development configuration."""

    DEBUG = True
    TESTING = False
    DATABASE_URI = "sqlite:///dev.db"
    LOG_LEVEL = "DEBUG"

    # Development-specific settings
    RELOAD_ON_CHANGE = True
    PROFILE_QUERIES = True
    SHOW_SQL_QUERIES = True

    # Relaxed security for development
    SECRET_KEY = "dev-secret-key-not-for-production"
    CORS_ENABLED = True
    ALLOWED_HOSTS = ["*"]

    def __init__(self):
        super().__init__()
        print("Loading development configuration")
