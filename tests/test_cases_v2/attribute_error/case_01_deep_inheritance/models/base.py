from typing import List, Tuple, Optional
from interfaces import Serializable, Cacheable, Validatable
from mixins import TimestampMixin, AuditMixin


class BaseEntity(Serializable, Cacheable, Validatable, TimestampMixin, AuditMixin):
    """Base entity with all standard interfaces and mixins."""

    def __init__(self, entity_id: str):
        self.entity_id = entity_id
        self._audit_log = []
        self.mark_created()

    def to_dict(self) -> dict:
        return {
            "entity_id": self.entity_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict):
        instance = cls(data["entity_id"])
        return instance

    def cache_key(self) -> str:
        return f"{self.__class__.__name__}:{self.entity_id}"

    def validate(self) -> Tuple[bool, List[str]]:
        errors = []
        if not self.entity_id:
            errors.append("entity_id is required")
        return len(errors) == 0, errors
