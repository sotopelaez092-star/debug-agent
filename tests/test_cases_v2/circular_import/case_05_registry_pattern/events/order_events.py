"""Order event definitions."""
from typing import Any, Dict, List
from registry import EventBus


class OrderCreatedEvent:
    """Event fired when an order is created."""

    def __init__(self, data: Dict[str, Any]):
        self.order_id = data.get('order_id')
        self.user_id = data.get('user_id')
        self.items = data.get('items', [])
        self.total = data.get('total', 0.0)
        self.timestamp = data.get('timestamp')

    def dispatch(self) -> None:
        """Dispatch this event to the event bus."""
        bus = EventBus()
        bus.publish('order.created', {
            'order_id': self.order_id,
            'user_id': self.user_id,
            'items': self.items,
            'total': self.total,
            'timestamp': self.timestamp
        })

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            'order_id': self.order_id,
            'user_id': self.user_id,
            'items': self.items,
            'total': self.total,
            'timestamp': self.timestamp
        }


class OrderConfirmedEvent:
    """Event fired when an order is confirmed."""

    def __init__(self, data: Dict[str, Any]):
        self.order_id = data.get('order_id')
        self.confirmation_number = data.get('confirmation_number')
        self.timestamp = data.get('timestamp')

    def dispatch(self) -> None:
        """Dispatch this event to the event bus."""
        bus = EventBus()
        bus.publish('order.confirmed', {
            'order_id': self.order_id,
            'confirmation_number': self.confirmation_number,
            'timestamp': self.timestamp
        })

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            'order_id': self.order_id,
            'confirmation_number': self.confirmation_number,
            'timestamp': self.timestamp
        }


class OrderCancelledEvent:
    """Event fired when an order is cancelled."""

    def __init__(self, data: Dict[str, Any]):
        self.order_id = data.get('order_id')
        self.reason = data.get('reason', 'User requested')
        self.timestamp = data.get('timestamp')

    def dispatch(self) -> None:
        """Dispatch this event to the event bus."""
        bus = EventBus()
        bus.publish('order.cancelled', {
            'order_id': self.order_id,
            'reason': self.reason,
            'timestamp': self.timestamp
        })

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            'order_id': self.order_id,
            'reason': self.reason,
            'timestamp': self.timestamp
        }
