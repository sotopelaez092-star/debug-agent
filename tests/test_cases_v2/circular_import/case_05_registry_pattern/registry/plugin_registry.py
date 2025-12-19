"""Plugin registry for managing handlers."""
from typing import Dict, List, Callable, Any
# CIRCULAR IMPORT: Registry needs handlers to register them
from handlers import UserHandler, OrderHandler, NotificationHandler


class PluginRegistry:
    """Central registry for managing plugin handlers."""

    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
        self._initialized = False

    def initialize(self) -> None:
        """Initialize registry with default handlers."""
        if self._initialized:
            return

        # Register default handlers
        user_handler = UserHandler()
        order_handler = OrderHandler()
        notification_handler = NotificationHandler()

        self.register_handler('user.created', user_handler.on_user_created)
        self.register_handler('user.updated', user_handler.on_user_updated)
        self.register_handler('user.deleted', user_handler.on_user_deleted)

        self.register_handler('order.created', order_handler.on_order_created)
        self.register_handler('order.confirmed', order_handler.on_order_confirmed)
        self.register_handler('order.cancelled', order_handler.on_order_cancelled)

        self.register_handler('notification.send', notification_handler.on_send_notification)
        self.register_handler('user.created', notification_handler.on_user_event)
        self.register_handler('order.created', notification_handler.on_order_event)

        self._initialized = True

    def register_handler(self, event_type: str, handler: Callable) -> None:
        """Register a handler for an event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def unregister_handler(self, event_type: str, handler: Callable) -> None:
        """Unregister a handler for an event type."""
        if event_type in self._handlers:
            self._handlers[event_type].remove(handler)

    def get_handlers(self, event_type: str) -> List[Callable]:
        """Get all handlers for an event type."""
        return self._handlers.get(event_type, [])

    def execute_handlers(self, event_type: str, event_data: Any) -> List[Any]:
        """Execute all handlers for an event type."""
        handlers = self.get_handlers(event_type)
        results = []
        for handler in handlers:
            result = handler(event_data)
            results.append(result)
        return results

    def list_event_types(self) -> List[str]:
        """List all registered event types."""
        return list(self._handlers.keys())

    def get_handler_count(self, event_type: str) -> int:
        """Get number of handlers for an event type."""
        return len(self._handlers.get(event_type, []))
