"""
Main application entry point.
Loads environment configuration and initializes services.
"""
import os
from env_loader import EnvLoader
from app_config import AppConfig
from database_setup import DatabaseSetup
from logger_setup import LoggerSetup


def main():
    """Main application function."""
    print("=== Application Startup ===\n")

    # Load environment variables from .env file
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    env_loader = EnvLoader(env_file)
    env_vars = env_loader.load_from_file()

    print(f"Loaded {len(env_vars)} environment variables")
    print(f"Environment: development\n")

    # Load application configuration
    # This will fail because app_config expects PRODUCTION var names
    # but .env file has DEVELOPMENT var names
    app_config = AppConfig(env_loader)
    config = app_config.load_config()

    print("Configuration loaded successfully")
    print(f"App: {config['app_name']} v{config['app_version']}\n")

    # Initialize database
    print("--- Database Setup ---")
    db_setup = DatabaseSetup(app_config)
    db_setup.initialize()
    print(f"Database connected: {db_setup.test_connection()}\n")

    # Configure logger
    print("--- Logger Setup ---")
    logger = LoggerSetup(app_config)
    logger.configure()
    print(f"Logger configured: {logger.get_level()}\n")

    print("=== Startup Complete ===")


if __name__ == "__main__":
    main()
