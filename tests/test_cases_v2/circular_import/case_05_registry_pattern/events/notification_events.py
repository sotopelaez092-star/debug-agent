"""Notification event definitions."""
from typing import Any, Dict
from registry import EventBus


class NotificationEvent:
    """Event for sending notifications."""

    def __init__(self, data: Dict[str, Any]):
        self.notification_type = data.get('type', 'generic')
        self.message = data.get('message', '')
        self.user_id = data.get('user_id')
        self.metadata = data.get('metadata', {})

    def dispatch(self) -> None:
        """Dispatch this event to the event bus."""
        bus = EventBus()
        bus.publish('notification.send', {
            'type': self.notification_type,
            'message': self.message,
            'user_id': self.user_id,
            'metadata': self.metadata
        })

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            'type': self.notification_type,
            'message': self.message,
            'user_id': self.user_id,
            'metadata': self.metadata
        }
