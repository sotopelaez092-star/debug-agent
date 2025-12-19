"""
Analytics plugin for tracking events.
"""

from .base_plugin import BasePlugin
from datetime import datetime
from collections import defaultdict


class AnalyticsPlugin(BasePlugin):
    """Plugin for tracking and analyzing events."""

    def __init__(self):
        super().__init__("Analytics")
        self.events = []
        self.event_counts = defaultdict(int)

    def initialize(self):
        """Initialize the analytics system."""
        print(f"Initializing {self.name} plugin")
        self.events = []
        self.event_counts = defaultdict(int)

    def execute(self, event_name, event_data=None):
        """Track an event."""
        if not self.enabled:
            return

        event = {
            "name": event_name,
            "data": event_data,
            "timestamp": datetime.now().isoformat()
        }
        self.events.append(event)
        self.event_counts[event_name] += 1

    def get_event_summary(self):
        """Get summary of tracked events."""
        return {
            "total_events": len(self.events),
            "event_types": dict(self.event_counts),
            "recent_events": self.events[-10:]
        }

    def clear_events(self):
        """Clear all tracked events."""
        self.events = []
        self.event_counts = defaultdict(int)
        print("Analytics data cleared")
