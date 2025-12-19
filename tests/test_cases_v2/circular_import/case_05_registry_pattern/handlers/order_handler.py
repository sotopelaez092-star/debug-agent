"""Handler for order events."""
from typing import Any, Dict
from events import OrderCreatedEvent, OrderConfirmedEvent, OrderCancelledEvent, NotificationEvent


class OrderHandler:
    """Handles order-related events."""

    def __init__(self):
        self._processed_events = []

    def on_order_created(self, event_data: Any) -> Dict[str, Any]:
        """Handle order created event."""
        event = OrderCreatedEvent(event_data)
        self._processed_events.append(event)

        result = {
            'status': 'success',
            'handler': 'OrderHandler.on_order_created',
            'order_id': event.order_id,
            'total': event.total,
            'message': f"Order {event.order_id} created for ${event.total}"
        }

        # Trigger notification
        notification = NotificationEvent({
            'type': 'order_created',
            'order_id': event.order_id,
            'user_id': event.user_id,
            'message': f"Order {event.order_id} received"
        })
        notification.dispatch()

        return result

    def on_order_confirmed(self, event_data: Any) -> Dict[str, Any]:
        """Handle order confirmed event."""
        event = OrderConfirmedEvent(event_data)
        self._processed_events.append(event)

        result = {
            'status': 'success',
            'handler': 'OrderHandler.on_order_confirmed',
            'order_id': event.order_id,
            'message': f"Order {event.order_id} confirmed"
        }

        # Trigger notification
        notification = NotificationEvent({
            'type': 'order_confirmed',
            'order_id': event.order_id,
            'message': f"Your order has been confirmed"
        })
        notification.dispatch()

        return result

    def on_order_cancelled(self, event_data: Any) -> Dict[str, Any]:
        """Handle order cancelled event."""
        event = OrderCancelledEvent(event_data)
        self._processed_events.append(event)

        result = {
            'status': 'success',
            'handler': 'OrderHandler.on_order_cancelled',
            'order_id': event.order_id,
            'reason': event.reason,
            'message': f"Order {event.order_id} cancelled"
        }

        return result

    def get_processed_count(self) -> int:
        """Get number of processed events."""
        return len(self._processed_events)
