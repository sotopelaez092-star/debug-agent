from typing import Any
import pickle


class PickleSerializer:
    """Pickle serialization implementation."""

    def serialize(self, data: Any) -> bytes:
        return pickle.dumps(data)

    def deserialize(self, data: bytes) -> Any:
        return pickle.loads(data)

    @property
    def content_type(self) -> str:
        return "application/octet-stream"
