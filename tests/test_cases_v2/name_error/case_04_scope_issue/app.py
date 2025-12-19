"""
Main application module.
"""

import logging
from typing import Dict, Any
import state_manager
from request_handler import RequestProcessor
from middleware import MiddlewareChain, LoggingMiddleware, AuthenticationMiddleware, ErrorHandlingMiddleware

logger = logging.getLogger(__name__)


class Application:
    """Main application class."""

    def __init__(self):
        self.processor = RequestProcessor()
        self.middleware = self._setup_middleware()
        logger.info("Application initialized")

    def _setup_middleware(self) -> MiddlewareChain:
        """Setup middleware chain."""
        chain = MiddlewareChain()

        chain.add(ErrorHandlingMiddleware())
        chain.add(LoggingMiddleware())
        chain.add(AuthenticationMiddleware())

        return chain

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an incoming request."""
        return self.middleware.process(request, self.processor.process_request)

    def start(self):
        """Start the application."""
        state_manager.initialize_state()
        logger.info("Application started")

    def get_stats(self) -> Dict[str, Any]:
        """Get application statistics."""
        state = state_manager.get_state()
        config = state_manager.get_config()

        return {
            'state': state,
            'config': config,
            'uptime': state_manager.get_uptime()
        }
