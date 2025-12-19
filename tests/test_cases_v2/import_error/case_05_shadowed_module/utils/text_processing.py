"""
Text processing utilities.
"""

import re


def clean_text(text):
    """Clean text by removing extra whitespace and special characters."""
    # Remove special characters except spaces
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    # Remove extra whitespace
    text = ' '.join(text.split())
    return text


def tokenize(text):
    """Split text into tokens."""
    cleaned = clean_text(text)
    return cleaned.lower().split()


def capitalize_words(text):
    """Capitalize each word in text."""
    return ' '.join(word.capitalize() for word in text.split())


def count_words(text):
    """Count words in text."""
    tokens = tokenize(text)
    return len(tokens)


def extract_numbers(text):
    """Extract all numbers from text."""
    return re.findall(r'\d+', text)
