"""
Base configuration class.
"""


class BaseConfig:
    """Base configuration with common settings."""

    DEBUG = False
    TESTING = False
    DATABASE_URI = None
    SECRET_KEY = "change-me-in-production"
    LOG_LEVEL = "INFO"

    # API settings
    API_TIMEOUT = 30
    API_RETRY_COUNT = 3

    # Cache settings
    CACHE_TYPE = "simple"
    CACHE_DEFAULT_TIMEOUT = 300

    def __init__(self):
        self.validate()

    def validate(self):
        """Validate configuration."""
        if not self.SECRET_KEY or self.SECRET_KEY == "change-me-in-production":
            if not self.DEBUG:
                raise ValueError("SECRET_KEY must be set in production")

    def get_database_uri(self):
        """Get database connection URI."""
        return self.DATABASE_URI

    def to_dict(self):
        """Convert config to dictionary."""
        return {
            key: value
            for key, value in self.__class__.__dict__.items()
            if not key.startswith('_') and not callable(value)
        }
