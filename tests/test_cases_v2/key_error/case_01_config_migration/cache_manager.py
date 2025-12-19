"""
Cache manager for handling application caching.
Uses configuration to set up cache backend.
"""
from typing import Optional, Dict, Any, List


class CacheManager:
    """Manages application cache with config-based setup."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.cache_store: Dict[str, Any] = {}
        self._initialized = False

    def initialize(self) -> None:
        """Initialize cache backend using configuration."""
        # Extract cache settings from config
        # This expects the OLD config structure
        redis_host = self.config['cache']['redis_host']
        redis_port = self.config['cache']['redis_port']
        ttl = self.config['cache']['ttl']

        print(f"Initializing cache with Redis at {redis_host}:{redis_port}")
        print(f"Default TTL: {ttl} seconds")

        self.cache_store = {}
        self._initialized = True

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self._initialized:
            raise RuntimeError("Cache not initialized")
        return self.cache_store.get(key)

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache."""
        if not self._initialized:
            raise RuntimeError("Cache not initialized")
        self.cache_store[key] = value

    def delete(self, key: str) -> None:
        """Delete key from cache."""
        if key in self.cache_store:
            del self.cache_store[key]

    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache_store.clear()

    def keys(self) -> List[str]:
        """Get all cache keys."""
        return list(self.cache_store.keys())
