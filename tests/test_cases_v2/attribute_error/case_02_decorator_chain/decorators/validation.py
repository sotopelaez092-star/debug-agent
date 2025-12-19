from functools import wraps
from typing import Callable, Dict, Any, Type, get_type_hints


class ValidationError(Exception):
    def __init__(self, errors: list):
        self.errors = errors
        super().__init__(f"Validation failed: {errors}")


def validate_input(schema: Dict[str, Type]) -> Callable:
    """Decorator that validates input arguments against a schema."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            errors = []
            for param_name, expected_type in schema.items():
                if param_name in kwargs:
                    value = kwargs[param_name]
                    if not isinstance(value, expected_type):
                        errors.append(
                            f"{param_name}: expected {expected_type.__name__}, "
                            f"got {type(value).__name__}"
                        )
            if errors:
                raise ValidationError(errors)
            return func(*args, **kwargs)
        wrapper._input_schema = schema
        return wrapper
    return decorator


def validate_output(expected_type: Type) -> Callable:
    """Decorator that validates output type."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            if not isinstance(result, expected_type):
                raise ValidationError([
                    f"Return type: expected {expected_type.__name__}, "
                    f"got {type(result).__name__}"
                ])
            return result
        wrapper._output_type = expected_type
        return wrapper
    return decorator
