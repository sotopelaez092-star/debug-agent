"""
Request handling module.
Processes requests and manages request lifecycle.
"""

import logging
from typing import Dict, Any, Optional
import state_manager

logger = logging.getLogger(__name__)

# Module-level variables for request context
current_request_id = None
current_user_id = None


def set_request_context(request_id: str, user_id: int):
    """Set the current request context."""
    global current_request_id, current_user_id

    current_request_id = request_id
    current_user_id = user_id

    logger.debug(f"Request context set: {request_id} for user {user_id}")


def get_request_context() -> Dict[str, Any]:
    """Get the current request context."""
    return {
        'request_id': current_request_id,
        'user_id': current_user_id
    }


def clear_request_context():
    """Clear the current request context."""
    global current_request_id, current_user_id

    current_request_id = None
    current_user_id = None

    logger.debug("Request context cleared")


class RequestProcessor:
    """Processes incoming requests."""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.RequestProcessor")

    def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a request and return response."""
        request_id = request_data.get('request_id', 'unknown')
        user_id = request_data.get('user_id', 0)

        self.logger.info(f"Processing request {request_id}")

        # Set request context
        set_request_context(request_id, user_id)

        try:
            # Increment request counter
            state_manager.increment_request_count()

            # Process the request
            response = self._handle_request(request_data)

            return response

        except Exception as e:
            state_manager.record_error(e)
            raise

        finally:
            clear_request_context()

    def _handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Internal request handling logic."""
        action = request_data.get('action', 'unknown')

        if action == 'get_status':
            return self._get_status()
        elif action == 'update_config':
            return self._update_config(request_data)
        elif action == 'process_data':
            return self._process_data(request_data)
        else:
            raise ValueError(f"Unknown action: {action}")

    def _get_status(self) -> Dict[str, Any]:
        """Get application status."""
        context = get_request_context()

        return {
            'status': 'ok',
            'request_id': context['request_id'],
            'state': state_manager.get_state(),
            'uptime': state_manager.get_uptime()
        }

    def _update_config(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update configuration."""
        config_updates = request_data.get('config', {})

        for key, value in config_updates.items():
            state_manager.update_config(key, value)

        context = get_request_context()

        return {
            'status': 'updated',
            'request_id': context['request_id'],
            'config': state_manager.get_config()
        }

    def _process_data(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process data with retries."""
        data = request_data.get('data', [])
        context = get_request_context()

        self.logger.info(f"Processing {len(data)} items for request {context['request_id']}")

        # Get retry configuration
        config = state_manager.get_config()
        max_retries = config['max_retries']

        # Process with retries
        result = self._process_with_retry(data, max_retries)

        return {
            'status': 'processed',
            'request_id': context['request_id'],
            'result': result
        }

    def _process_with_retry(self, data: list, max_retries: int) -> Dict[str, Any]:
        """
        Process data with retry logic.

        This function has a scope issue: it tries to use 'attempt' variable
        that should be declared in the outer scope, but is shadowed.
        """
        attempt = 0  # Local variable in outer scope

        def try_process():
            """Inner function that tries to process data."""
            self.logger.info(f"Processing attempt {attempt + 1}/{max_retries + 1}")

            # Simulate processing
            processed_count = 0

            for item in data:
                # Simulate some processing
                processed_count += 1

            # Increment attempt counter
            # BUG: This tries to reference 'attempt' from outer scope
            # but will fail because of Python's scoping rules
            attempt = attempt + 1

            return {
                'processed': processed_count,
                'attempts': attempt
            }

        # Try processing with retries
        last_error = None

        while attempt <= max_retries:
            try:
                return try_process()
            except Exception as e:
                last_error = e
                self.logger.warning(f"Attempt {attempt + 1} failed: {e}")
                attempt += 1

        # All retries exhausted
        raise Exception(f"Processing failed after {max_retries + 1} attempts: {last_error}")
