"""Test diamond circular import pattern: Auth <-> Storage dependency."""
from consumers import APIHandler, TaskProcessor


def main():
    # Create API handler
    api = APIHandler()

    # User login
    session_id = api.login("alice", "password123")
    print(f"User logged in with session: {session_id}")

    # Save some data
    success = api.save_user_data(session_id, "profile", {"name": "Alice", "age": 30})
    print(f"Data saved: {success}")

    # Retrieve data
    profile = api.get_user_data(session_id, "profile")
    print(f"Retrieved profile: {profile}")

    # Process background tasks
    processor = TaskProcessor()
    processor.queue_task("save", session_id, {"key": "settings", "value": {"theme": "dark"}})
    processed = processor.process_tasks()
    print(f"Processed {processed} background tasks")

    # Logout
    api.logout(session_id)
    print("User logged out")


if __name__ == "__main__":
    main()
