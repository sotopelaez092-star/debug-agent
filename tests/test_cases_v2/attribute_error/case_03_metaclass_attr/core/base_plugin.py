from abc import abstractmethod
from typing import Any, Dict
from .plugin_meta import PluginMeta


class BasePlugin(metaclass=PluginMeta):
    """Base class for all plugins."""

    plugin_name: str = "base"
    version: str = "1.0.0"
    author: str = "system"
    dependencies: list = []

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self._initialized = False

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the plugin."""
        pass

    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """Execute the plugin's main functionality."""
        pass

    def shutdown(self) -> None:
        """Clean up resources."""
        self._initialized = False

    def get_info(self) -> dict:
        """Get plugin information."""
        return {
            "name": self.plugin_name,
            "version": self.version,
            "initialized": self._initialized,
            "config": self.config,
        }

    @classmethod
    def get_metadata(cls) -> dict:
        """Get plugin metadata from metaclass."""
        return cls._meta
