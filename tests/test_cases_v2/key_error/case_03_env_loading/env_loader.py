"""
Environment variable loader.
Loads and validates environment variables from .env files.
"""
import os
from typing import Dict, Any, Optional


class EnvLoader:
    """Loads environment variables from files or system."""

    def __init__(self, env_file: Optional[str] = None):
        self.env_file = env_file
        self.env_vars: Dict[str, str] = {}

    def load_from_file(self) -> Dict[str, str]:
        """Load environment variables from .env file."""
        if not self.env_file or not os.path.exists(self.env_file):
            return {}

        env_vars = {}
        with open(self.env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()

        self.env_vars = env_vars
        return env_vars

    def load_from_system(self) -> Dict[str, str]:
        """Load environment variables from system."""
        self.env_vars = dict(os.environ)
        return self.env_vars

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get environment variable value."""
        return self.env_vars.get(key, default)

    def require(self, key: str) -> str:
        """Get required environment variable, raise if missing."""
        value = self.env_vars.get(key)
        if value is None:
            raise KeyError(f"Required environment variable not found: {key}")
        return value

    def get_all(self) -> Dict[str, str]:
        """Get all loaded environment variables."""
        return self.env_vars.copy()
