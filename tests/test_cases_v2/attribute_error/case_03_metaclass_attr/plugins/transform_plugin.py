import json
from typing import Any, Dict
from core import BasePlugin


class TransformPlugin(BasePlugin):
    """Plugin for data transformation."""

    plugin_name = "transform"
    version = "3.0.0"
    author = "data-team"
    dependencies = ["compress", "encrypt"]

    def initialize(self) -> None:
        self.format = self.config.get("format", "json")
        self._initialized = True

    def execute(self, data: Any) -> bytes:
        """Transform the input data to bytes."""
        if not self._initialized:
            raise RuntimeError("Plugin not initialized")
        if self.format == "json":
            return json.dumps(data).encode()
        elif self.format == "str":
            return str(data).encode()
        else:
            raise ValueError(f"Unknown format: {self.format}")

    def reverse(self, data: bytes) -> Any:
        """Reverse the transformation."""
        if self.format == "json":
            return json.loads(data.decode())
        elif self.format == "str":
            return data.decode()
        else:
            raise ValueError(f"Unknown format: {self.format}")
