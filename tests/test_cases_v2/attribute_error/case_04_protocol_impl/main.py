"""Test protocol-based implementations with adapters."""
from protocols import StorageProtocol, SerializerProtocol
from implementations import (
    MemoryStorage, FileStorage,
    JsonSerializer, PickleSerializer,
    SchemaValidator
)
from adapters import StorageAdapter


def main():
    # Create implementations
    storage = MemoryStorage()
    serializer = JsonSerializer()
    validator = SchemaValidator({
        "name": str,
        "age": int,
        "email": str,
    })

    # Verify protocol compliance
    print(f"Storage implements protocol: {isinstance(storage, StorageProtocol)}")
    print(f"Serializer implements protocol: {isinstance(serializer, SerializerProtocol)}")

    # Create adapter
    adapter = StorageAdapter(storage, serializer, validator)

    # Save some data
    user_data = {
        "name": "Alice",
        "age": 30,
        "email": "alice@example.com",
    }
    adapter.save("user:001", user_data)
    print(f"\nSaved user data")

    # Load data back
    loaded = adapter.load("user:001")
    print(f"Loaded: {loaded}")

    # List keys
    keys = adapter.list_keys("user:")
    print(f"Keys: {keys}")

    # Get content type - this triggers the bug
    content_type = adapter.get_content_type()
    print(f"Content type: {content_type}")

    # Get schema
    schema = adapter.get_schema()
    print(f"Schema: {schema}")


if __name__ == "__main__":
    main()
