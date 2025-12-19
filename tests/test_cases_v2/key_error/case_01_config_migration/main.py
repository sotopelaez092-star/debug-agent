"""
Main application entry point.
Loads configuration and initializes database and cache.
"""
from config_loader import ConfigLoader
from database import DatabaseConnection
from cache_manager import CacheManager
import os


def main():
    """Main application function."""
    # Load configuration from file
    config_file = os.path.join(os.path.dirname(__file__), 'config.json')
    loader = ConfigLoader(config_file)
    config = loader.load()

    print("Configuration loaded successfully")
    print(f"Config version: {config.get('version', 'unknown')}")

    # Initialize database connection
    print("\n--- Initializing Database ---")
    db = DatabaseConnection(config)
    db.connect()

    # Initialize cache
    print("\n--- Initializing Cache ---")
    cache = CacheManager(config)
    cache.initialize()

    print("\n--- Application Ready ---")
    print(f"Database connected: {db.is_connected()}")
    print(f"Cache keys: {cache.keys()}")

    # Cleanup
    db.disconnect()


if __name__ == "__main__":
    main()
