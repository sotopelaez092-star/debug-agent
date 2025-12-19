"""
Main application demonstrating dynamic plugin loading.
This will fail when trying to load the transformer plugin.
"""

from plugin_manager import PluginManager


def main():
    """Main function demonstrating plugin system."""
    print("=== Plugin System Demo ===\n")

    manager = PluginManager()

    # List available plugins
    print("Available plugins:", manager.list_plugins())
    print()

    # Load and use processor plugin - this works
    print("--- Testing Data Processor Plugin ---")
    processor = manager.get_plugin("processor")
    result = processor.execute({"name": "john", "city": "paris"})
    print(f"Processed result: {result}\n")

    # Load and use validator plugin - this works
    print("--- Testing Validation Plugin ---")
    validator = manager.get_plugin("validator")
    is_valid = validator.execute("test@example.com", "email")
    print(f"Email validation: {is_valid}\n")

    # Load and use analytics plugin - this works
    print("--- Testing Analytics Plugin ---")
    analytics = manager.get_plugin("analytics")
    analytics.execute("user_login", {"user_id": 123})
    analytics.execute("page_view", {"page": "/home"})
    print(f"Analytics summary: {analytics.get_event_summary()}\n")

    # Try to load transformer plugin - this will FAIL
    print("--- Testing Transformer Plugin ---")
    try:
        transformer = manager.get_plugin("transformer")
        result = transformer.execute([{"a": 1}, {"b": 2}], "to_csv")
        print(f"Transformation result: {result}")
    except Exception as e:
        print(f"ERROR: {e}")


if __name__ == "__main__":
    main()
