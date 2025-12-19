from typing import Any, Dict, List, Optional
from datetime import datetime
from .dynamic_model import DynamicModel


class EntityModel(DynamicModel):
    """Entity model with lifecycle hooks and relationships."""

    def __init__(self, entity_id: str, **kwargs):
        super().__init__(**kwargs)
        self._entity_id = entity_id
        self._created_at = datetime.now()
        self._updated_at = datetime.now()
        self._relations: Dict[str, List['EntityModel']] = {}
        self._hooks: Dict[str, List[callable]] = {}

    @property
    def entity_id(self) -> str:
        return self._entity_id

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    def add_relation(self, relation_type: str, entity: 'EntityModel') -> None:
        """Add a relationship to another entity."""
        if relation_type not in self._relations:
            self._relations[relation_type] = []
        self._relations[relation_type].append(entity)
        self._trigger_hook("on_relation_added", relation_type, entity)

    def get_relations(self, relation_type: str) -> List['EntityModel']:
        """Get related entities by type."""
        return self._relations.get(relation_type, [])

    def add_hook(self, event: str, callback: callable) -> None:
        """Add a lifecycle hook."""
        if event not in self._hooks:
            self._hooks[event] = []
        self._hooks[event].append(callback)

    def _trigger_hook(self, event: str, *args, **kwargs) -> None:
        """Trigger all callbacks for an event."""
        for callback in self._hooks.get(event, []):
            callback(self, *args, **kwargs)

    def update(self, **kwargs) -> None:
        """Update entity attributes."""
        self._trigger_hook("before_update", kwargs)
        for key, value in kwargs.items():
            setattr(self, key, value)
        self._updated_at = datetime.now()
        self._trigger_hook("after_update", kwargs)

    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary."""
        return {
            "id": self._entity_id,
            "created_at": self._created_at.isoformat(),
            "updated_at": self._updated_at.isoformat(),
            "attributes": self.get_attributes(),
            "relations": {k: [e.entity_id for e in v] for k, v in self._relations.items()},
        }
