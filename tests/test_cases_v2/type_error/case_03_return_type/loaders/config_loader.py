"""Configuration file loader with metadata tracking."""
import json
import os
from datetime import datetime


class ConfigMetadata:
    """Metadata about loaded configuration."""

    def __init__(self, source, loaded_at, version=None, checksum=None):
        self.source = source
        self.loaded_at = loaded_at
        self.version = version
        self.checksum = checksum

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "source": self.source,
            "loaded_at": self.loaded_at.isoformat(),
            "version": self.version,
            "checksum": self.checksum,
        }

    def __repr__(self):
        return f"ConfigMetadata(source={self.source}, version={self.version})"


def load_json_config(filepath):
    """
    Load JSON configuration file with metadata.

    Args:
        filepath: Path to JSON configuration file

    Returns:
        tuple: (config_dict, metadata) - Configuration dictionary and metadata object

    Note:
        This function was refactored to return both config and metadata for
        better auditability and debugging support.
        Old signature: Returns dict
        New signature: Returns tuple of (dict, ConfigMetadata)
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Config file not found: {filepath}")

    with open(filepath, 'r') as f:
        config_data = json.load(f)

    # Extract version if present in config
    version = config_data.get("_version", "1.0.0")

    # Create metadata
    metadata = ConfigMetadata(
        source=filepath,
        loaded_at=datetime.now(),
        version=version,
        checksum=None,  # Could calculate file hash here
    )

    # Remove internal fields from config
    clean_config = {k: v for k, v in config_data.items() if not k.startswith('_')}

    return clean_config, metadata


def load_env_config():
    """
    Load configuration from environment variables.

    Returns:
        tuple: (config_dict, metadata) - Configuration from env vars and metadata
    """
    config = {
        "database_url": os.getenv("DATABASE_URL", "sqlite:///db.sqlite"),
        "api_key": os.getenv("API_KEY", ""),
        "debug": os.getenv("DEBUG", "false").lower() == "true",
        "port": int(os.getenv("PORT", "8000")),
    }

    metadata = ConfigMetadata(
        source="environment",
        loaded_at=datetime.now(),
        version=None,
    )

    return config, metadata


def merge_configs(*configs):
    """
    Merge multiple configuration dictionaries.

    Args:
        *configs: Variable number of config dicts to merge (later ones override earlier)

    Returns:
        dict: Merged configuration dictionary
    """
    result = {}
    for config in configs:
        if isinstance(config, tuple):
            # Handle case where tuple (config, metadata) is passed
            config = config[0]
        result.update(config)
    return result


def validate_config(config, required_keys):
    """
    Validate that configuration has required keys.

    Args:
        config: Configuration dictionary (or tuple of (config, metadata))
        required_keys: List of required key names

    Returns:
        bool: True if valid, False otherwise

    Raises:
        ValueError: If required keys are missing
    """
    # Handle both old and new return types
    if isinstance(config, tuple):
        config = config[0]

    missing_keys = [key for key in required_keys if key not in config]

    if missing_keys:
        raise ValueError(f"Missing required config keys: {missing_keys}")

    return True
