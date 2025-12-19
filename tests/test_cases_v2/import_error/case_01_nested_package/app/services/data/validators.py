"""
Data validation utilities.
"""

import re
from typing import Any, Dict


class DataValidator:
    """Validates data against various rules."""

    @staticmethod
    def validate_email(email):
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    @staticmethod
    def validate_phone(phone):
        """Validate phone number format."""
        pattern = r'^\+?1?\d{9,15}$'
        return re.match(pattern, phone.replace('-', '').replace(' ', '')) is not None

    @staticmethod
    def validate_json(data):
        """Validate if string is valid JSON."""
        try:
            import json
            json.loads(data) if isinstance(data, str) else data
            return True
        except (ValueError, TypeError):
            return False

    def validate_record(self, record, schema):
        """Validate a record against a schema."""
        for field, rules in schema.items():
            if field not in record and rules.get('required'):
                return False
        return True
