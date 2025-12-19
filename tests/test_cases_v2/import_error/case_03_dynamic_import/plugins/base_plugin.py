"""
Base plugin class for all plugins.
"""

from abc import ABC, abstractmethod


class BasePlugin(ABC):
    """Abstract base class for all plugins."""

    def __init__(self, name):
        self.name = name
        self.enabled = True

    @abstractmethod
    def initialize(self):
        """Initialize the plugin."""
        pass

    @abstractmethod
    def execute(self, *args, **kwargs):
        """Execute the plugin's main functionality."""
        pass

    def enable(self):
        """Enable the plugin."""
        self.enabled = True
        print(f"Plugin '{self.name}' enabled")

    def disable(self):
        """Disable the plugin."""
        self.enabled = False
        print(f"Plugin '{self.name}' disabled")

    def get_info(self):
        """Get plugin information."""
        return {
            "name": self.name,
            "enabled": self.enabled,
            "type": self.__class__.__name__
        }
