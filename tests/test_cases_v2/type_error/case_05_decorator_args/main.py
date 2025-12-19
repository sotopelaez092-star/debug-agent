"""Test caching system with decorator usage."""
from services import DataService, APIService
from utils import compute_hash, fibonacci, is_prime
from decorators import cache_stats, cache_clear_all


def main():
    print("=== Caching System Test ===\n")

    # Test DataService
    # This will trigger TypeError because @cache decorator now requires ttl argument
    # but the decorated methods use old @cache syntax without arguments
    print("1. Testing DataService...")
    try:
        data_service = DataService()

        # First call - should execute and cache
        print("   Fetching user data (first call):")
        user = data_service.fetch_user_data(1)
        print(f"   Result: {user['name']}")

        # Second call - should use cache
        print("\n   Fetching same user data (second call):")
        user = data_service.fetch_user_data(1)
        print(f"   Result: {user['name']}")

        print(f"\n   Total DB calls: {data_service.get_call_count()}")

    except Exception as e:
        print(f"\n   Error: {type(e).__name__}: {e}")
        raise

    print("\n2. Testing APIService...")
    api_service = APIService()

    print("   Fetching weather data:")
    weather = api_service.fetch_weather_data("New York")
    print(f"   Result: {weather['temperature']}°C, {weather['condition']}")

    print("\n   Fetching weather data again (should be cached):")
    weather = api_service.fetch_weather_data("New York")
    print(f"   Result: {weather['temperature']}°C, {weather['condition']}")

    print(f"\n   Total API requests: {api_service.get_request_count()}")

    print("\n3. Testing utility functions...")
    print("   Computing hash:")
    hash1 = compute_hash("Hello World")
    print(f"   Hash: {hash1}")

    print("\n   Computing fibonacci(10):")
    fib = fibonacci(10)
    print(f"   Result: {fib}")

    print("\n   Checking if 17 is prime:")
    prime = is_prime(17)
    print(f"   Result: {prime}")

    print("\n4. Cache statistics:")
    stats = cache_stats()
    print(f"   Total entries: {stats['total_entries']}")
    print(f"   Active entries: {stats['active_entries']}")
    print(f"   Expired entries: {stats['expired_entries']}")

    print("\nDone!")


if __name__ == "__main__":
    main()
