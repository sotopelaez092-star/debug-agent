"""
Database setup module.
Initializes database connection using app configuration.
"""
from typing import Optional
from app_config import AppConfig


class DatabaseSetup:
    """Handles database initialization and connection."""

    def __init__(self, app_config: AppConfig):
        self.config = app_config
        self.connection = None

    def initialize(self) -> bool:
        """Initialize database connection."""
        db_config = self.config.get_database_config()

        print("Initializing database connection...")
        print(f"  Host: {db_config['host']}")
        print(f"  Port: {db_config['port']}")
        print(f"  Database: {db_config['name']}")
        print(f"  User: {db_config['user']}")

        # Simulate connection
        self.connection = {
            'connected': True,
            'host': db_config['host'],
            'database': db_config['name']
        }

        return True

    def test_connection(self) -> bool:
        """Test database connection."""
        if not self.connection:
            return False
        return self.connection.get('connected', False)

    def close(self) -> None:
        """Close database connection."""
        if self.connection:
            print("Closing database connection...")
            self.connection = None
