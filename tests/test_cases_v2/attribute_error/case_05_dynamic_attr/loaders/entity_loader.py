from typing import Dict, Any, Type
from models import EntityModel


class EntityLoader:
    """Loader for entity models from dictionaries."""

    def __init__(self, entity_class: Type[EntityModel] = EntityModel):
        self._entity_class = entity_class

    def load(self, data: Dict[str, Any]) -> EntityModel:
        """Load an entity from dictionary data."""
        entity_id = data.get("id", "unknown")
        attributes = data.get("attributes", {})

        entity = self._entity_class(entity_id, **attributes)
        return entity

    def load_many(self, data_list: list) -> list:
        """Load multiple entities."""
        return [self.load(data) for data in data_list]

    def dump(self, entity: EntityModel) -> Dict[str, Any]:
        """Dump an entity to dictionary."""
        return entity.to_dict()

    def dump_many(self, entities: list) -> list:
        """Dump multiple entities."""
        return [self.dump(e) for e in entities]
