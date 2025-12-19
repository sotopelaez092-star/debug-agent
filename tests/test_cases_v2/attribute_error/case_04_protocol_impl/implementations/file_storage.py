from typing import Any, Optional, List
from pathlib import Path
import os


class FileStorage:
    """File-based storage implementation."""

    def __init__(self, base_path: str = "/tmp/storage"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_path(self, key: str) -> Path:
        # Sanitize key for filesystem
        safe_key = key.replace("/", "_").replace("\\", "_")
        return self.base_path / safe_key

    def save(self, key: str, value: Any) -> bool:
        path = self._get_path(key)
        path.write_bytes(value if isinstance(value, bytes) else str(value).encode())
        return True

    def load(self, key: str) -> Optional[Any]:
        path = self._get_path(key)
        if not path.exists():
            return None
        return path.read_bytes()

    def delete(self, key: str) -> bool:
        path = self._get_path(key)
        if path.exists():
            path.unlink()
            return True
        return False

    def list_keys(self, prefix: str = "") -> List[str]:
        return [f.name for f in self.base_path.iterdir() if f.name.startswith(prefix)]

    def exists(self, key: str) -> bool:
        return self._get_path(key).exists()
