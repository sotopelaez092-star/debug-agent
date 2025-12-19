from typing import Callable
from decorators.auth import AuthContext


class RequestMiddleware:
    """Middleware for handling request context."""

    def __init__(self, handler: Callable):
        self.handler = handler

    def __call__(self, request: dict):
        # Set up auth context if user is in request
        if "user" in request:
            AuthContext.set_user(request["user"])

        try:
            return self.handler(request)
        finally:
            AuthContext.clear()
