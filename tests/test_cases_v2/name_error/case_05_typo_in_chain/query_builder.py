"""
SQL query builder with fluent interface.
Provides a chainable API for building complex queries.
"""

from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class QueryBuilder:
    """
    Fluent interface for building SQL queries.
    Supports method chaining for complex query construction.
    """

    def __init__(self, table: str):
        self.table = table
        self._select_fields: List[str] = []
        self._where_conditions: List[str] = []
        self._join_clauses: List[str] = []
        self._group_by_fields: List[str] = []
        self._having_conditions: List[str] = []
        self._order_by_fields: List[str] = []
        self._limit_value: Optional[int] = None
        self._offset_value: Optional[int] = None

        logger.debug(f"QueryBuilder created for table: {table}")

    def select(self, *fields: str) -> 'QueryBuilder':
        """Select specific fields."""
        self._select_fields.extend(fields)
        return self

    def where(self, condition: str) -> 'QueryBuilder':
        """Add a WHERE condition."""
        self._where_conditions.append(condition)
        return self

    def join(self, table: str, condition: str, join_type: str = 'INNER') -> 'QueryBuilder':
        """Add a JOIN clause."""
        self._join_clauses.append(f"{join_type} JOIN {table} ON {condition}")
        return self

    def group_by(self, *fields: str) -> 'QueryBuilder':
        """Add GROUP BY fields."""
        self._group_by_fields.extend(fields)
        return self

    def having(self, condition: str) -> 'QueryBuilder':
        """Add a HAVING condition."""
        self._having_conditions.append(condition)
        return self

    def order_by(self, field: str, direction: str = 'ASC') -> 'QueryBuilder':
        """Add ORDER BY field."""
        self._order_by_fields.append(f"{field} {direction}")
        return self

    def limit(self, value: int) -> 'QueryBuilder':
        """Set LIMIT value."""
        self._limit_value = value
        return self

    def offset(self, value: int) -> 'QueryBuilder':
        """Set OFFSET value."""
        self._offset_value = value
        return self

    def build(self) -> str:
        """Build the final SQL query."""
        parts = []

        # SELECT
        if self._select_fields:
            fields = ', '.join(self._select_fields)
        else:
            fields = '*'

        parts.append(f"SELECT {fields}")

        # FROM
        parts.append(f"FROM {self.table}")

        # JOIN
        if self._join_clauses:
            parts.extend(self._join_clauses)

        # WHERE
        if self._where_conditions:
            conditions = ' AND '.join(f"({cond})" for cond in self._where_conditions)
            parts.append(f"WHERE {conditions}")

        # GROUP BY
        if self._group_by_fields:
            fields = ', '.join(self._group_by_fields)
            parts.append(f"GROUP BY {fields}")

        # HAVING
        if self._having_conditions:
            conditions = ' AND '.join(f"({cond})" for cond in self._having_conditions)
            parts.append(f"HAVING {conditions}")

        # ORDER BY
        if self._order_by_fields:
            fields = ', '.join(self._order_by_fields)
            parts.append(f"ORDER BY {fields}")

        # LIMIT
        if self._limit_value is not None:
            parts.append(f"LIMIT {self._limit_value}")

        # OFFSET
        if self._offset_value is not None:
            parts.append(f"OFFSET {self._offset_value}")

        query = ' '.join(parts)
        logger.debug(f"Built query: {query}")

        return query

    def __repr__(self):
        return f"QueryBuilder(table='{self.table}')"
