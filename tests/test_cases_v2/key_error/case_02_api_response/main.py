"""
Main application demonstrating API integration.
Uses UserService to fetch and display user data.
"""
from api_client import APIClient
from user_service import UserService
from analytics import UserAnalytics
from notification_service import NotificationService


def main():
    """Main application entry point."""
    # Initialize API client
    api_client = APIClient(
        base_url="https://api.example.com",
        api_key="test_key_123"
    )
    api_client.authenticate()

    # Initialize services
    user_service = UserService(api_client)
    analytics = UserAnalytics(user_service)
    notifications = NotificationService(user_service)

    print("=== User Profile Demo ===\n")

    user_id = "user_12345"

    # This will fail with KeyError because the API response structure changed
    print(f"Fetching user info for: {user_id}")
    user_info = user_service.get_user_info(user_id)

    print(f"\nUser Info:")
    print(f"  ID: {user_info['id']}")
    print(f"  Name: {user_info['name']}")
    print(f"  Email: {user_info['email']}")

    # Track analytics
    print(f"\nTracking user engagement...")
    analytics.track_user_engagement(user_id)

    # Send notification
    print(f"\nSending welcome email...")
    notifications.send_welcome_email(user_id)

    print(f"\n=== Complete ===")


if __name__ == "__main__":
    main()
