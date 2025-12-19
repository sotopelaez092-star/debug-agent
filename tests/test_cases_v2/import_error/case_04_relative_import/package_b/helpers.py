"""
Helper functions for package B.
"""

import json
from datetime import datetime


def format_output(data, format_type="json"):
    """Format output in specified format."""
    if format_type == "json":
        return json.dumps(data, indent=2)
    elif format_type == "text":
        return str(data)
    elif format_type == "pretty":
        return f"Data: {data}\nTimestamp: {datetime.now().isoformat()}"
    return data


def log_message(message, level="INFO"):
    """Log a message with timestamp."""
    timestamp = datetime.now().isoformat()
    print(f"[{timestamp}] {level}: {message}")


def merge_results(*results):
    """Merge multiple result dictionaries."""
    merged = {}
    for result in results:
        if isinstance(result, dict):
            merged.update(result)
    return merged
