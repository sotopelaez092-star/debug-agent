"""User API endpoints."""
from forms import UserRegistrationForm, FormValidationError
from validators import validate_email


class APIResponse:
    """API response wrapper."""

    def __init__(self, success, data=None, errors=None):
        self.success = success
        self.data = data or {}
        self.errors = errors or {}

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "success": self.success,
            "data": self.data,
            "errors": self.errors,
        }


class UserAPI:
    """User management API."""

    def __init__(self):
        self.users = []  # In-memory user storage

    def register(self, request_data):
        """
        Register a new user.

        Args:
            request_data: Dictionary with name, email, password, password_confirm

        Returns:
            APIResponse object
        """
        # Validate form
        form = UserRegistrationForm(request_data)

        if not form.is_valid():
            return APIResponse(success=False, errors=form.get_errors())

        # Get cleaned data
        try:
            user_data = form.get_cleaned_data()
        except FormValidationError as e:
            return APIResponse(success=False, errors={"form": str(e)})

        # Check if user already exists
        if any(u["email"] == user_data["email"] for u in self.users):
            return APIResponse(
                success=False,
                errors={"email": "User with this email already exists"}
            )

        # Create user
        user = {
            "id": len(self.users) + 1,
            "name": user_data["name"],
            "email": user_data["email"],
            "active": True,
        }
        self.users.append(user)

        return APIResponse(
            success=True,
            data={"user": user, "message": "User registered successfully"}
        )

    def check_email_availability(self, email):
        """
        Check if email is available for registration.

        Args:
            email: Email address to check

        Returns:
            APIResponse object
        """
        # Quick validation - also uses old signature without strict parameter
        result = validate_email(email)

        if not result["valid"]:
            return APIResponse(
                success=False,
                errors={"email": result["message"]}
            )

        # Check availability
        is_taken = any(u["email"] == email for u in self.users)

        return APIResponse(
            success=True,
            data={
                "email": email,
                "available": not is_taken,
                "message": "Email is available" if not is_taken else "Email is taken"
            }
        )

    def get_users(self):
        """Get all registered users."""
        return APIResponse(
            success=True,
            data={"users": self.users, "count": len(self.users)}
        )

    def update_email(self, user_id, new_email):
        """
        Update user's email address.

        Args:
            user_id: User ID
            new_email: New email address

        Returns:
            APIResponse object
        """
        # Validate new email - also missing strict parameter
        result = validate_email(new_email)

        if not result["valid"]:
            return APIResponse(
                success=False,
                errors={"email": result["message"]}
            )

        # Find user
        user = next((u for u in self.users if u["id"] == user_id), None)
        if not user:
            return APIResponse(
                success=False,
                errors={"user": "User not found"}
            )

        # Update email
        user["email"] = new_email

        return APIResponse(
            success=True,
            data={"user": user, "message": "Email updated successfully"}
        )
