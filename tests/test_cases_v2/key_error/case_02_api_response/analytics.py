"""
Analytics module for tracking user metrics.
Processes user data for analytics purposes.
"""
from typing import Dict, Any, List
from user_service import UserService


class UserAnalytics:
    """Handles user analytics and metrics."""

    def __init__(self, user_service: UserService):
        self.user_service = user_service
        self.metrics: Dict[str, Any] = {}

    def track_user_engagement(self, user_id: str) -> None:
        """Track user engagement metrics."""
        try:
            user_info = self.user_service.get_user_info(user_id)
            print(f"Tracking engagement for user: {user_info['name']}")

            # Record metrics
            self.metrics[user_id] = {
                'name': user_info['name'],
                'email': user_info['email'],
                'last_tracked': '2024-01-15'
            }

        except KeyError as e:
            print(f"Error tracking user: {e}")
            raise

    def get_user_theme_stats(self, user_id: str) -> Dict[str, Any]:
        """Get statistics about user theme preferences."""
        prefs = self.user_service.get_user_preferences(user_id)
        return {
            'theme': prefs['theme'],
            'is_dark_mode': prefs['theme'] == 'dark'
        }

    def export_metrics(self) -> List[Dict[str, Any]]:
        """Export all collected metrics."""
        return [
            {'user_id': uid, **data}
            for uid, data in self.metrics.items()
        ]
