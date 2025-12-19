"""
Application state management module.
Manages global application state and configuration.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Global state dictionary
app_state = {
    'initialized': False,
    'start_time': None,
    'request_count': 0,
    'error_count': 0,
    'last_error': None,
}

# Global configuration
app_config = {
    'max_retries': 3,
    'timeout': 30,
    'debug': False,
    'enable_cache': True,
}


def initialize_state():
    """Initialize the application state."""
    # This function modifies global state
    app_state['initialized'] = True
    app_state['start_time'] = datetime.now()
    app_state['request_count'] = 0
    app_state['error_count'] = 0

    logger.info(f"Application state initialized at {app_state['start_time']}")


def get_state() -> Dict[str, Any]:
    """Get the current application state."""
    return app_state.copy()


def get_config() -> Dict[str, Any]:
    """Get the current configuration."""
    return app_config.copy()


def update_config(key: str, value: Any):
    """Update a configuration value."""
    app_config[key] = value
    logger.info(f"Configuration updated: {key} = {value}")


def increment_request_count():
    """Increment the request counter."""
    app_state['request_count'] += 1


def record_error(error: Exception):
    """Record an error in the application state."""
    app_state['error_count'] += 1
    app_state['last_error'] = {
        'type': type(error).__name__,
        'message': str(error),
        'timestamp': datetime.now()
    }
    logger.error(f"Error recorded: {error}")


def get_uptime() -> Optional[float]:
    """Get application uptime in seconds."""
    if not app_state['initialized'] or app_state['start_time'] is None:
        return None

    delta = datetime.now() - app_state['start_time']
    return delta.total_seconds()
