"""Handler for notification events."""
from typing import Any, Dict, List


class NotificationHandler:
    """Handles notification events."""

    def __init__(self):
        self._notifications: List[Dict[str, Any]] = []

    def on_send_notification(self, event_data: Any) -> Dict[str, Any]:
        """Handle send notification event."""
        notification = {
            'type': event_data.get('type', 'generic'),
            'message': event_data.get('message', ''),
            'recipient': event_data.get('user_id', 'system')
        }
        self._notifications.append(notification)

        result = {
            'status': 'sent',
            'handler': 'NotificationHandler.on_send_notification',
            'notification_type': notification['type'],
            'message': f"Notification sent: {notification['message']}"
        }

        return result

    def on_user_event(self, event_data: Any) -> Dict[str, Any]:
        """Handle generic user event for notifications."""
        message = f"User event processed: {event_data}"
        self._notifications.append({
            'type': 'user_event',
            'message': message,
            'data': event_data
        })

        return {
            'status': 'logged',
            'handler': 'NotificationHandler.on_user_event'
        }

    def on_order_event(self, event_data: Any) -> Dict[str, Any]:
        """Handle generic order event for notifications."""
        message = f"Order event processed: {event_data}"
        self._notifications.append({
            'type': 'order_event',
            'message': message,
            'data': event_data
        })

        return {
            'status': 'logged',
            'handler': 'NotificationHandler.on_order_event'
        }

    def get_notifications(self) -> List[Dict[str, Any]]:
        """Get all notifications."""
        return self._notifications.copy()

    def get_notification_count(self) -> int:
        """Get total notification count."""
        return len(self._notifications)
