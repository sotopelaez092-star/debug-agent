from typing import List, Tuple, Dict, Any
from models import EntityModel


class EntityValidator:
    """Validator for entity models."""

    def __init__(self, required_attrs: List[str] = None):
        self._required_attrs = required_attrs or []

    def validate(self, entity: EntityModel) -> Tuple[bool, List[str]]:
        """Validate an entity."""
        errors = []

        # Check required attributes
        for attr in self._required_attrs:
            # BUG: Typo - should be has_attribute not has_attr
            if not entity.has_attr(attr):
                errors.append(f"Missing required attribute: {attr}")

        return len(errors) == 0, errors

    def validate_many(self, entities: List[EntityModel]) -> Dict[str, Tuple[bool, List[str]]]:
        """Validate multiple entities."""
        results = {}
        for entity in entities:
            results[entity.entity_id] = self.validate(entity)
        return results
