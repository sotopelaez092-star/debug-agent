"""Test complex decorator chains with multiple decorators stacked."""
from decorators.auth import AuthContext
from handlers import UserHandler, AdminHandler


def main():
    # Set up handlers
    user_handler = UserHandler()
    admin_handler = AdminHandler(user_handler)

    # Simulate authentication as super admin
    AuthContext.set_user({
        "id": "admin-001",
        "username": "superadmin",
        "roles": ["user", "admin", "super_admin"],
    })

    # Create some users
    user1 = user_handler.create_user("user-001", "alice", "alice@example.com")
    user2 = user_handler.create_user("user-002", "bob", "bob@example.com")
    print(f"Created users: {user1['username']}, {user2['username']}")

    # Grant admin role to alice
    admin_handler.grant_role("user-001", "admin")
    print("Granted admin role to alice")

    # List all users
    users = user_handler.list_users()
    print(f"Total users: {len(users)}")

    # This triggers the bug - get_log() doesn't exist, should be get_logs()
    logs = admin_handler.get_audit_logs()
    print(f"Audit log entries: {len(logs)}")

    # Clean up
    AuthContext.clear()


if __name__ == "__main__":
    main()
