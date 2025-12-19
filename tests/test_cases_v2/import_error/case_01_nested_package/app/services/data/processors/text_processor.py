"""
Text data processing utilities.
"""

import re
from collections import Counter


class TextProcessor:
    """Processes and analyzes text data."""

    def __init__(self):
        self.stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at'}

    def clean_text(self, text):
        """Remove special characters and normalize text."""
        text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
        return ' '.join(text.split())

    def tokenize(self, text):
        """Split text into tokens."""
        return self.clean_text(text).lower().split()

    def remove_stop_words(self, tokens):
        """Remove common stop words from tokens."""
        return [t for t in tokens if t not in self.stop_words]

    def word_frequency(self, text):
        """Calculate word frequency in text."""
        tokens = self.remove_stop_words(self.tokenize(text))
        return Counter(tokens)

    def extract_keywords(self, text, top_n=10):
        """Extract top N keywords from text."""
        freq = self.word_frequency(text)
        return freq.most_common(top_n)
