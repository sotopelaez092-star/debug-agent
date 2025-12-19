"""
Main application demonstrating cache key mismatch issue.
Cache warmer uses v2 keys, but user/session cache use v1 keys.
"""
from cache_backend import CacheBackend
from cache_warmer import CacheWarmer
from user_cache import UserCache
from session_cache import SessionCache


def main():
    """Main application entry point."""
    print("=== Cache Key Migration Demo ===\n")

    # Initialize cache backend
    cache = CacheBackend()

    # Warm cache with data (uses NEW v2 key format)
    print("--- Warming Cache ---")
    warmer = CacheWarmer(cache)
    warmer.warm_user_data('user_123')
    warmer.warm_session_data('session_abc')

    stats = warmer.get_cache_stats()
    print(f"\nCache stats: {stats['total_keys']} keys")
    for key in stats['keys']:
        print(f"  - {key}")

    # Try to retrieve data (uses OLD v1 key format)
    print("\n--- Retrieving Cached Data ---")

    user_cache = UserCache(cache)
    session_cache = SessionCache(cache)

    # This will return None because the keys don't match!
    # Cache warmer stored with key: "app:user:profile:user_123:v2"
    # But user_cache looks for key: "user_profile_user_123"
    profile = user_cache.get_user_profile('user_123')
    print(f"User profile: {profile}")  # Will be None!

    settings = user_cache.get_user_settings('user_123')
    print(f"User settings: {settings}")  # Will be None!

    session = session_cache.get_session('session_abc')
    print(f"Session data: {session}")  # Will be None!

    # This demonstrates the mismatch
    if profile is None:
        print("\n!!! ERROR: Cache miss! !!!")
        print("Cache was warmed but retrieval failed due to key format mismatch")
        print("\nExpected behavior: Should have found cached data")
        print("Actual behavior: Got None (cache miss)")

    # Try to get cache statistics
    print("\n--- Getting Cache Statistics ---")

    # The application code expects to get metadata for cached keys
    # But it's using the OLD v1 key format
    # This will raise KeyError because the metadata is stored with v2 keys

    expected_key = "user_profile_user_123"  # OLD v1 format
    print(f"Attempting to get metadata for key: '{expected_key}'")

    # This will raise KeyError: the metadata exists for "app:user:profile:user_123:v2"
    # but not for "user_profile_user_123"
    metadata = cache.get_key_metadata(expected_key)
    print(f"Metadata: {metadata}")

    print("\n=== Demo Complete ===")


if __name__ == "__main__":
    main()
