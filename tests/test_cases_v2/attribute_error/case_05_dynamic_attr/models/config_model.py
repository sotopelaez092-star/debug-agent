from typing import Any, Dict, Optional
from .dynamic_model import DynamicModel


class ConfigModel(DynamicModel):
    """Configuration model with nested config support."""

    def __init__(self, config_name: str, **kwargs):
        super().__init__(**kwargs)
        self._config_name = config_name
        self._nested_configs: Dict[str, 'ConfigModel'] = {}

    def add_nested_config(self, name: str, config: 'ConfigModel') -> None:
        """Add a nested configuration."""
        self._nested_configs[name] = config

    def get_nested_config(self, name: str) -> Optional['ConfigModel']:
        """Get a nested configuration."""
        return self._nested_configs.get(name)

    def get_full_config(self) -> Dict[str, Any]:
        """Get full configuration including nested."""
        result = {
            "name": self._config_name,
            "values": self.get_attributes(),
            "nested": {}
        }
        for name, config in self._nested_configs.items():
            result["nested"][name] = config.get_full_config()
        return result

    def merge_config(self, other: 'ConfigModel') -> None:
        """Merge another configuration into this one."""
        for key, value in other.get_attributes().items():
            setattr(self, key, value)
        for name, config in other._nested_configs.items():
            if name in self._nested_configs:
                self._nested_configs[name].merge_config(config)
            else:
                self._nested_configs[name] = config
