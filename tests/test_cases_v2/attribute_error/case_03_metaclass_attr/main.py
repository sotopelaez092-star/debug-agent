"""Test metaclass-based plugin system with auto-registration."""
from plugins import CompressPlugin, EncryptPlugin, TransformPlugin
from registry import PluginManager
from core import PluginMeta


def main():
    # List all registered plugins
    print("Registered plugins:")
    for name, cls in PluginMeta.list_plugins().items():
        print(f"  - {name}: {cls.__name__}")

    # Create plugin manager
    manager = PluginManager()

    # Load transform plugin with dependencies
    # This will trigger the bug - get_plugin_metdata doesn't exist
    transform = manager.load_with_dependencies("transform", {"format": "json"})
    print(f"\nLoaded: {transform.get_info()}")

    # Execute pipeline
    data = {"message": "Hello, World!", "count": 42}
    print(f"\nOriginal data: {data}")

    # Transform -> Compress -> Encrypt pipeline
    result = manager.execute_pipeline(["transform", "compress", "encrypt"], data)
    print(f"Processed: {result[:50]}...")

    # Cleanup
    manager.shutdown_all()
    print("\nAll plugins shutdown")


if __name__ == "__main__":
    main()
