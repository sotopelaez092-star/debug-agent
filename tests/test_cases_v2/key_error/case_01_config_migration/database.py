"""
Database connection manager using configuration settings.
This module manages database connections using the loaded config.
"""
from typing import Optional, Dict, Any
import time


class DatabaseConnection:
    """Manages database connections with configuration."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connection = None
        self._connected = False

    def connect(self) -> bool:
        """Establish database connection using config settings."""
        try:
            # Extract connection parameters from config
            # This code expects the OLD config structure
            host = self.config['database']['host']
            port = self.config['database']['port']
            username = self.config['database']['credentials']['username']
            password = self.config['database']['credentials']['password']

            # Simulate connection
            print(f"Connecting to database at {host}:{port}")
            print(f"Using credentials for user: {username}")

            # Simulate connection delay
            time.sleep(0.1)

            self._connected = True
            self.connection = {
                'host': host,
                'port': port,
                'user': username
            }

            return True

        except KeyError as e:
            print(f"Configuration error: Missing key {e}")
            raise

    def disconnect(self) -> None:
        """Close database connection."""
        if self._connected:
            print("Disconnecting from database")
            self.connection = None
            self._connected = False

    def is_connected(self) -> bool:
        """Check if database is connected."""
        return self._connected

    def execute_query(self, query: str) -> list:
        """Execute a database query."""
        if not self._connected:
            raise RuntimeError("Not connected to database")

        # Simulate query execution
        return []
