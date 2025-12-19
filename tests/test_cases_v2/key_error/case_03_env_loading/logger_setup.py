"""
Logger setup module.
Configures application logging from environment settings.
"""
from app_config import AppConfig


class LoggerSetup:
    """Configures application logging."""

    def __init__(self, app_config: AppConfig):
        self.config = app_config
        self.log_level = None

    def configure(self) -> None:
        """Configure logger from config."""
        app_name = self.config.get_app_name()
        # This will fail because APP_NAME doesn't exist in dev env
        log_level = self.config.config.get('log_level', 'INFO')

        print(f"Configuring logger for: {app_name}")
        print(f"Log level: {log_level}")

        self.log_level = log_level

    def get_level(self) -> str:
        """Get current log level."""
        return self.log_level or 'INFO'

    def log(self, level: str, message: str) -> None:
        """Log a message."""
        print(f"[{level}] {message}")
