"""
API client for making requests to external service.
Handles authentication and request formatting.
"""
import json
from typing import Dict, Any, Optional


class APIClient:
    """Client for interacting with external API."""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.session_token: Optional[str] = None

    def authenticate(self) -> bool:
        """Authenticate with the API."""
        print(f"Authenticating with API at {self.base_url}")
        # Simulate authentication
        self.session_token = "mock_token_12345"
        return True

    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Fetch user profile from API.
        Returns the API response as-is.
        """
        # Simulate API response with NEW v2 format
        # The API was updated and changed the response structure
        response = {
            "status": "success",
            "data": {
                "user": {
                    "id": user_id,
                    "profile": {
                        "personal": {
                            "firstName": "John",
                            "lastName": "Doe"
                        },
                        "contact": {
                            "email": "john.doe@example.com",
                            "phone": "+1234567890"
                        }
                    },
                    "settings": {
                        "preferences": {
                            "theme": "dark",
                            "language": "en"
                        },
                        "privacy": {
                            "profileVisible": True
                        }
                    }
                }
            },
            "metadata": {
                "version": "2.0",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
        return response

    def get_user_posts(self, user_id: str) -> Dict[str, Any]:
        """
        Fetch user's posts from API.
        Returns the API response.
        """
        response = {
            "status": "success",
            "data": {
                "posts": [
                    {
                        "id": "post_1",
                        "content": {
                            "text": "Hello world!",
                            "media": []
                        },
                        "metadata": {
                            "created": "2024-01-15",
                            "likes": 42
                        }
                    }
                ]
            }
        }
        return response
