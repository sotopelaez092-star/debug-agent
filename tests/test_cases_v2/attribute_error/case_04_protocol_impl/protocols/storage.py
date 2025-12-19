from typing import Protocol, Any, Optional, List, runtime_checkable


@runtime_checkable
class StorageProtocol(Protocol):
    """Protocol for storage backends."""

    def save(self, key: str, value: Any) -> bool:
        """Save a value with the given key."""
        ...

    def load(self, key: str) -> Optional[Any]:
        """Load a value by key."""
        ...

    def delete(self, key: str) -> bool:
        """Delete a value by key."""
        ...

    def list_keys(self, prefix: str = "") -> List[str]:
        """List all keys, optionally filtered by prefix."""
        ...

    def exists(self, key: str) -> bool:
        """Check if a key exists."""
        ...
