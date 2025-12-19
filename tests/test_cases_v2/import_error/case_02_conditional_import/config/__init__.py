"""
Configuration module with environment-specific imports.
"""

import os
import sys

# Get environment from env variable
ENVIRONMENT = os.getenv('APP_ENV', 'development')


def load_config():
    """Load configuration based on environment."""
    if ENVIRONMENT == 'production':
        from .production_config import ProductionConfig
        return ProductionConfig()
    elif ENVIRONMENT == 'staging':
        from .staging_config import StagingConfig
        return StagingConfig()
    elif ENVIRONMENT == 'development':
        from .dev_config import DevelopmentConfig
        return DevelopmentConfig()
    else:
        raise ValueError(f"Unknown environment: {ENVIRONMENT}")


# This is the problematic import - tries to import based on runtime condition
# but the module name has a typo
if ENVIRONMENT == 'testing':
    from .test_config import TestConfig  # This file doesn't exist - should be testing_config
    config = TestConfig()
else:
    config = load_config()
