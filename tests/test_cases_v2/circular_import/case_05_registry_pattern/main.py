"""Test registry pattern circular import: Registry -> Handlers -> Events -> Registry."""
from datetime import datetime
from registry import EventBus


def main():
    # Initialize event bus (which initializes registry with handlers)
    event_bus = EventBus()

    # Publish user events
    user_created_data = {
        'user_id': 'u1',
        'username': 'alice',
        'email': 'alice@example.com',
        'timestamp': datetime.now().isoformat()
    }
    event_bus.publish('user.created', user_created_data)

    user_updated_data = {
        'user_id': 'u1',
        'changes': {'email': 'newalice@example.com'},
        'timestamp': datetime.now().isoformat()
    }
    event_bus.publish('user.updated', user_updated_data)

    # Publish order events
    order_created_data = {
        'order_id': 'o1',
        'user_id': 'u1',
        'items': [
            {'product_id': 'p1', 'quantity': 2, 'price': 99.99},
            {'product_id': 'p2', 'quantity': 1, 'price': 49.99}
        ],
        'total': 249.97,
        'timestamp': datetime.now().isoformat()
    }
    event_bus.publish('order.created', order_created_data)

    order_confirmed_data = {
        'order_id': 'o1',
        'confirmation_number': 'CONF123456',
        'timestamp': datetime.now().isoformat()
    }
    event_bus.publish('order.confirmed', order_confirmed_data)

    # Check subscriber counts
    user_created_count = event_bus.get_subscriber_count('user.created')
    print(f"Subscribers to 'user.created': {user_created_count}")

    order_created_count = event_bus.get_subscriber_count('order.created')
    print(f"Subscribers to 'order.created': {order_created_count}")

    # Get event history
    history = event_bus.get_event_history()
    print(f"\nTotal events published: {len(history)}")
    for event in history:
        print(f"  - {event['type']}")

    # Test cancellation
    order_cancelled_data = {
        'order_id': 'o2',
        'reason': 'Out of stock',
        'timestamp': datetime.now().isoformat()
    }
    event_bus.publish('order.cancelled', order_cancelled_data)

    print(f"\nFinal event count: {len(event_bus.get_event_history())}")


if __name__ == "__main__":
    main()
