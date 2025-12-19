"""
Notification service for sending messages to users.
Uses user data to send personalized notifications.
"""
from typing import List
from user_service import UserService


class NotificationService:
    """Handles sending notifications to users."""

    def __init__(self, user_service: UserService):
        self.user_service = user_service
        self.sent_notifications: List[str] = []

    def send_welcome_email(self, user_id: str) -> bool:
        """Send welcome email to user."""
        try:
            email = self.user_service.get_user_email(user_id)
            message = f"Welcome! Sending email to {email}"
            print(message)
            self.sent_notifications.append(email)
            return True
        except KeyError as e:
            print(f"Failed to send email: {e}")
            return False

    def send_preference_update(self, user_id: str) -> bool:
        """Notify user about preference updates."""
        user_info = self.user_service.get_user_info(user_id)
        email = user_info['email']

        message = f"Your preferences have been updated: {email}"
        print(message)
        return True

    def get_notification_count(self) -> int:
        """Get count of sent notifications."""
        return len(self.sent_notifications)
