from typing import Any, Optional, List
from protocols import StorageProtocol, SerializerProtocol, ValidatorProtocol


class StorageAdapter:
    """Adapter that combines storage, serializer, and validator."""

    def __init__(
        self,
        storage: StorageProtocol,
        serializer: SerializerProtocol,
        validator: Optional[ValidatorProtocol] = None
    ):
        self._storage = storage
        self._serializer = serializer
        self._validator = validator

    def save(self, key: str, data: Any) -> bool:
        """Save data with validation and serialization."""
        # Validate if validator is set
        if self._validator:
            is_valid, errors = self._validator.validate(data)
            if not is_valid:
                raise ValueError(f"Validation failed: {errors}")

        # Serialize and save
        serialized = self._serializer.serialize(data)
        return self._storage.save(key, serialized)

    def load(self, key: str) -> Optional[Any]:
        """Load and deserialize data."""
        raw = self._storage.load(key)
        if raw is None:
            return None
        return self._serializer.deserialize(raw)

    def delete(self, key: str) -> bool:
        """Delete data by key."""
        return self._storage.delete(key)

    def list_keys(self, prefix: str = "") -> List[str]:
        """List all keys with optional prefix filter."""
        return self._storage.list_keys(prefix)

    def exists(self, key: str) -> bool:
        """Check if key exists."""
        return self._storage.exists(key)

    def get_content_type(self) -> str:
        """Get the serializer's content type."""
        # BUG: Typo - should be content_type not contentype
        return self._serializer.contentype

    def get_schema(self) -> Optional[dict]:
        """Get the validator's schema if available."""
        if self._validator:
            return self._validator.get_schema()
        return None
