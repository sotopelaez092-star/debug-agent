"""
User service layer that processes API responses.
This module was written for the old API v1 format.
"""
from typing import Dict, Any, List
from api_client import APIClient


class UserService:
    """Service for managing user-related operations."""

    def __init__(self, api_client: APIClient):
        self.api_client = api_client

    def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """
        Get user information from API and format it.
        This code expects the OLD v1 API response structure.
        """
        response = self.api_client.get_user_profile(user_id)

        # OLD v1 API structure was:
        # {
        #   "success": true,
        #   "user_data": {
        #     "id": "...",
        #     "name": "...",
        #     "email": "...",
        #     "preferences": {...}
        #   }
        # }

        # This code tries to access the old structure
        user_data = response['user_data']  # KeyError: 'user_data' doesn't exist
        user_id = user_data['id']
        name = user_data['name']
        email = user_data['email']

        return {
            'id': user_id,
            'name': name,
            'email': email
        }

    def get_user_preferences(self, user_id: str) -> Dict[str, str]:
        """
        Get user preferences from profile.
        Also expects old API format.
        """
        response = self.api_client.get_user_profile(user_id)

        # OLD v1 structure had preferences at top level
        prefs = response['user_data']['preferences']  # KeyError
        theme = prefs['theme']
        language = prefs['language']

        return {
            'theme': theme,
            'language': language
        }

    def get_user_email(self, user_id: str) -> str:
        """Get user's email address."""
        response = self.api_client.get_user_profile(user_id)
        # Old format: response['user_data']['email']
        return response['user_data']['email']  # KeyError
