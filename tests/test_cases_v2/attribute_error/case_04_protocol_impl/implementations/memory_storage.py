from typing import Any, Optional, List, Dict


class MemoryStorage:
    """In-memory storage implementation."""

    def __init__(self):
        self._data: Dict[str, Any] = {}

    def save(self, key: str, value: Any) -> bool:
        self._data[key] = value
        return True

    def load(self, key: str) -> Optional[Any]:
        return self._data.get(key)

    def delete(self, key: str) -> bool:
        if key in self._data:
            del self._data[key]
            return True
        return False

    def list_keys(self, prefix: str = "") -> List[str]:
        return [k for k in self._data.keys() if k.startswith(prefix)]

    def exists(self, key: str) -> bool:
        return key in self._data

    def clear(self) -> None:
        self._data.clear()
