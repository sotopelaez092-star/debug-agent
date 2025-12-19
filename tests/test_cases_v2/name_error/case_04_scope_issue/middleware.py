"""
Middleware for request processing.
Handles authentication, logging, and error handling.
"""

import logging
from typing import Dict, Any, Callable
import state_manager

logger = logging.getLogger(__name__)


class Middleware:
    """Base middleware class."""

    def process(self, request: Dict[str, Any], next_handler: Callable) -> Dict[str, Any]:
        """Process request and call next handler."""
        raise NotImplementedError


class LoggingMiddleware(Middleware):
    """Logs all requests and responses."""

    def process(self, request: Dict[str, Any], next_handler: Callable) -> Dict[str, Any]:
        """Process with logging."""
        request_id = request.get('request_id', 'unknown')

        logger.info(f"[{request_id}] Request received: {request.get('action')}")

        try:
            response = next_handler(request)
            logger.info(f"[{request_id}] Request completed: {response.get('status')}")
            return response

        except Exception as e:
            logger.error(f"[{request_id}] Request failed: {e}")
            raise


class AuthenticationMiddleware(Middleware):
    """Authenticates requests."""

    def process(self, request: Dict[str, Any], next_handler: Callable) -> Dict[str, Any]:
        """Process with authentication."""
        user_id = request.get('user_id')

        if user_id is None or user_id == 0:
            raise ValueError("User authentication required")

        # Simulate authentication check
        if user_id < 0:
            raise ValueError("Invalid user ID")

        logger.debug(f"User {user_id} authenticated")

        return next_handler(request)


class ErrorHandlingMiddleware(Middleware):
    """Handles errors and records them."""

    def process(self, request: Dict[str, Any], next_handler: Callable) -> Dict[str, Any]:
        """Process with error handling."""
        try:
            return next_handler(request)

        except Exception as e:
            # Record error in state
            state_manager.record_error(e)

            # Return error response
            return {
                'status': 'error',
                'request_id': request.get('request_id', 'unknown'),
                'error': {
                    'type': type(e).__name__,
                    'message': str(e)
                }
            }


class MiddlewareChain:
    """Chains multiple middleware together."""

    def __init__(self):
        self.middlewares = []

    def add(self, middleware: Middleware):
        """Add middleware to the chain."""
        self.middlewares.append(middleware)

    def process(self, request: Dict[str, Any], final_handler: Callable) -> Dict[str, Any]:
        """Process request through middleware chain."""

        def build_chain(index: int) -> Callable:
            """Build the middleware chain recursively."""
            if index >= len(self.middlewares):
                return final_handler

            middleware = self.middlewares[index]
            next_handler = build_chain(index + 1)

            return lambda req: middleware.process(req, next_handler)

        chain = build_chain(0)
        return chain(request)
