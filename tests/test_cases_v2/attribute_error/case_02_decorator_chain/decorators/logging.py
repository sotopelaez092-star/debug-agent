from functools import wraps
from typing import Callable
from datetime import datetime
import traceback


class CallLogger:
    _logs: list = []

    @classmethod
    def log(cls, entry: dict) -> None:
        entry["timestamp"] = datetime.now().isoformat()
        cls._logs.append(entry)

    @classmethod
    def get_logs(cls) -> list:
        return cls._logs.copy()

    @classmethod
    def clear(cls) -> None:
        cls._logs = []


def log_call(func: Callable) -> Callable:
    """Decorator that logs function calls."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        CallLogger.log({
            "type": "call",
            "function": func.__name__,
            "args_count": len(args),
            "kwargs_keys": list(kwargs.keys()),
        })
        result = func(*args, **kwargs)
        CallLogger.log({
            "type": "return",
            "function": func.__name__,
            "success": True,
        })
        return result
    wrapper._logged = True
    return wrapper


def log_errors(func: Callable) -> Callable:
    """Decorator that logs errors."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            CallLogger.log({
                "type": "error",
                "function": func.__name__,
                "error": str(e),
                "traceback": traceback.format_exc(),
            })
            raise
    wrapper._error_logged = True
    return wrapper
