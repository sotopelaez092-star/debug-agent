"""
Environment variable schema definitions.
Defines expected environment variables for different deployment stages.
"""

# Production environment schema
PRODUCTION_ENV_SCHEMA = {
    "APP_NAME": str,
    "APP_VERSION": str,
    "DB_HOST": str,
    "DB_PORT": int,
    "DB_NAME": str,
    "DB_USER": str,
    "DB_PASSWORD": str,
    "REDIS_URL": str,
    "API_KEY": str,
    "SECRET_KEY": str,
    "LOG_LEVEL": str,
}

# Development environment schema (slightly different keys)
DEVELOPMENT_ENV_SCHEMA = {
    "APPLICATION_NAME": str,  # Different from APP_NAME
    "APPLICATION_VERSION": str,  # Different from APP_VERSION
    "DATABASE_HOST": str,  # Different from DB_HOST
    "DATABASE_PORT": int,
    "DATABASE_NAME": str,
    "DATABASE_USER": str,
    "DATABASE_PASSWORD": str,
    "CACHE_URL": str,  # Different from REDIS_URL
    "API_SECRET_KEY": str,  # Different from API_KEY
    "APP_SECRET": str,  # Different from SECRET_KEY
    "LOGGING_LEVEL": str,  # Different from LOG_LEVEL
}


def get_env_schema(environment: str) -> dict:
    """Get the appropriate schema for the environment."""
    if environment == "production":
        return PRODUCTION_ENV_SCHEMA
    elif environment == "development":
        return DEVELOPMENT_ENV_SCHEMA
    else:
        raise ValueError(f"Unknown environment: {environment}")
