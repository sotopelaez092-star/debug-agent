"""User business logic service."""
from models import User, UserRepository


class UserService:
    """Service layer for user operations."""

    def __init__(self, connection):
        self.repository = UserRepository(connection)

    def get_user(self, user_id):
        """Get user by ID with error handling."""
        user = self.repository.find_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        return user

    def get_user_by_email(self, email):
        """Get user by email."""
        user = self.repository.find_by_email(email)
        if not user:
            raise ValueError(f"User with email {email} not found")
        return user

    def list_users(self):
        """List all users."""
        return self.repository.find_all()

    def list_admin_users(self):
        """List all admin users."""
        all_users = self.repository.find_all()
        return [u for u in all_users if u.role == "admin"]

    def register_user(self, name, email, role="user"):
        """Register a new user."""
        # Check if email already exists
        try:
            existing = self.repository.find_by_email(email)
            if existing:
                raise ValueError(f"User with email {email} already exists")
        except:
            pass  # Email doesn't exist, which is good

        user = User(name=name, email=email, role=role)
        return self.repository.create(user)

    def update_user_role(self, user_id, new_role):
        """Update user's role."""
        user = self.get_user(user_id)
        user.role = new_role
        return self.repository.update(user)

    def promote_to_admin(self, user_id):
        """Promote user to admin role."""
        return self.update_user_role(user_id, "admin")

    def demote_from_admin(self, user_id):
        """Demote admin to regular user."""
        return self.update_user_role(user_id, "user")

    def delete_user(self, user_id):
        """Delete a user."""
        # Verify user exists first
        self.get_user(user_id)
        self.repository.delete(user_id)
