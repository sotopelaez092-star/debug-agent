"""
Cache warming utility.
Pre-populates cache with commonly accessed data using NEW v2 key format.
"""
from cache_backend import CacheBackend
from cache_keys import CacheKeyGenerator


class CacheWarmer:
    """Warms up cache with frequently accessed data."""

    def __init__(self, cache: CacheBackend):
        self.cache = cache
        self.key_gen = CacheKeyGenerator()

    def warm_user_data(self, user_id: str) -> None:
        """Warm cache with user data using NEW v2 keys."""
        # Sample user profile data
        profile_data = {
            'id': user_id,
            'name': 'John Doe',
            'email': 'john@example.com',
            'created_at': '2024-01-01'
        }

        # Sample user settings
        settings_data = {
            'theme': 'dark',
            'language': 'en',
            'notifications': True
        }

        # Use NEW v2 key format
        profile_key = self.key_gen.user_profile_key(user_id)
        settings_key = self.key_gen.user_settings_key(user_id)

        self.cache.set(profile_key, profile_data, ttl=3600)
        self.cache.set(settings_key, settings_data, ttl=7200)

        print(f"Warmed cache for user {user_id}")
        print(f"  Profile key: {profile_key}")
        print(f"  Settings key: {settings_key}")

    def warm_session_data(self, session_id: str) -> None:
        """Warm cache with session data using NEW v2 keys."""
        session_data = {
            'session_id': session_id,
            'user_id': 'user_123',
            'created_at': '2024-01-15T10:00:00Z',
            'last_activity': '2024-01-15T10:30:00Z'
        }

        # Use NEW v2 key format
        session_key = self.key_gen.session_key(session_id)
        self.cache.set(session_key, session_data, ttl=1800)

        print(f"Warmed session cache: {session_key}")

    def get_cache_stats(self) -> dict:
        """Get cache statistics."""
        all_keys = self.cache.keys()
        return {
            'total_keys': len(all_keys),
            'keys': all_keys
        }
