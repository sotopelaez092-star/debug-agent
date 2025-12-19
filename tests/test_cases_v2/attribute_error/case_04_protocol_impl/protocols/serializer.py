from typing import Protocol, Any, runtime_checkable


@runtime_checkable
class SerializerProtocol(Protocol):
    """Protocol for serialization backends."""

    def serialize(self, data: Any) -> bytes:
        """Serialize data to bytes."""
        ...

    def deserialize(self, data: bytes) -> Any:
        """Deserialize bytes to data."""
        ...

    @property
    def content_type(self) -> str:
        """Get the content type for this serializer."""
        ...
