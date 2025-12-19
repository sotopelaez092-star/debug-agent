from typing import Protocol, Any, List, Tuple, runtime_checkable


@runtime_checkable
class ValidatorProtocol(Protocol):
    """Protocol for data validators."""

    def validate(self, data: Any) -> Tuple[bool, List[str]]:
        """Validate data and return (is_valid, errors)."""
        ...

    def get_schema(self) -> dict:
        """Get the validation schema."""
        ...
