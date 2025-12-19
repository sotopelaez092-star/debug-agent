"""
Plugin manager for loading and managing plugins dynamically.
"""

import importlib
import sys
from pathlib import Path


class PluginManager:
    """Manages dynamic loading and execution of plugins."""

    def __init__(self):
        self.plugins = {}
        self.plugin_registry = {
            "processor": "plugins.data_processor_plugin.DataProcessorPlugin",
            "validator": "plugins.validation_plugin.ValidationPlugin",
            "analytics": "plugins.analytics_plugin.AnalyticsPlugin",
            # Intentional error: wrong module path - should be data_transformer_plugin
            "transformer": "plugins.transformer_plugin.DataTransformerPlugin"
        }

    def load_plugin(self, plugin_key):
        """
        Dynamically load a plugin by its key.

        Args:
            plugin_key: Key from plugin_registry

        Returns:
            Plugin instance or None if loading fails
        """
        if plugin_key in self.plugins:
            print(f"Plugin '{plugin_key}' already loaded")
            return self.plugins[plugin_key]

        if plugin_key not in self.plugin_registry:
            print(f"Unknown plugin key: {plugin_key}")
            return None

        module_path = self.plugin_registry[plugin_key]
        try:
            # Split module path into module and class
            module_name, class_name = module_path.rsplit('.', 1)

            # Dynamically import the module
            module = importlib.import_module(module_name)

            # Get the class from the module
            plugin_class = getattr(module, class_name)

            # Instantiate the plugin
            plugin = plugin_class()
            plugin.initialize()

            # Store in registry
            self.plugins[plugin_key] = plugin
            print(f"Successfully loaded plugin: {plugin_key}")
            return plugin

        except Exception as e:
            print(f"Failed to load plugin '{plugin_key}': {e}")
            raise

    def get_plugin(self, plugin_key):
        """Get a loaded plugin or load it if not already loaded."""
        if plugin_key not in self.plugins:
            return self.load_plugin(plugin_key)
        return self.plugins[plugin_key]

    def list_plugins(self):
        """List all available plugins."""
        return list(self.plugin_registry.keys())

    def list_loaded_plugins(self):
        """List all currently loaded plugins."""
        return list(self.plugins.keys())

    def execute_plugin(self, plugin_key, *args, **kwargs):
        """Load and execute a plugin."""
        plugin = self.get_plugin(plugin_key)
        if plugin:
            return plugin.execute(*args, **kwargs)
        return None
