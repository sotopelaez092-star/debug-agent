"""Caching decorator with configurable TTL."""
import time
from functools import wraps


class CacheEntry:
    """Cache entry with timestamp and TTL."""

    def __init__(self, value, ttl):
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl

    def is_expired(self):
        """Check if cache entry is expired."""
        if self.ttl is None:
            return False
        return (time.time() - self.created_at) > self.ttl


# Global cache storage
_cache_storage = {}


def cache(ttl):
    """
    Cache function results with time-to-live.

    Args:
        ttl: Time-to-live in seconds (required parameter)

    Returns:
        Decorator function

    Usage:
        @cache(ttl=300)
        def expensive_function(x, y):
            return x + y

    Note:
        This decorator was refactored to require explicit TTL configuration
        for better cache control and to prevent indefinite memory growth.

        Old signature: @cache (no arguments, infinite TTL)
        New signature: @cache(ttl=seconds) (requires TTL argument)

        Migration:
        - Old: @cache
        - New: @cache(ttl=3600) or @cache(ttl=None) for infinite
    """
    def decorator(func):
        cache_key_prefix = f"{func.__module__}.{func.__name__}"

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function arguments
            cache_key = f"{cache_key_prefix}:{args}:{kwargs}"

            # Check if cached value exists and is not expired
            if cache_key in _cache_storage:
                entry = _cache_storage[cache_key]
                if not entry.is_expired():
                    print(f"[CACHE HIT] {func.__name__}{args}")
                    return entry.value
                else:
                    print(f"[CACHE EXPIRED] {func.__name__}{args}")
                    del _cache_storage[cache_key]

            # Call function and cache result
            print(f"[CACHE MISS] {func.__name__}{args}")
            result = func(*args, **kwargs)
            _cache_storage[cache_key] = CacheEntry(result, ttl)
            return result

        wrapper.cache_clear = lambda: _cache_storage.clear()
        wrapper.cache_info = lambda: {
            "size": len(_cache_storage),
            "ttl": ttl,
        }

        return wrapper

    return decorator


def cache_clear_all():
    """Clear all cached values."""
    _cache_storage.clear()


def cache_stats():
    """Get cache statistics."""
    total_entries = len(_cache_storage)
    expired_entries = sum(1 for entry in _cache_storage.values() if entry.is_expired())

    return {
        "total_entries": total_entries,
        "active_entries": total_entries - expired_entries,
        "expired_entries": expired_entries,
    }


def get_cache_storage():
    """Get reference to cache storage (for testing)."""
    return _cache_storage
