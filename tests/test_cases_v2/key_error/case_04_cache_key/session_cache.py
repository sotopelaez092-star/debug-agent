"""
Session data caching layer.
Also uses the OLD v1 cache key format.
"""
from typing import Optional, Dict, Any
from cache_backend import CacheBackend


class SessionCache:
    """Manages caching of session data."""

    def __init__(self, cache: CacheBackend):
        self.cache = cache

    def cache_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """Cache session data using OLD v1 key format."""
        # OLD v1 format: session_{session_id}
        cache_key = f"session_{session_id}"
        return self.cache.set(cache_key, session_data, ttl=1800)

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get cached session data using OLD v1 key format."""
        # OLD v1 format: session_{session_id}
        cache_key = f"session_{session_id}"
        return self.cache.get(cache_key)

    def delete_session(self, session_id: str) -> bool:
        """Delete session from cache."""
        cache_key = f"session_{session_id}"
        return self.cache.delete(cache_key)

    def session_exists(self, session_id: str) -> bool:
        """Check if session exists in cache."""
        cache_key = f"session_{session_id}"
        return self.cache.exists(cache_key)
