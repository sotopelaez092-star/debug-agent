from typing import List, Tuple


class Validatable:
    """Interface for validatable objects."""

    def validate(self) -> Tuple[bool, List[str]]:
        """Validate the object and return (is_valid, error_messages)."""
        raise NotImplementedError

    def is_valid(self) -> bool:
        valid, _ = self.validate()
        return valid

    def validation_errors(self) -> List[str]:
        _, errors = self.validate()
        return errors
