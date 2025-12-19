"""
Data processing module.
Processes serialized data from models - expects OLD snake_case keys.
"""
from typing import Dict, Any, List


class DataProcessor:
    """Processes and validates data from models."""

    def process_user_profile(self, user_dict: Dict[str, Any]) -> Dict[str, str]:
        """
        Process user profile dictionary.
        This code expects OLD snake_case keys (user_id, first_name, etc.)
        """
        # Extract fields using OLD key names
        user_id = user_dict['user_id']  # KeyError: expects 'user_id' but gets 'userId'
        first_name = user_dict['first_name']  # KeyError: expects 'first_name'
        last_name = user_dict['last_name']  # KeyError: expects 'last_name'
        email = user_dict['email']  # This one is fine

        # Format full name
        full_name = f"{first_name} {last_name}"

        return {
            'id': user_id,
            'name': full_name,
            'email': email
        }

    def extract_user_contact(self, user_dict: Dict[str, Any]) -> Dict[str, str]:
        """Extract contact information from user profile."""
        email = user_dict['email']
        phone = user_dict.get('phone_number', 'N/A')  # KeyError: expects 'phone_number'

        return {
            'email': email,
            'phone': phone
        }

    def validate_user_data(self, user_dict: Dict[str, Any]) -> bool:
        """Validate required user fields exist."""
        required_fields = ['user_id', 'first_name', 'last_name', 'email']

        for field in required_fields:
            if field not in user_dict:
                print(f"Missing required field: {field}")
                return False

        return True
