"""User event definitions."""
from typing import Any, Dict
# CIRCULAR IMPORT: Events need registry/EventBus to dispatch themselves
from registry import EventBus


class UserCreatedEvent:
    """Event fired when a user is created."""

    def __init__(self, data: Dict[str, Any]):
        self.user_id = data.get('user_id')
        self.username = data.get('username')
        self.email = data.get('email')
        self.timestamp = data.get('timestamp')

    def dispatch(self) -> None:
        """Dispatch this event to the event bus."""
        bus = EventBus()
        bus.publish('user.created', {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'timestamp': self.timestamp
        })

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'timestamp': self.timestamp
        }


class UserUpdatedEvent:
    """Event fired when a user is updated."""

    def __init__(self, data: Dict[str, Any]):
        self.user_id = data.get('user_id')
        self.changes = data.get('changes', {})
        self.timestamp = data.get('timestamp')

    def dispatch(self) -> None:
        """Dispatch this event to the event bus."""
        bus = EventBus()
        bus.publish('user.updated', {
            'user_id': self.user_id,
            'changes': self.changes,
            'timestamp': self.timestamp
        })

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            'user_id': self.user_id,
            'changes': self.changes,
            'timestamp': self.timestamp
        }


class UserDeletedEvent:
    """Event fired when a user is deleted."""

    def __init__(self, data: Dict[str, Any]):
        self.user_id = data.get('user_id')
        self.timestamp = data.get('timestamp')

    def dispatch(self) -> None:
        """Dispatch this event to the event bus."""
        bus = EventBus()
        bus.publish('user.deleted', {
            'user_id': self.user_id,
            'timestamp': self.timestamp
        })

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            'user_id': self.user_id,
            'timestamp': self.timestamp
        }
