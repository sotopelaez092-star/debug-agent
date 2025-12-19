"""
Configuration schema definitions for application settings.
This module defines the structure of configuration files.
"""

# Legacy v1 schema (deprecated)
LEGACY_CONFIG_SCHEMA = {
    "database": {
        "host": str,
        "port": int,
        "credentials": {
            "username": str,
            "password": str
        }
    },
    "cache": {
        "redis_host": str,
        "redis_port": int,
        "ttl": int
    }
}

# New v2 schema
CONFIG_SCHEMA_V2 = {
    "database": {
        "connection": {
            "host": str,
            "port": int,
            "timeout": int
        },
        "auth": {
            "user": str,  # changed from 'username'
            "password": str
        }
    },
    "cache": {
        "backend": {
            "type": str,
            "host": str,
            "port": int
        },
        "settings": {
            "ttl": int,
            "max_size": int
        }
    }
}


def validate_config_schema(config: dict, schema: dict) -> bool:
    """Validate configuration against schema."""
    # Simple validation logic
    for key in schema:
        if key not in config:
            return False
        if isinstance(schema[key], dict):
            if not validate_config_schema(config[key], schema[key]):
                return False
    return True
