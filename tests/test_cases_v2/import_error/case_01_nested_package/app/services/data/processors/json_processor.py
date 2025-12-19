"""
JSON data processing utilities.
"""

import json
from typing import Any, Dict, List


class JSONProcessor:
    """Processes and manipulates JSON data."""

    def __init__(self):
        self.schema_cache = {}

    def validate_structure(self, data, required_keys):
        """Validate JSON structure has required keys."""
        if not isinstance(data, dict):
            return False
        return all(key in data for key in required_keys)

    def merge_json(self, base, updates):
        """Deep merge two JSON objects."""
        result = base.copy()
        for key, value in updates.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self.merge_json(result[key], value)
            else:
                result[key] = value
        return result

    def extract_paths(self, data, path=''):
        """Extract all paths in a nested JSON structure."""
        paths = []
        if isinstance(data, dict):
            for key, value in data.items():
                new_path = f"{path}.{key}" if path else key
                paths.append(new_path)
                paths.extend(self.extract_paths(value, new_path))
        elif isinstance(data, list):
            for i, item in enumerate(data):
                new_path = f"{path}[{i}]"
                paths.extend(self.extract_paths(item, new_path))
        return paths

    def filter_by_condition(self, data_list, condition_key, condition_value):
        """Filter list of JSON objects by condition."""
        return [item for item in data_list if item.get(condition_key) == condition_value]
