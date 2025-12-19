"""
Data processor in submodule X.
"""

# Relative import from parent package
from ..utilities import validate_input, serialize_data
from ..constants import MAX_RETRIES


class DataProcessor:
    """Process data with validation and serialization."""

    def __init__(self):
        self.processed_items = []
        self.max_retries = MAX_RETRIES

    def process(self, data):
        """Process data with validation."""
        if not validate_input(data):
            raise ValueError("Invalid input data")

        # Process the data
        processed = self._transform(data)
        self.processed_items.append(processed)

        return processed

    def _transform(self, data):
        """Transform data to standardized format."""
        if isinstance(data, dict):
            return {k.upper(): v for k, v in data.items()}
        return data

    def export(self):
        """Export processed items as JSON."""
        return serialize_data(self.processed_items)

    def get_stats(self):
        """Get processing statistics."""
        return {
            "total_processed": len(self.processed_items),
            "max_retries": self.max_retries
        }
