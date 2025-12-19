"""Query execution engine that manages database drivers."""
from typing import Dict, Any, Optional
# CIRCULAR IMPORT: Executor needs drivers to execute queries
from drivers import PostgresDriver, RedisDriver, MongoDriver


class QueryExecutor:
    """Executes queries across different database drivers."""

    def __init__(self):
        self._drivers: Dict[str, Any] = {
            'postgres': PostgresDriver(),
            'redis': RedisDriver(),
            'mongo': MongoDriver()
        }
        self._cache = {}

    def execute(self, query: str, driver_type: str = 'postgres') -> Any:
        """Execute a query using the specified driver."""
        driver = self._drivers.get(driver_type)
        if not driver:
            raise ValueError(f"Unknown driver type: {driver_type}")

        # Check cache first
        cache_key = f"{driver_type}:{query}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Execute query
        result = driver.execute(query)
        self._cache[cache_key] = result
        return result

    def execute_batch(self, queries: list, driver_type: str = 'postgres') -> list:
        """Execute multiple queries in batch."""
        driver = self._drivers.get(driver_type)
        if not driver:
            raise ValueError(f"Unknown driver type: {driver_type}")

        return driver.execute_batch(queries)

    def get_driver_status(self, driver_type: str) -> Dict[str, Any]:
        """Get status information for a specific driver."""
        driver = self._drivers.get(driver_type)
        if driver:
            return driver.get_status()
        return {"error": "Driver not found"}

    def clear_cache(self) -> None:
        """Clear the query cache."""
        self._cache.clear()
