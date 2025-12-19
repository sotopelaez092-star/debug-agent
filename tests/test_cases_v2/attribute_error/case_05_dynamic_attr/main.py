"""Test dynamic attribute models with __getattr__ and __setattr__."""
from models import DynamicModel, ConfigModel, EntityModel
from loaders import EntityLoader, ConfigLoader
from validators import EntityValidator


def main():
    # Create an entity with dynamic attributes
    user = EntityModel("user-001", name="Alice", email="alice@example.com", age=30)
    print(f"Created entity: {user.entity_id}")
    print(f"Name: {user.name}")
    print(f"Age: {user.age}")

    # Add more dynamic attributes
    user.department = "Engineering"
    user.level = "Senior"
    print(f"Department: {user.department}")

    # Update entity
    user.update(age=31, level="Staff")
    print(f"Updated age: {user.age}")

    # Create related entity
    manager = EntityModel("user-002", name="Bob", email="bob@example.com")
    user.add_relation("manager", manager)
    print(f"Manager: {user.get_relations('manager')[0].name}")

    # Load entities from dictionaries
    loader = EntityLoader()
    data = {
        "id": "user-003",
        "attributes": {"name": "Charlie", "email": "charlie@example.com"}
    }
    charlie = loader.load(data)
    print(f"\nLoaded: {charlie.name}")

    # Validate entity - this triggers the bug
    validator = EntityValidator(required_attrs=["name", "email", "department"])
    is_valid, errors = validator.validate(charlie)
    print(f"\nValid: {is_valid}")
    if errors:
        print(f"Errors: {errors}")

    # Test config model
    config = ConfigModel("app", debug=True, log_level="INFO")
    db_config = ConfigModel("database", host="localhost", port=5432)
    config.add_nested_config("database", db_config)
    print(f"\nConfig: {config.get_full_config()}")


if __name__ == "__main__":
    main()
