"""
Data analyzer in submodule X.
"""

from ..utilities import validate_input
from statistics import mean, median


class DataAnalyzer:
    """Analyze data and provide statistics."""

    def __init__(self):
        self.data_points = []

    def add_data(self, data):
        """Add data point for analysis."""
        if validate_input(data):
            if isinstance(data, (int, float)):
                self.data_points.append(data)
            elif isinstance(data, list):
                self.data_points.extend([x for x in data if isinstance(x, (int, float))])

    def analyze(self):
        """Analyze collected data."""
        if not self.data_points:
            return None

        return {
            "count": len(self.data_points),
            "mean": mean(self.data_points),
            "median": median(self.data_points),
            "min": min(self.data_points),
            "max": max(self.data_points)
        }

    def clear(self):
        """Clear all data points."""
        self.data_points = []
