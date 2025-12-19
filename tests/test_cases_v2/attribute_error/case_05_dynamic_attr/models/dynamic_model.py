from typing import Any, Dict, Set


class DynamicModel:
    """Base model with dynamic attribute support via __getattr__."""

    _protected_attrs: Set[str] = {"_data", "_protected_attrs", "_validators"}

    def __init__(self, **kwargs):
        self._data: Dict[str, Any] = {}
        self._validators: Dict[str, callable] = {}
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        if name in self._data:
            return self._data[name]
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_") or name in self._protected_attrs:
            super().__setattr__(name, value)
        else:
            # Run validator if exists
            if hasattr(self, "_validators") and name in self._validators:
                validator = self._validators[name]
                if not validator(value):
                    raise ValueError(f"Validation failed for '{name}'")
            self._data[name] = value

    def __delattr__(self, name: str) -> None:
        if name in self._data:
            del self._data[name]
        else:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def add_validator(self, attr: str, validator: callable) -> None:
        """Add a validator for an attribute."""
        self._validators[attr] = validator

    def get_attributes(self) -> Dict[str, Any]:
        """Get all dynamic attributes."""
        return self._data.copy()

    def has_attribute(self, name: str) -> bool:
        """Check if dynamic attribute exists."""
        return name in self._data
