from typing import Dict, Any, Optional
from models import ConfigModel


class ConfigLoader:
    """Loader for configuration models."""

    def load(self, name: str, data: Dict[str, Any]) -> ConfigModel:
        """Load a configuration from dictionary data."""
        values = data.get("values", {})
        nested = data.get("nested", {})

        config = ConfigModel(name, **values)

        for nested_name, nested_data in nested.items():
            nested_config = self.load(nested_name, nested_data)
            config.add_nested_config(nested_name, nested_config)

        return config

    def dump(self, config: ConfigModel) -> Dict[str, Any]:
        """Dump a configuration to dictionary."""
        return config.get_full_config()
