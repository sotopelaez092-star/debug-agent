"""
User data caching layer.
This module still uses the OLD v1 cache key format.
"""
from typing import Optional, Dict, Any
from cache_backend import CacheBackend


class UserCache:
    """Manages caching of user-related data."""

    def __init__(self, cache: CacheBackend):
        self.cache = cache

    def cache_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> bool:
        """Cache user profile data using OLD v1 key format."""
        # OLD v1 format: user_profile_{user_id}
        cache_key = f"user_profile_{user_id}"
        return self.cache.set(cache_key, profile_data, ttl=3600)

    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached user profile using OLD v1 key format."""
        # OLD v1 format: user_profile_{user_id}
        cache_key = f"user_profile_{user_id}"
        return self.cache.get(cache_key)

    def cache_user_settings(self, user_id: str, settings: Dict[str, Any]) -> bool:
        """Cache user settings using OLD v1 key format."""
        # OLD v1 format: user_settings_{user_id}
        cache_key = f"user_settings_{user_id}"
        return self.cache.set(cache_key, settings, ttl=7200)

    def get_user_settings(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached user settings using OLD v1 key format."""
        # OLD v1 format: user_settings_{user_id}
        cache_key = f"user_settings_{user_id}"
        return self.cache.get(cache_key)

    def invalidate_user_cache(self, user_id: str) -> None:
        """Invalidate all user cache entries."""
        # Need to delete both profile and settings
        profile_key = f"user_profile_{user_id}"
        settings_key = f"user_settings_{user_id}"

        self.cache.delete(profile_key)
        self.cache.delete(settings_key)
