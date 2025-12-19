"""Database connection management."""


class DatabaseConnection:
    """Simulated database connection."""

    def __init__(self, host, database, user, password):
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.connected = False
        self._results = []

    def connect(self):
        """Establish database connection."""
        print(f"Connecting to {self.database} at {self.host} as {self.user}")
        self.connected = True
        return self

    def disconnect(self):
        """Close database connection."""
        print("Disconnecting from database")
        self.connected = False

    def execute(self, query):
        """Execute a query and return results."""
        if not self.connected:
            raise ConnectionError("Not connected to database")

        print(f"Executing: {query}")

        # Simulate query results
        if query.startswith("SELECT"):
            return [
                {"id": 1, "name": "Alice", "email": "alice@example.com", "role": "admin"},
                {"id": 2, "name": "Bob", "email": "bob@example.com", "role": "user"},
            ]
        elif query.startswith("INSERT"):
            return {"inserted_id": 123, "rows_affected": 1}
        elif query.startswith("UPDATE"):
            return {"rows_affected": 1}
        elif query.startswith("DELETE"):
            return {"rows_affected": 1}
        else:
            return {"status": "ok"}

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
        return False


def create_connection(config):
    """Factory function to create database connection."""
    return DatabaseConnection(
        host=config.get("host", "localhost"),
        database=config.get("database", "mydb"),
        user=config.get("user", "admin"),
        password=config.get("password", ""),
    )
