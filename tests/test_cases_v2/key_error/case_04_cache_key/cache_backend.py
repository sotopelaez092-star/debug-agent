"""
Cache backend implementation.
Simulates a Redis-like cache with dictionary storage.
"""
from typing import Any, Optional, Dict
import json
import time


class CacheBackend:
    """In-memory cache backend with TTL support."""

    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}  # Track metadata per key

    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set a value in cache with TTL."""
        self._store[key] = {
            'value': value,
            'expires_at': time.time() + ttl
        }
        # Track metadata for analytics
        self._metadata[key] = {
            'created_at': time.time(),
            'access_count': 0,
            'last_accessed': None
        }
        return True

    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        if key not in self._store:
            return None

        entry = self._store[key]
        if time.time() > entry['expires_at']:
            del self._store[key]
            if key in self._metadata:
                del self._metadata[key]
            return None

        # Update access metadata
        if key in self._metadata:
            self._metadata[key]['access_count'] += 1
            self._metadata[key]['last_accessed'] = time.time()

        return entry['value']

    def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        if key in self._store:
            del self._store[key]
            return True
        return False

    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if key not in self._store:
            return False

        entry = self._store[key]
        if time.time() > entry['expires_at']:
            del self._store[key]
            return False

        return True

    def keys(self) -> list:
        """Get all keys in cache."""
        # Clean expired keys first
        current_time = time.time()
        expired = [k for k, v in self._store.items() if current_time > v['expires_at']]
        for k in expired:
            del self._store[k]

        return list(self._store.keys())

    def clear(self) -> None:
        """Clear all cache entries."""
        self._store.clear()
        self._metadata.clear()

    def get_key_metadata(self, key: str) -> Dict[str, Any]:
        """Get metadata for a specific cache key."""
        # This will raise KeyError if key doesn't exist in metadata
        return self._metadata[key]

    def get_access_count(self, key: str) -> int:
        """Get access count for a cache key."""
        return self._metadata[key]['access_count']
