"""Base processor interface for data processing pipeline."""
from abc import ABC, abstractmethod


class ProcessorResult:
    """Result of a processing operation."""

    def __init__(self, success, data, errors=None):
        self.success = success
        self.data = data
        self.errors = errors or []

    def __repr__(self):
        return f"ProcessorResult(success={self.success}, errors={len(self.errors)})"


class BaseProcessor(ABC):
    """
    Abstract base class for data processors.

    All processors must implement the process() method with the signature:
    process(data, context) -> ProcessorResult
    """

    def __init__(self, name, config=None):
        self.name = name
        self.config = config or {}
        self.enabled = True

    @abstractmethod
    def process(self, data, context):
        """
        Process data with given context.

        Args:
            data: Input data to process (any type)
            context: Processing context dictionary with metadata

        Returns:
            ProcessorResult: Processing result with success status and output data

        Note:
            This is the standard interface. All derived classes must implement
            this exact signature for polymorphic usage in the pipeline.
        """
        pass

    def validate_input(self, data):
        """Validate input data before processing."""
        if data is None:
            raise ValueError(f"{self.name}: Input data cannot be None")
        return True

    def enable(self):
        """Enable this processor."""
        self.enabled = True

    def disable(self):
        """Disable this processor."""
        self.enabled = False

    def is_enabled(self):
        """Check if processor is enabled."""
        return self.enabled

    def get_info(self):
        """Get processor information."""
        return {
            "name": self.name,
            "type": self.__class__.__name__,
            "enabled": self.enabled,
            "config": self.config,
        }

    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.name}, enabled={self.enabled})"
