"""
Cache backend implementations.
Different backends are defined based on feature flags.
"""

import logging
from typing import Any, Optional
from feature_flags import has_redis, feature_flags

logger = logging.getLogger(__name__)


class CacheBackend:
    """Base class for cache backends."""

    def get(self, key: str) -> Optional[Any]:
        raise NotImplementedError

    def set(self, key: str, value: Any, ttl: int = 300):
        raise NotImplementedError

    def delete(self, key: str):
        raise NotImplementedError

    def clear(self):
        raise NotImplementedError


class MemoryCache(CacheBackend):
    """In-memory cache implementation (always available)."""

    def __init__(self):
        self._cache = {}
        logger.info("Memory cache initialized")

    def get(self, key: str) -> Optional[Any]:
        return self._cache.get(key)

    def set(self, key: str, value: Any, ttl: int = 300):
        self._cache[key] = value
        logger.debug(f"Cache set: {key}")

    def delete(self, key: str):
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Cache deleted: {key}")

    def clear(self):
        self._cache.clear()
        logger.info("Cache cleared")


# Conditionally define RedisCache only if Redis is enabled
if has_redis():
    logger.info("Redis cache is enabled, defining RedisCache class")

    class RedisCache(CacheBackend):
        """Redis cache implementation (only available when Redis is enabled)."""

        def __init__(self, host: str = 'localhost', port: int = 6379):
            self.host = host
            self.port = port
            # Simulate Redis connection
            self._client = self._connect()
            logger.info(f"Redis cache initialized: {host}:{port}")

        def _connect(self):
            """Connect to Redis."""
            # Simulated connection
            return {'connected': True, 'data': {}}

        def get(self, key: str) -> Optional[Any]:
            return self._client['data'].get(key)

        def set(self, key: str, value: Any, ttl: int = 300):
            self._client['data'][key] = value
            logger.debug(f"Redis cache set: {key} (ttl={ttl})")

        def delete(self, key: str):
            if key in self._client['data']:
                del self._client['data'][key]
                logger.debug(f"Redis cache deleted: {key}")

        def clear(self):
            self._client['data'].clear()
            logger.info("Redis cache cleared")

else:
    logger.info("Redis cache is disabled, RedisCache will not be available")


def get_default_cache() -> CacheBackend:
    """Get the default cache backend based on configuration."""
    if has_redis():
        logger.info("Using Redis cache backend")
        return RedisCache()
    else:
        logger.info("Using memory cache backend")
        return MemoryCache()
