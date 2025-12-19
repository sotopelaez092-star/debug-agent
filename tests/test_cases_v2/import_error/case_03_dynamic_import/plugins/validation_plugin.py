"""
Validation plugin.
"""

from .base_plugin import BasePlugin
import re


class ValidationPlugin(BasePlugin):
    """Plugin for validating data."""

    def __init__(self):
        super().__init__("Validator")
        self.validation_rules = {}

    def initialize(self):
        """Initialize the validator with default rules."""
        print(f"Initializing {self.name} plugin")
        self.validation_rules = {
            "email": r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            "phone": r'^\+?1?\d{9,15}$',
            "url": r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        }

    def execute(self, data, rule_type):
        """Validate data against a rule."""
        if not self.enabled:
            print(f"Plugin {self.name} is disabled")
            return False

        if rule_type not in self.validation_rules:
            print(f"Unknown validation rule: {rule_type}")
            return False

        pattern = self.validation_rules[rule_type]
        return bool(re.match(pattern, str(data)))

    def add_rule(self, name, pattern):
        """Add a custom validation rule."""
        self.validation_rules[name] = pattern
        print(f"Added validation rule: {name}")

    def validate_multiple(self, data_dict):
        """Validate multiple fields."""
        results = {}
        for field, (value, rule_type) in data_dict.items():
            results[field] = self.execute(value, rule_type)
        return results
