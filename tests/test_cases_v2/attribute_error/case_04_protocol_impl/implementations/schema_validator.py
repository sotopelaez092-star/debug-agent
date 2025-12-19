from typing import Any, List, Tuple, Dict


class SchemaValidator:
    """Schema-based data validator."""

    def __init__(self, schema: Dict[str, type]):
        self._schema = schema

    def validate(self, data: Any) -> Tuple[bool, List[str]]:
        errors = []

        if not isinstance(data, dict):
            return False, ["Data must be a dictionary"]

        for field, expected_type in self._schema.items():
            if field not in data:
                errors.append(f"Missing required field: {field}")
            elif not isinstance(data[field], expected_type):
                errors.append(
                    f"Field '{field}': expected {expected_type.__name__}, "
                    f"got {type(data[field]).__name__}"
                )

        # Check for extra fields
        for field in data:
            if field not in self._schema:
                errors.append(f"Unknown field: {field}")

        return len(errors) == 0, errors

    def get_schema(self) -> dict:
        return {k: v.__name__ for k, v in self._schema.items()}
