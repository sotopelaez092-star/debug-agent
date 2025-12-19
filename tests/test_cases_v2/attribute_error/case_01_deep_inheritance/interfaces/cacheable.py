from typing import Optional
from datetime import datetime, timedelta


class Cacheable:
    """Interface for cacheable objects."""

    _cache_ttl: timedelta = timedelta(minutes=5)
    _cached_at: Optional[datetime] = None

    def cache_key(self) -> str:
        raise NotImplementedError

    def is_cache_valid(self) -> bool:
        if self._cached_at is None:
            return False
        return datetime.now() - self._cached_at < self._cache_ttl

    def invalidate_cache(self) -> None:
        self._cached_at = None
