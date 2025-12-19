"""
Main entry point for the application.
"""

import sys
import logging
from app import Application


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def main():
    """Run the application."""
    setup_logging()

    print("=" * 60)
    print("Request Processing Application")
    print("=" * 60)

    # Create and start application
    app = Application()
    app.start()

    print("\n✓ Application started")

    # Test 1: Get status
    print("\n" + "-" * 60)
    print("Test 1: Get Status")
    print("-" * 60)

    request = {
        'request_id': 'req_001',
        'user_id': 123,
        'action': 'get_status'
    }

    response = app.handle_request(request)
    print(f"Response: {response.get('status')}")
    print(f"Uptime: {response.get('uptime', 0):.2f}s")

    # Test 2: Update configuration
    print("\n" + "-" * 60)
    print("Test 2: Update Configuration")
    print("-" * 60)

    request = {
        'request_id': 'req_002',
        'user_id': 123,
        'action': 'update_config',
        'config': {
            'max_retries': 5,
            'timeout': 60
        }
    }

    response = app.handle_request(request)
    print(f"Response: {response.get('status')}")
    print(f"New max_retries: {response.get('config', {}).get('max_retries')}")

    # Test 3: Process data (this will trigger the scope issue)
    print("\n" + "-" * 60)
    print("Test 3: Process Data with Retries")
    print("-" * 60)

    request = {
        'request_id': 'req_003',
        'user_id': 123,
        'action': 'process_data',
        'data': [1, 2, 3, 4, 5]
    }

    try:
        response = app.handle_request(request)
        print(f"Response: {response.get('status')}")

        if 'result' in response:
            print(f"Processed: {response['result'].get('processed')} items")
            print(f"Attempts: {response['result'].get('attempts')}")
        elif 'error' in response:
            print(f"Error: {response['error']}")

    except Exception as e:
        print(f"✗ Request failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Print final stats
    print("\n" + "=" * 60)
    print("Final Statistics")
    print("=" * 60)

    stats = app.get_stats()
    print(f"Total requests: {stats['state']['request_count']}")
    print(f"Total errors: {stats['state']['error_count']}")
    print(f"Uptime: {stats['uptime']:.2f}s")

    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
