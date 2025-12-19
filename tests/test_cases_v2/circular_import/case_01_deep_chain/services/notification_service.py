from typing import List
from models import Product, User
# CIRCULAR IMPORT: NotificationService needs UserService to get admin users
from services.user_service import UserService


class NotificationService:
    def __init__(self):
        self._user_service = UserService()
        self._notifications: List[str] = []

    def send_low_stock_alert(self, product: Product) -> None:
        message = f"Low stock alert: {product.name} has only {product.stock} items"
        self._notifications.append(message)
        # Notify admin users
        admins = self._get_admin_users()
        for admin in admins:
            print(f"[ALERT] To {admin.email}: {message}")

    def _get_admin_users(self) -> List[User]:
        # Get users with admin role (simplified)
        all_users = self._user_service.list_users()
        return [u for u in all_users if "admin" in u.email]

    def get_notifications(self) -> List[str]:
        return self._notifications.copy()
