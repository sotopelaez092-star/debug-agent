"""Event bus for publishing and subscribing to events."""
from typing import Any, Dict, List
from registry.plugin_registry import PluginRegistry


class EventBus:
    """Event bus for pub/sub pattern."""

    def __init__(self):
        self._registry = PluginRegistry()
        self._registry.initialize()
        self._event_history: List[Dict[str, Any]] = []

    def publish(self, event_type: str, event_data: Any) -> None:
        """Publish an event to all registered handlers."""
        # Store in history
        self._event_history.append({
            'type': event_type,
            'data': event_data
        })

        # Execute handlers
        results = self._registry.execute_handlers(event_type, event_data)
        print(f"Published {event_type}: {len(results)} handlers executed")

    def subscribe(self, event_type: str, handler) -> None:
        """Subscribe a handler to an event type."""
        self._registry.register_handler(event_type, handler)

    def unsubscribe(self, event_type: str, handler) -> None:
        """Unsubscribe a handler from an event type."""
        self._registry.unregister_handler(event_type, handler)

    def get_event_history(self) -> List[Dict[str, Any]]:
        """Get event publication history."""
        return self._event_history.copy()

    def clear_history(self) -> None:
        """Clear event history."""
        self._event_history.clear()

    def get_subscriber_count(self, event_type: str) -> int:
        """Get number of subscribers for an event type."""
        return self._registry.get_handler_count(event_type)
