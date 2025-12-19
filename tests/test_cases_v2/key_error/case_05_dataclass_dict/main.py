"""
Main application demonstrating dataclass dictionary key mismatch.
Models use camelCase in to_dict(), but processors expect snake_case.
"""
from models import UserProfile, Order, Address
from data_processor import DataProcessor
from order_processor import OrderProcessor
from report_generator import ReportGenerator


def main():
    """Main application entry point."""
    print("=== Data Processing Demo ===\n")

    # Create user profile
    user = UserProfile(
        user_id="user_12345",
        first_name="Jane",
        last_name="Smith",
        email="jane.smith@example.com",
        phone_number="+1-555-0100",
        date_of_birth="1990-05-15"
    )

    # Create order with shipping address
    address = Address(
        street="123 Main St",
        city="Springfield",
        state="IL",
        zip_code="62701"
    )

    order = Order(
        order_id="order_9876",
        user_id="user_12345",
        items=["item1", "item2", "item3"],
        total_amount=99.99,
        order_status="processing",
        shipping_address=address
    )

    # Convert to dictionaries (uses NEW camelCase keys)
    print("--- Converting Models to Dictionaries ---")
    user_dict = user.to_dict()
    order_dict = order.to_dict()

    print(f"User dict keys: {list(user_dict.keys())}")
    print(f"Order dict keys: {list(order_dict.keys())}")

    # Process data (expects OLD snake_case keys)
    print("\n--- Processing User Data ---")
    processor = DataProcessor()

    try:
        # This will fail because to_dict() returns camelCase keys
        # but processor expects snake_case keys
        result = processor.process_user_profile(user_dict)
        print(f"Processed user: {result}")
    except KeyError as e:
        print(f"KeyError while processing user: {e}")
        raise

    print("\n--- Processing Order Data ---")
    order_proc = OrderProcessor()

    try:
        result = order_proc.process_order(order_dict)
        print(f"Processed order: {result}")
    except KeyError as e:
        print(f"KeyError while processing order: {e}")
        raise

    # Generate reports
    print("\n--- Generating Reports ---")
    report_gen = ReportGenerator()

    user_report = report_gen.generate_user_report(user_dict)
    print(user_report)

    order_report = report_gen.generate_order_report(order_dict)
    print(order_report)

    print("\n=== Complete ===")


if __name__ == "__main__":
    main()
