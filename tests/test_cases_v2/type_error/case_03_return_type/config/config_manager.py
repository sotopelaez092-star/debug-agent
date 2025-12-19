"""Application configuration manager."""
import os
from loaders import load_json_config, load_env_config, merge_configs


class ConfigManager:
    """Manage application configuration from multiple sources."""

    def __init__(self, config_file=None):
        self.config_file = config_file or self._find_config_file()
        self._config = None
        self._loaded = False

    def _find_config_file(self):
        """Find configuration file in standard locations."""
        search_paths = [
            "config/app_config.json",
            "../config/app_config.json",
            "/etc/myapp/config.json",
        ]

        for path in search_paths:
            if os.path.exists(path):
                return path

        return "config/app_config.json"  # Default fallback

    def load(self):
        """Load configuration from file and environment."""
        if self._loaded:
            return self._config

        # Load from JSON file
        # BUG: This expects dict but gets tuple (dict, metadata)
        file_config = load_json_config(self.config_file)

        # Load from environment
        # BUG: This also expects dict but gets tuple
        env_config = load_env_config()

        # Merge configurations (env overrides file)
        # BUG: merge_configs receives tuples but expects dicts
        self._config = merge_configs(file_config, env_config)

        self._loaded = True
        return self._config

    def get(self, key, default=None):
        """Get configuration value by key (supports dot notation)."""
        if not self._loaded:
            self.load()

        # Support dot notation like "database.host"
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value

    def get_database_config(self):
        """Get database configuration."""
        if not self._loaded:
            self.load()

        # BUG: self._config.get() will fail if _config is tuple
        return self._config.get("database", {})

    def get_api_config(self):
        """Get API configuration."""
        if not self._loaded:
            self.load()

        return self._config.get("api", {})

    def get_logging_config(self):
        """Get logging configuration."""
        if not self._loaded:
            self.load()

        return self._config.get("logging", {})

    def is_feature_enabled(self, feature_name):
        """Check if a feature is enabled."""
        if not self._loaded:
            self.load()

        features = self._config.get("features", {})
        return features.get(feature_name, False)

    def reload(self):
        """Reload configuration from sources."""
        self._loaded = False
        return self.load()

    def to_dict(self):
        """Get full configuration as dictionary."""
        if not self._loaded:
            self.load()

        return self._config.copy()
