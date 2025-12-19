"""Data service with cached operations."""
from decorators import cache
import time


class DataService:
    """Service for data operations with caching."""

    def __init__(self):
        self.call_count = 0

    @cache  # BUG: Old syntax without TTL argument
    def fetch_user_data(self, user_id):
        """
        Fetch user data from database (expensive operation).

        This method uses the old @cache decorator syntax without TTL.
        The new decorator requires @cache(ttl=seconds).
        """
        self.call_count += 1
        print(f"  [DB] Fetching user data for user_id={user_id}...")
        time.sleep(0.1)  # Simulate DB query

        return {
            "user_id": user_id,
            "name": f"User {user_id}",
            "email": f"user{user_id}@example.com",
            "role": "member",
            "created_at": "2024-01-01",
        }

    @cache  # BUG: Old syntax
    def get_user_permissions(self, user_id):
        """Get user permissions (cached)."""
        self.call_count += 1
        print(f"  [DB] Fetching permissions for user_id={user_id}...")
        time.sleep(0.1)

        return {
            "user_id": user_id,
            "permissions": ["read", "write", "delete"],
            "is_admin": user_id == 1,
        }

    @cache  # BUG: Old syntax
    def calculate_user_stats(self, user_id):
        """Calculate user statistics (expensive computation)."""
        self.call_count += 1
        print(f"  [COMPUTE] Calculating stats for user_id={user_id}...")
        time.sleep(0.2)

        return {
            "user_id": user_id,
            "total_posts": user_id * 10,
            "total_comments": user_id * 25,
            "reputation": user_id * 100,
        }

    def get_call_count(self):
        """Get number of actual function calls (not cached)."""
        return self.call_count

    def reset_count(self):
        """Reset call counter."""
        self.call_count = 0
