"""
Data processing plugin.
"""

from .base_plugin import BasePlugin


class DataProcessorPlugin(BasePlugin):
    """Plugin for processing data."""

    def __init__(self):
        super().__init__("DataProcessor")
        self.processed_count = 0

    def initialize(self):
        """Initialize the data processor."""
        print(f"Initializing {self.name} plugin")
        self.processed_count = 0

    def execute(self, data):
        """Process the provided data."""
        if not self.enabled:
            print(f"Plugin {self.name} is disabled")
            return None

        processed = self._process_data(data)
        self.processed_count += 1
        return processed

    def _process_data(self, data):
        """Internal data processing logic."""
        if isinstance(data, str):
            return data.upper()
        elif isinstance(data, list):
            return [str(item).upper() for item in data]
        elif isinstance(data, dict):
            return {k: str(v).upper() for k, v in data.items()}
        return str(data).upper()

    def get_stats(self):
        """Get processing statistics."""
        return {
            "processed_count": self.processed_count,
            "status": "active" if self.enabled else "inactive"
        }
