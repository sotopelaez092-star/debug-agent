"""
Main application entry point.
Demonstrates complex nested package imports with an error.
"""

from app.services.authentication import AuthService
from app.services.database import DatabaseManager
from app.services.data.validators import DataValidator
# Wrong import path - should be app.services.data.processors.json_processor
from app.services.processors.json_processor import JSONProcessor


def main():
    """Main application function."""
    # Initialize services
    auth = AuthService()
    db = DatabaseManager("postgresql://localhost/mydb")
    validator = DataValidator()
    processor = JSONProcessor()

    # Test authentication
    token = auth.generate_token("user123")
    print(f"Generated token: {token}")

    # Test database
    db.connect()
    results = db.query("SELECT * FROM users")
    print(f"Query results: {results}")

    # Test validation
    email_valid = validator.validate_email("test@example.com")
    print(f"Email valid: {email_valid}")

    # Test JSON processing
    data = {"name": "John", "age": 30}
    paths = processor.extract_paths(data)
    print(f"JSON paths: {paths}")


if __name__ == "__main__":
    main()
