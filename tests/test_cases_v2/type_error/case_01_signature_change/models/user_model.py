"""User data model and repository."""
from database import QueryBuilder


class User:
    """User entity."""

    def __init__(self, id=None, name=None, email=None, role="user"):
        self.id = id
        self.name = name
        self.email = email
        self.role = role

    def to_dict(self):
        """Convert user to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
        }

    @classmethod
    def from_dict(cls, data):
        """Create user from dictionary."""
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            email=data.get("email"),
            role=data.get("role", "user"),
        )

    def __repr__(self):
        return f"User(id={self.id}, name={self.name}, email={self.email}, role={self.role})"


class UserRepository:
    """Repository for user data access."""

    def __init__(self, connection):
        self.connection = connection
        self.table = "users"

    def find_by_id(self, user_id):
        """Find user by ID."""
        # This uses the OLD signature - should be fixed to use keyword args
        # Old: select(table, columns, filters)
        # New: select(table=table, columns=columns, filters=filters)
        builder = QueryBuilder(self.connection)
        results = builder.select(
            self.table,
            ["id", "name", "email", "role"],
            {"id": user_id}
        ).execute()

        if results:
            return User.from_dict(results[0])
        return None

    def find_by_email(self, email):
        """Find user by email."""
        builder = QueryBuilder(self.connection)
        # This also uses old signature
        results = builder.select(
            self.table,
            ["id", "name", "email", "role"],
            {"email": email}
        ).execute()

        if results:
            return User.from_dict(results[0])
        return None

    def find_all(self):
        """Get all users."""
        builder = QueryBuilder(self.connection)
        # This one too
        results = builder.select(
            self.table,
            ["id", "name", "email", "role"],
            None
        ).execute()

        return [User.from_dict(row) for row in results]

    def create(self, user):
        """Create a new user."""
        builder = QueryBuilder(self.connection)
        result = builder.insert(
            table=self.table,
            data={
                "name": user.name,
                "email": user.email,
                "role": user.role,
            }
        ).execute()

        user.id = result.get("inserted_id")
        return user

    def update(self, user):
        """Update existing user."""
        builder = QueryBuilder(self.connection)
        builder.update(
            table=self.table,
            data={
                "name": user.name,
                "email": user.email,
                "role": user.role,
            },
            filters={"id": user.id}
        ).execute()

        return user

    def delete(self, user_id):
        """Delete user by ID."""
        builder = QueryBuilder(self.connection)
        builder.delete(
            table=self.table,
            filters={"id": user_id}
        ).execute()
