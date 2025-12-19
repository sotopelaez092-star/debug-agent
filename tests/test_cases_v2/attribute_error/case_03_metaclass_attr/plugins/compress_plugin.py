import zlib
from typing import Any, Dict
from core import BasePlugin


class CompressPlugin(BasePlugin):
    """Plugin for data compression."""

    plugin_name = "compress"
    version = "2.1.0"
    author = "data-team"
    dependencies = []

    def initialize(self) -> None:
        self.compression_level = self.config.get("level", 6)
        self._initialized = True

    def execute(self, data: bytes) -> bytes:
        """Compress the input data."""
        if not self._initialized:
            raise RuntimeError("Plugin not initialized")
        return zlib.compress(data, level=self.compression_level)

    def decompress(self, data: bytes) -> bytes:
        """Decompress the input data."""
        return zlib.decompress(data)
