"""Test user management system with database query builder."""
from database import create_connection
from services import UserService


def main():
    # Database configuration
    config = {
        "host": "localhost",
        "database": "user_db",
        "user": "admin",
        "password": "secret123",
    }

    # Create connection and service
    with create_connection(config) as conn:
        service = UserService(conn)

        print("=== User Management System ===\n")

        # This will trigger TypeError when find_by_id calls builder.select()
        # with positional arguments instead of keyword-only arguments
        print("1. Fetching user by ID...")
        try:
            user = service.get_user(1)
            print(f"   Found: {user}")
        except Exception as e:
            print(f"   Error: {type(e).__name__}: {e}")
            raise

        print("\n2. Fetching user by email...")
        user = service.get_user_by_email("alice@example.com")
        print(f"   Found: {user}")

        print("\n3. Listing all users...")
        users = service.list_users()
        for user in users:
            print(f"   - {user}")

        print("\n4. Listing admin users...")
        admins = service.list_admin_users()
        for admin in admins:
            print(f"   - {admin}")

        print("\nDone!")


if __name__ == "__main__":
    main()
