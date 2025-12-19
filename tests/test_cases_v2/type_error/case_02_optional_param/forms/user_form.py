"""User registration form validation."""
from validators import validate_email, validate_email_domain


class FormValidationError(Exception):
    """Raised when form validation fails."""
    pass


class UserRegistrationForm:
    """Validates user registration data."""

    ALLOWED_DOMAINS = ["example.com", "company.com", "test.org"]

    def __init__(self, data):
        self.data = data
        self.errors = {}

    def validate_name(self):
        """Validate user name."""
        name = self.data.get("name", "").strip()

        if not name:
            self.errors["name"] = "Name is required"
            return False

        if len(name) < 2:
            self.errors["name"] = "Name must be at least 2 characters"
            return False

        if len(name) > 100:
            self.errors["name"] = "Name must be less than 100 characters"
            return False

        return True

    def validate_email_field(self):
        """Validate email field."""
        email = self.data.get("email", "").strip()

        if not email:
            self.errors["email"] = "Email is required"
            return False

        # BUG: This uses the old signature without passing 'strict' parameter
        # Old code assumed strict=False was the default
        # New signature requires explicit strict parameter
        result = validate_email(email)

        if not result["valid"]:
            self.errors["email"] = result["message"]
            return False

        # Check domain whitelist
        if not validate_email_domain(email, self.ALLOWED_DOMAINS):
            self.errors["email"] = f"Email domain must be one of: {', '.join(self.ALLOWED_DOMAINS)}"
            return False

        return True

    def validate_password(self):
        """Validate password field."""
        password = self.data.get("password", "")

        if not password:
            self.errors["password"] = "Password is required"
            return False

        if len(password) < 8:
            self.errors["password"] = "Password must be at least 8 characters"
            return False

        # Check password strength
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)

        if not (has_upper and has_lower and has_digit):
            self.errors["password"] = "Password must contain uppercase, lowercase, and digits"
            return False

        return True

    def validate_password_confirm(self):
        """Validate password confirmation."""
        password = self.data.get("password", "")
        confirm = self.data.get("password_confirm", "")

        if password != confirm:
            self.errors["password_confirm"] = "Passwords do not match"
            return False

        return True

    def is_valid(self):
        """Check if form is valid."""
        self.errors = {}

        name_valid = self.validate_name()
        email_valid = self.validate_email_field()
        password_valid = self.validate_password()
        confirm_valid = self.validate_password_confirm()

        return name_valid and email_valid and password_valid and confirm_valid

    def get_errors(self):
        """Get validation errors."""
        return self.errors

    def get_cleaned_data(self):
        """Get cleaned and validated data."""
        if self.errors:
            raise FormValidationError("Form has validation errors")

        return {
            "name": self.data.get("name", "").strip(),
            "email": self.data.get("email", "").strip().lower(),
            "password": self.data.get("password", ""),
        }
