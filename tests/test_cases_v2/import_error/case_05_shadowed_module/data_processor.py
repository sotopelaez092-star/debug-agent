"""
Data processor for handling datasets.
"""

import random
from utils import tokenize


class DataProcessor:
    """Process and sample data."""

    def __init__(self):
        self.data = []

    def add_data(self, items):
        """Add data items."""
        if isinstance(items, list):
            self.data.extend(items)
        else:
            self.data.append(items)

    def sample_data(self, n=5):
        """Get random sample of data."""
        if n > len(self.data):
            n = len(self.data)

        # Use random.sample - THIS WILL FAIL!
        # The local random.py doesn't have sample() function
        return random.sample(self.data, n)

    def process_text_data(self, text):
        """Process text data."""
        tokens = tokenize(text)
        return {
            "token_count": len(tokens),
            "tokens": tokens,
            "sample": self.sample_data(3) if self.data else []
        }
