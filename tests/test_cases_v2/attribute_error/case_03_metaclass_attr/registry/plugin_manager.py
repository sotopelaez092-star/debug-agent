from typing import Dict, List, Any, Type
from core import PluginMeta, BasePlugin


class PluginManager:
    """Manager for loading and executing plugins."""

    def __init__(self):
        self._loaded: Dict[str, BasePlugin] = {}
        self._execution_order: List[str] = []

    def load_plugin(self, name: str, config: Dict[str, Any] = None) -> BasePlugin:
        """Load a plugin by name."""
        plugin_class = PluginMeta.get_plugin(name)
        instance = plugin_class(config or {})
        instance.initialize()
        self._loaded[name] = instance
        return instance

    def load_with_dependencies(self, name: str, config: Dict[str, Any] = None) -> BasePlugin:
        """Load a plugin and all its dependencies."""
        # Get plugin metadata
        # BUG: Typo - should be get_plugin_metadata not get_plugin_metdata
        metadata = PluginMeta.get_plugin_metdata(name)

        # Load dependencies first
        for dep in metadata.get("dependencies", []):
            if dep not in self._loaded:
                self.load_with_dependencies(dep)

        # Load the plugin itself
        if name not in self._loaded:
            return self.load_plugin(name, config)
        return self._loaded[name]

    def get_plugin(self, name: str) -> BasePlugin:
        """Get a loaded plugin instance."""
        if name not in self._loaded:
            raise KeyError(f"Plugin not loaded: {name}")
        return self._loaded[name]

    def execute_pipeline(self, plugins: List[str], data: Any) -> Any:
        """Execute a pipeline of plugins."""
        result = data
        for name in plugins:
            plugin = self.get_plugin(name)
            result = plugin.execute(result)
        return result

    def shutdown_all(self) -> None:
        """Shutdown all loaded plugins."""
        for plugin in self._loaded.values():
            plugin.shutdown()
        self._loaded.clear()
