"""
Aggregation builder for complex queries.
Extends query builder with aggregation functions.
"""

from query_builder import QueryBuilder
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class AggregationBuilder(QueryBuilder):
    """
    Extended query builder with aggregation support.
    Provides methods for COUNT, SUM, AVG, MIN, MAX operations.
    """

    def __init__(self, table: str):
        super().__init__(table)
        self._aggregations: Dict[str, str] = {}

    def count(self, field: str = '*', alias: str = 'count') -> 'AggregationBuilder':
        """Add COUNT aggregation."""
        self._aggregations[alias] = f"COUNT({field})"
        return self

    def sum(self, field: str, alias: str = 'sum') -> 'AggregationBuilder':
        """Add SUM aggregation."""
        self._aggregations[alias] = f"SUM({field})"
        return self

    def avg(self, field: str, alias: str = 'avg') -> 'AggregationBuilder':
        """Add AVG aggregation."""
        self._aggregations[alias] = f"AVG({field})"
        return self

    def min(self, field: str, alias: str = 'min') -> 'AggregationBuilder':
        """Add MIN aggregation."""
        self._aggregations[alias] = f"MIN({field})"
        return self

    def max(self, field: str, alias: str = 'max') -> 'AggregationBuilder':
        """Add MAX aggregation."""
        self._aggregations[alias] = f"MAX({field})"
        return self

    def distinct_count(self, field: str, alias: str = 'distinct_count') -> 'AggregationBuilder':
        """Add DISTINCT COUNT aggregation."""
        self._aggregations[alias] = f"COUNT(DISTINCT {field})"
        return self

    def build(self) -> str:
        """Build query with aggregations."""
        # Add aggregation fields to select
        for alias, agg_func in self._aggregations.items():
            self.select(f"{agg_func} AS {alias}")

        return super().build()

    def __repr__(self):
        return f"AggregationBuilder(table='{self.table}', aggregations={len(self._aggregations)})"
