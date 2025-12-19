"""
Data models using dataclasses.
These models have to_dict() methods for serialization.
"""
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class Address:
    """Address data model."""
    street: str
    city: str
    state: str
    zip_code: str
    country: str = "USA"

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'street': self.street,
            'city': self.city,
            'state': self.state,
            'zipCode': self.zip_code,  # Changed from zip_code to zipCode
            'country': self.country
        }


@dataclass
class UserProfile:
    """User profile data model."""
    user_id: str
    first_name: str
    last_name: str
    email: str
    phone_number: Optional[str] = None
    date_of_birth: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        # Changed key names to camelCase for API compatibility
        return {
            'userId': self.user_id,  # Changed from user_id
            'firstName': self.first_name,  # Changed from first_name
            'lastName': self.last_name,  # Changed from last_name
            'email': self.email,
            'phoneNumber': self.phone_number,  # Changed from phone_number
            'dateOfBirth': self.date_of_birth,  # Changed from date_of_birth
            'createdAt': self.created_at  # Changed from created_at
        }


@dataclass
class Order:
    """Order data model."""
    order_id: str
    user_id: str
    items: List[str]
    total_amount: float
    order_status: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    shipping_address: Optional[Address] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = {
            'orderId': self.order_id,  # Changed from order_id
            'userId': self.user_id,  # Changed from user_id
            'items': self.items,
            'totalAmount': self.total_amount,  # Changed from total_amount
            'orderStatus': self.order_status,  # Changed from order_status
            'createdAt': self.created_at  # Changed from created_at
        }

        if self.shipping_address:
            result['shippingAddress'] = self.shipping_address.to_dict()

        return result
