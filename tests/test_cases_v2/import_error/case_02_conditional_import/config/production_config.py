"""
Production environment configuration.
"""

import os
from .base_config import BaseConfig


class ProductionConfig(BaseConfig):
    """Production configuration."""

    DEBUG = False
    TESTING = False
    DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://prod-db:5432/app')
    SECRET_KEY = os.getenv('SECRET_KEY')
    LOG_LEVEL = "WARNING"

    # Production-specific settings
    SSL_REQUIRED = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = 3600

    # Security settings
    CORS_ENABLED = False
    ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

    # Performance settings
    CACHE_TYPE = "redis"
    CACHE_REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')

    def __init__(self):
        super().__init__()
        print("Loading production configuration")
