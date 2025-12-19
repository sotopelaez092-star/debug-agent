import base64
from typing import Any, Dict
from core import BasePlugin


class EncryptPlugin(BasePlugin):
    """Plugin for data encryption (simple XOR for demo)."""

    plugin_name = "encrypt"
    version = "1.5.0"
    author = "security-team"
    dependencies = ["compress"]

    def initialize(self) -> None:
        self.key = self.config.get("key", "default-key")
        self._initialized = True

    def execute(self, data: bytes) -> bytes:
        """Encrypt the input data."""
        if not self._initialized:
            raise RuntimeError("Plugin not initialized")
        key_bytes = self.key.encode()
        encrypted = bytes(
            data[i] ^ key_bytes[i % len(key_bytes)]
            for i in range(len(data))
        )
        return base64.b64encode(encrypted)

    def decrypt(self, data: bytes) -> bytes:
        """Decrypt the input data."""
        decoded = base64.b64decode(data)
        key_bytes = self.key.encode()
        return bytes(
            decoded[i] ^ key_bytes[i % len(key_bytes)]
            for i in range(len(decoded))
        )
