"""
Application factory module.
"""

import os
from config import config


class Application:
    """Main application class."""

    def __init__(self, config_obj=None):
        """Initialize application with configuration."""
        self.config = config_obj or config
        self.setup()

    def setup(self):
        """Setup application components."""
        print(f"Setting up application with config: {self.config.__class__.__name__}")
        print(f"Debug mode: {self.config.DEBUG}")
        print(f"Database: {self.config.DATABASE_URI}")

    def run(self):
        """Run the application."""
        print(f"Running application in {os.getenv('APP_ENV', 'development')} mode")
        print(f"Log level: {self.config.LOG_LEVEL}")

        if self.config.DEBUG:
            print("Debug mode enabled - verbose logging active")

        return True


def create_app():
    """Application factory function."""
    return Application()
