"""Application settings with validation."""
from typing import Any, Dict, Optional
# CIRCULAR IMPORT: Settings needs engine to validate query execution settings
from engine import QueryExecutor


class Settings:
    """Manages application configuration settings."""

    def __init__(self):
        self._config: Dict[str, Any] = {
            # Database settings
            'postgres_host': 'localhost',
            'postgres_port': 5432,
            'redis_host': 'localhost',
            'redis_port': 6379,
            'mongo_host': 'localhost',
            'mongo_port': 27017,

            # Optimization settings
            'enable_optimization': True,
            'optimization_level': 2,
            'max_connections': 10,

            # Query settings
            'query_timeout': 30,
            'max_query_size': 1024
        }
        # Validate query execution settings
        self._executor = QueryExecutor()

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self._config[key] = value

    def validate_query_settings(self) -> bool:
        """Validate query execution settings."""
        # Test query execution with current settings
        try:
            test_query = "SELECT 1"
            result = self._executor.execute(test_query, 'postgres')
            return result is not None
        except Exception:
            return False

    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values."""
        return self._config.copy()

    def update(self, new_config: Dict[str, Any]) -> None:
        """Update multiple configuration values."""
        self._config.update(new_config)

    def reset(self) -> None:
        """Reset configuration to defaults."""
        self.__init__()
