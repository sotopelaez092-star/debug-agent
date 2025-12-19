"""
File operation utilities.
"""

import os
import json


def read_file(filepath):
    """Read file contents."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    with open(filepath, 'r') as f:
        return f.read()


def write_file(filepath, content):
    """Write content to file."""
    with open(filepath, 'w') as f:
        f.write(content)
    return True


def read_json_file(filepath):
    """Read JSON file."""
    content = read_file(filepath)
    return json.loads(content)


def write_json_file(filepath, data):
    """Write data to JSON file."""
    content = json.dumps(data, indent=2)
    return write_file(filepath, content)


def list_files(directory):
    """List files in directory."""
    if not os.path.isdir(directory):
        return []
    return [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
