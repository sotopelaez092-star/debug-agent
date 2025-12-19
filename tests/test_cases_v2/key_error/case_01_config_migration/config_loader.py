"""
Configuration loader module for loading and managing application config.
Supports both legacy and new configuration formats.
"""
import json
import os
from typing import Dict, Any
from pathlib import Path


class ConfigLoader:
    """Handles loading configuration from JSON files."""

    def __init__(self, config_path: str):
        self.config_path = config_path
        self._config: Dict[str, Any] = {}

    def load(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            self._config = json.load(f)

        return self._config

    def get(self, key_path: str, default=None) -> Any:
        """
        Get configuration value by dot-separated key path.
        Example: 'database.host' or 'cache.redis_host'
        """
        keys = key_path.split('.')
        value = self._config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration section."""
        return self._config.get('database', {})

    def get_cache_config(self) -> Dict[str, Any]:
        """Get cache configuration section."""
        return self._config.get('cache', {})

    def reload(self) -> None:
        """Reload configuration from file."""
        self.load()
