"""
Data transformation plugin.
"""

from .base_plugin import BasePlugin


class DataTransformerPlugin(BasePlugin):
    """Plugin for transforming data between formats."""

    def __init__(self):
        super().__init__("DataTransformer")
        self.transformations = []

    def initialize(self):
        """Initialize the transformer."""
        print(f"Initializing {self.name} plugin")
        self.transformations = []

    def execute(self, data, transformation_type):
        """Transform data based on type."""
        if not self.enabled:
            print(f"Plugin {self.name} is disabled")
            return None

        self.transformations.append(transformation_type)

        if transformation_type == "to_json":
            return self._to_json(data)
        elif transformation_type == "to_csv":
            return self._to_csv(data)
        elif transformation_type == "flatten":
            return self._flatten(data)
        else:
            return data

    def _to_json(self, data):
        """Convert data to JSON format."""
        import json
        return json.dumps(data)

    def _to_csv(self, data):
        """Convert data to CSV format."""
        if isinstance(data, list) and data and isinstance(data[0], dict):
            headers = list(data[0].keys())
            rows = [','.join(headers)]
            for item in data:
                row = ','.join(str(item.get(h, '')) for h in headers)
                rows.append(row)
            return '\n'.join(rows)
        return str(data)

    def _flatten(self, data, parent_key='', sep='_'):
        """Flatten nested dictionary."""
        items = []
        if isinstance(data, dict):
            for k, v in data.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v, dict):
                    items.extend(self._flatten(v, new_key, sep=sep).items())
                else:
                    items.append((new_key, v))
            return dict(items)
        return data
