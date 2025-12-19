from typing import Any
import json


class JsonSerializer:
    """JSON serialization implementation."""

    def serialize(self, data: Any) -> bytes:
        return json.dumps(data, indent=2).encode("utf-8")

    def deserialize(self, data: bytes) -> Any:
        return json.loads(data.decode("utf-8"))

    @property
    def content_type(self) -> str:
        return "application/json"
