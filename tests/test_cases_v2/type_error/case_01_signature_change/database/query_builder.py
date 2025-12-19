"""Database query builder with refactored API."""


class QueryBuilder:
    """Build SQL queries with fluent interface."""

    def __init__(self, connection):
        self.connection = connection
        self.query_parts = []

    def select(self, *, table, columns=None, filters=None):
        """
        Build a SELECT query.

        Args:
            table: Table name (keyword-only)
            columns: List of column names (keyword-only, optional)
            filters: Dict of column: value filters (keyword-only, optional)

        Returns:
            QueryBuilder instance for chaining

        Note:
            This method was refactored to use keyword-only arguments
            for better clarity and to support future extensions.
            Old signature: select(table, columns, filters)
            New signature: select(*, table, columns=None, filters=None)
        """
        cols = columns if columns else ['*']
        col_str = ', '.join(cols)

        query = f"SELECT {col_str} FROM {table}"

        if filters:
            conditions = [f"{col} = '{val}'" for col, val in filters.items()]
            query += " WHERE " + " AND ".join(conditions)

        self.query_parts.append(query)
        return self

    def insert(self, *, table, data):
        """
        Build an INSERT query.

        Args:
            table: Table name (keyword-only)
            data: Dict of column: value pairs (keyword-only)

        Returns:
            QueryBuilder instance for chaining
        """
        columns = ', '.join(data.keys())
        values = ', '.join(f"'{v}'" for v in data.values())
        query = f"INSERT INTO {table} ({columns}) VALUES ({values})"
        self.query_parts.append(query)
        return self

    def update(self, *, table, data, filters=None):
        """
        Build an UPDATE query.

        Args:
            table: Table name (keyword-only)
            data: Dict of column: value pairs to update (keyword-only)
            filters: Dict of column: value filters (keyword-only, optional)

        Returns:
            QueryBuilder instance for chaining
        """
        set_clause = ', '.join(f"{col} = '{val}'" for col, val in data.items())
        query = f"UPDATE {table} SET {set_clause}"

        if filters:
            conditions = [f"{col} = '{val}'" for col, val in filters.items()]
            query += " WHERE " + " AND ".join(conditions)

        self.query_parts.append(query)
        return self

    def delete(self, *, table, filters=None):
        """
        Build a DELETE query.

        Args:
            table: Table name (keyword-only)
            filters: Dict of column: value filters (keyword-only, optional)

        Returns:
            QueryBuilder instance for chaining
        """
        query = f"DELETE FROM {table}"

        if filters:
            conditions = [f"{col} = '{val}'" for col, val in filters.items()]
            query += " WHERE " + " AND ".join(conditions)

        self.query_parts.append(query)
        return self

    def execute(self):
        """Execute the built query."""
        if not self.query_parts:
            raise ValueError("No query to execute")

        query = self.query_parts[-1]
        return self.connection.execute(query)

    def get_sql(self):
        """Get the SQL string without executing."""
        return self.query_parts[-1] if self.query_parts else ""
