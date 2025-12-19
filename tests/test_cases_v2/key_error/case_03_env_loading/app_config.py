"""
Application configuration built from environment variables.
This module expects PRODUCTION environment variable names.
"""
from typing import Dict, Any
from env_loader import EnvLoader


class AppConfig:
    """Application configuration from environment variables."""

    def __init__(self, env_loader: EnvLoader):
        self.env = env_loader
        self.config: Dict[str, Any] = {}

    def load_config(self) -> Dict[str, Any]:
        """
        Load all configuration from environment variables.
        This code expects PRODUCTION env var names (APP_NAME, DB_HOST, etc.)
        """
        # Application settings
        self.config['app_name'] = self.env.require('APP_NAME')
        self.config['app_version'] = self.env.require('APP_VERSION')

        # Database settings
        self.config['database'] = {
            'host': self.env.require('DB_HOST'),
            'port': int(self.env.require('DB_PORT')),
            'name': self.env.require('DB_NAME'),
            'user': self.env.require('DB_USER'),
            'password': self.env.require('DB_PASSWORD'),
        }

        # Cache settings
        self.config['redis_url'] = self.env.require('REDIS_URL')

        # Security settings
        self.config['api_key'] = self.env.require('API_KEY')
        self.config['secret_key'] = self.env.require('SECRET_KEY')

        # Logging settings
        self.config['log_level'] = self.env.get('LOG_LEVEL', 'INFO')

        return self.config

    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration."""
        if 'database' not in self.config:
            self.load_config()
        return self.config['database']

    def get_app_name(self) -> str:
        """Get application name."""
        if 'app_name' not in self.config:
            self.load_config()
        return self.config['app_name']

    def get_api_key(self) -> str:
        """Get API key."""
        if 'api_key' not in self.config:
            self.load_config()
        return self.config['api_key']
