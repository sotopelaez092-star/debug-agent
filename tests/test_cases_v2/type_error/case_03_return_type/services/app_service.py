"""Application service using configuration."""
from config import ConfigManager


class DatabaseService:
    """Database service using configuration."""

    def __init__(self, config_manager):
        self.config = config_manager
        self.connection = None

    def connect(self):
        """Connect to database using configuration."""
        db_config = self.config.get_database_config()

        print(f"Connecting to database:")
        print(f"  Host: {db_config.get('host')}")
        print(f"  Port: {db_config.get('port')}")
        print(f"  Database: {db_config.get('name')}")
        print(f"  User: {db_config.get('user')}")
        print(f"  Pool size: {db_config.get('pool_size')}")

        self.connection = f"Connected to {db_config.get('name')}"
        return self.connection

    def disconnect(self):
        """Disconnect from database."""
        print("Disconnecting from database")
        self.connection = None


class APIService:
    """API service using configuration."""

    def __init__(self, config_manager):
        self.config = config_manager
        self.running = False

    def start(self):
        """Start API server using configuration."""
        api_config = self.config.get_api_config()

        print(f"Starting API server:")
        print(f"  Host: {api_config.get('host')}")
        print(f"  Port: {api_config.get('port')}")
        print(f"  Workers: {api_config.get('workers')}")
        print(f"  Timeout: {api_config.get('timeout')}s")

        self.running = True
        return True

    def stop(self):
        """Stop API server."""
        print("Stopping API server")
        self.running = False


class LoggingService:
    """Logging service using configuration."""

    def __init__(self, config_manager):
        self.config = config_manager
        self.initialized = False

    def initialize(self):
        """Initialize logging using configuration."""
        log_config = self.config.get_logging_config()

        print(f"Initializing logging:")
        print(f"  Level: {log_config.get('level')}")
        print(f"  Format: {log_config.get('format')}")
        print(f"  Output: {log_config.get('output')}")
        print(f"  File: {log_config.get('file_path')}")

        self.initialized = True

    def log(self, level, message):
        """Log a message."""
        if not self.initialized:
            self.initialize()

        print(f"[{level}] {message}")


class ApplicationService:
    """Main application service coordinating all services."""

    def __init__(self, config_file=None):
        self.config_manager = ConfigManager(config_file)
        self.db_service = DatabaseService(self.config_manager)
        self.api_service = APIService(self.config_manager)
        self.log_service = LoggingService(self.config_manager)

    def initialize(self):
        """Initialize all application services."""
        print("=== Initializing Application ===\n")

        # Load configuration
        print("Loading configuration...")
        config = self.config_manager.load()
        print(f"Configuration loaded: {self.config_manager.get('app_name')}\n")

        # Initialize logging
        print("Setting up logging...")
        self.log_service.initialize()
        print()

        # Check feature flags
        print("Checking feature flags...")
        metrics_enabled = self.config_manager.is_feature_enabled("enable_metrics")
        tracing_enabled = self.config_manager.is_feature_enabled("enable_tracing")
        print(f"  Metrics: {'enabled' if metrics_enabled else 'disabled'}")
        print(f"  Tracing: {'enabled' if tracing_enabled else 'disabled'}")
        print()

        # Connect to database
        print("Connecting to database...")
        self.db_service.connect()
        print()

        # Start API server
        print("Starting API server...")
        self.api_service.start()
        print()

        print("Application initialized successfully!")

    def shutdown(self):
        """Shutdown all application services."""
        print("\n=== Shutting Down Application ===\n")

        self.api_service.stop()
        self.db_service.disconnect()

        print("Application shutdown complete")
