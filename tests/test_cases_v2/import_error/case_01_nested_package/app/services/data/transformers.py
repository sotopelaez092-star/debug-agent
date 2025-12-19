"""
Data transformation utilities.
"""

from typing import List, Dict, Any


class DataTransformer:
    """Transforms data between different formats."""

    def __init__(self):
        self.transformations = []

    def normalize_data(self, data):
        """Normalize data to standard format."""
        if isinstance(data, dict):
            return {k.lower(): v for k, v in data.items()}
        return data

    def flatten_dict(self, d, parent_key='', sep='_'):
        """Flatten a nested dictionary."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self.flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def convert_to_csv_format(self, records):
        """Convert records to CSV-compatible format."""
        if not records:
            return []

        headers = list(records[0].keys())
        rows = [[str(record.get(h, '')) for h in headers] for record in records]
        return [headers] + rows
