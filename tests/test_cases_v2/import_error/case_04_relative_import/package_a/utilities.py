"""
Utility functions for package A.
"""

from .constants import VERSION, DEFAULT_TIMEOUT
import json


def get_config():
    """Get current configuration."""
    return {
        "version": VERSION,
        "timeout": DEFAULT_TIMEOUT
    }


def validate_input(data):
    """Validate input data."""
    if not data:
        return False
    if isinstance(data, dict):
        return len(data) > 0
    if isinstance(data, str):
        return len(data.strip()) > 0
    return True


def serialize_data(data):
    """Serialize data to JSON string."""
    return json.dumps(data, indent=2)


def deserialize_data(json_string):
    """Deserialize JSON string to data."""
    try:
        return json.loads(json_string)
    except json.JSONDecodeError:
        return None
