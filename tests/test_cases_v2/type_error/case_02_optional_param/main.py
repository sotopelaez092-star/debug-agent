"""Test user registration API with email validation."""
from api import UserAPI
import json


def main():
    api = UserAPI()

    print("=== User Registration API Test ===\n")

    # Test 1: Register a new user
    # This will trigger TypeError because validate_email() is called without 'strict' parameter
    print("1. Registering new user...")
    try:
        response = api.register({
            "name": "Alice Johnson",
            "email": "alice@example.com",
            "password": "SecurePass123",
            "password_confirm": "SecurePass123",
        })
        print(f"   Result: {json.dumps(response.to_dict(), indent=2)}")
    except Exception as e:
        print(f"   Error: {type(e).__name__}: {e}")
        raise

    # Test 2: Check email availability
    print("\n2. Checking email availability...")
    response = api.check_email_availability("bob@company.com")
    print(f"   Result: {json.dumps(response.to_dict(), indent=2)}")

    # Test 3: Register another user
    print("\n3. Registering second user...")
    response = api.register({
        "name": "Bob Smith",
        "email": "bob@company.com",
        "password": "AnotherPass456",
        "password_confirm": "AnotherPass456",
    })
    print(f"   Result: {json.dumps(response.to_dict(), indent=2)}")

    # Test 4: List all users
    print("\n4. Listing all users...")
    response = api.get_users()
    print(f"   Result: {json.dumps(response.to_dict(), indent=2)}")

    # Test 5: Update email
    print("\n5. Updating user email...")
    response = api.update_email(1, "alice.new@example.com")
    print(f"   Result: {json.dumps(response.to_dict(), indent=2)}")

    print("\nDone!")


if __name__ == "__main__":
    main()
