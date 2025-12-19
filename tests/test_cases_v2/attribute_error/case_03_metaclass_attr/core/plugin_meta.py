from typing import Dict, Type, Any


class PluginMeta(type):
    """Metaclass that auto-registers plugins and adds metadata."""

    _registry: Dict[str, Type] = {}

    def __new__(mcs, name: str, bases: tuple, namespace: dict):
        cls = super().__new__(mcs, name, bases, namespace)

        # Skip base class registration
        if name != "BasePlugin":
            # Auto-register plugin
            plugin_name = namespace.get("plugin_name", name.lower())
            mcs._registry[plugin_name] = cls

            # Add metadata
            cls._meta = {
                "name": plugin_name,
                "version": namespace.get("version", "1.0.0"),
                "author": namespace.get("author", "unknown"),
                "dependencies": namespace.get("dependencies", []),
            }

        return cls

    @classmethod
    def get_plugin(mcs, name: str) -> Type:
        """Get a registered plugin by name."""
        if name not in mcs._registry:
            raise KeyError(f"Plugin not found: {name}")
        return mcs._registry[name]

    @classmethod
    def list_plugins(mcs) -> Dict[str, Type]:
        """List all registered plugins."""
        return mcs._registry.copy()

    @classmethod
    def get_plugin_metadata(mcs, name: str) -> dict:
        """Get metadata for a plugin."""
        plugin = mcs.get_plugin(name)
        return plugin._meta
