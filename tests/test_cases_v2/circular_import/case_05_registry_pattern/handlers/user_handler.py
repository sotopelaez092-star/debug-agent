"""Handler for user events."""
from typing import Any, Dict
# CIRCULAR IMPORT: Handlers need events to process and dispatch them
from events import UserCreatedEvent, UserUpdatedEvent, UserDeletedEvent, NotificationEvent


class UserHandler:
    """Handles user-related events."""

    def __init__(self):
        self._processed_events = []

    def on_user_created(self, event_data: Any) -> Dict[str, Any]:
        """Handle user created event."""
        event = UserCreatedEvent(event_data)
        self._processed_events.append(event)

        # Process the event
        result = {
            'status': 'success',
            'handler': 'UserHandler.on_user_created',
            'user_id': event.user_id,
            'message': f"User {event.username} created successfully"
        }

        # Trigger notification
        notification = NotificationEvent({
            'type': 'user_created',
            'user_id': event.user_id,
            'message': f"Welcome {event.username}!"
        })
        notification.dispatch()

        return result

    def on_user_updated(self, event_data: Any) -> Dict[str, Any]:
        """Handle user updated event."""
        event = UserUpdatedEvent(event_data)
        self._processed_events.append(event)

        result = {
            'status': 'success',
            'handler': 'UserHandler.on_user_updated',
            'user_id': event.user_id,
            'changes': event.changes
        }

        return result

    def on_user_deleted(self, event_data: Any) -> Dict[str, Any]:
        """Handle user deleted event."""
        event = UserDeletedEvent(event_data)
        self._processed_events.append(event)

        result = {
            'status': 'success',
            'handler': 'UserHandler.on_user_deleted',
            'user_id': event.user_id,
            'message': f"User {event.user_id} deleted"
        }

        # Trigger notification
        notification = NotificationEvent({
            'type': 'user_deleted',
            'user_id': event.user_id,
            'message': f"User account deleted"
        })
        notification.dispatch()

        return result

    def get_processed_count(self) -> int:
        """Get number of processed events."""
        return len(self._processed_events)
