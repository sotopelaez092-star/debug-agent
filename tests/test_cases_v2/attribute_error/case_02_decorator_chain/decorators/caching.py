from functools import wraps
from typing import Callable, Optional
from datetime import datetime, timedelta


class CacheStore:
    _cache: dict = {}
    _ttl: dict = {}
    _default_ttl: timedelta = timedelta(minutes=5)

    @classmethod
    def get(cls, key: str) -> Optional[any]:
        if key not in cls._cache:
            return None
        if key in cls._ttl and datetime.now() > cls._ttl[key]:
            del cls._cache[key]
            del cls._ttl[key]
            return None
        return cls._cache[key]

    @classmethod
    def set(cls, key: str, value: any, ttl: Optional[timedelta] = None) -> None:
        cls._cache[key] = value
        cls._ttl[key] = datetime.now() + (ttl or cls._default_ttl)

    @classmethod
    def invalidate(cls, key: str) -> None:
        cls._cache.pop(key, None)
        cls._ttl.pop(key, None)

    @classmethod
    def clear(cls) -> None:
        cls._cache = {}
        cls._ttl = {}


def cached(ttl_seconds: int = 300) -> Callable:
    """Decorator that caches function results."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Build cache key from function name and arguments
            key_parts = [func.__name__] + [str(a) for a in args]
            key_parts += [f"{k}={v}" for k, v in sorted(kwargs.items())]
            cache_key = ":".join(key_parts)

            cached_value = CacheStore.get(cache_key)
            if cached_value is not None:
                return cached_value

            result = func(*args, **kwargs)
            CacheStore.set(cache_key, result, timedelta(seconds=ttl_seconds))
            return result
        wrapper._cached = True
        wrapper._cache_ttl = ttl_seconds
        return wrapper
    return decorator


def cache_invalidate(pattern: str) -> Callable:
    """Decorator that invalidates cache after function execution."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            # Invalidate matching cache entries
            keys_to_remove = [k for k in CacheStore._cache.keys() if pattern in k]
            for key in keys_to_remove:
                CacheStore.invalidate(key)
            return result
        wrapper._invalidates_cache = pattern
        return wrapper
    return decorator
