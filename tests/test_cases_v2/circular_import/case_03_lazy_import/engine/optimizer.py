"""Query optimizer that analyzes and optimizes queries."""
from typing import List, Dict, Any
from config import Settings


class QueryOptimizer:
    """Optimizes queries based on configuration settings."""

    def __init__(self):
        self._settings = Settings()

    def optimize(self, query: str) -> str:
        """Optimize a query based on settings."""
        if self._settings.get('enable_optimization'):
            # Add query hints
            if 'SELECT' in query.upper():
                query = f"/* USE INDEX */ {query}"
        return query

    def analyze(self, query: str) -> Dict[str, Any]:
        """Analyze query complexity and performance."""
        analysis = {
            "length": len(query),
            "tables": self._extract_tables(query),
            "estimated_cost": len(query) * 0.1,
            "optimization_level": self._settings.get('optimization_level', 1)
        }
        return analysis

    def _extract_tables(self, query: str) -> List[str]:
        """Extract table names from query."""
        # Simplified extraction
        tables = []
        if 'FROM' in query.upper():
            parts = query.upper().split('FROM')[1].split()
            if parts:
                tables.append(parts[0].lower())
        return tables

    def suggest_indexes(self, queries: List[str]) -> List[str]:
        """Suggest indexes based on query patterns."""
        suggestions = []
        for query in queries:
            tables = self._extract_tables(query)
            for table in tables:
                suggestions.append(f"CREATE INDEX idx_{table}_id ON {table}(id)")
        return list(set(suggestions))
