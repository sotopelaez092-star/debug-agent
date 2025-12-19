"""Test application with configuration management."""
from services import ApplicationService


def main():
    # Create application service
    # This will trigger TypeError when load_json_config() returns tuple
    # but ConfigManager expects dict
    try:
        app = ApplicationService(config_file="config/app_config.json")
        app.initialize()
        app.shutdown()
    except Exception as e:
        print(f"\nError: {type(e).__name__}: {e}")
        raise


if __name__ == "__main__":
    main()
