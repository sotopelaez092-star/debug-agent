"""Text processing plugin."""
from core import BaseProcessor, ProcessorResult


class TextCleanerProcessor(BaseProcessor):
    """Clean and normalize text data."""

    def __init__(self, config=None):
        super().__init__("text_cleaner", config)

    def process(self, data, context):
        """
        Clean text data by removing extra whitespace and normalizing.

        Args:
            data: Text string to clean
            context: Processing context

        Returns:
            ProcessorResult with cleaned text
        """
        self.validate_input(data)

        if not isinstance(data, str):
            return ProcessorResult(
                success=False,
                data=data,
                errors=["Input must be a string"]
            )

        # Clean the text
        cleaned = data.strip()
        cleaned = ' '.join(cleaned.split())  # Normalize whitespace

        # Apply case transformation if configured
        if self.config.get("lowercase", False):
            cleaned = cleaned.lower()
        elif self.config.get("uppercase", False):
            cleaned = cleaned.upper()

        context["cleaned"] = True
        context["original_length"] = len(data)
        context["cleaned_length"] = len(cleaned)

        return ProcessorResult(success=True, data=cleaned)


class TextValidatorProcessor(BaseProcessor):
    """Validate text data against rules."""

    def __init__(self, config=None):
        super().__init__("text_validator", config)

    def process(self, data, context):
        """
        Validate text data.

        Args:
            data: Text string to validate
            context: Processing context

        Returns:
            ProcessorResult with validation status
        """
        self.validate_input(data)

        if not isinstance(data, str):
            return ProcessorResult(
                success=False,
                data=data,
                errors=["Input must be a string"]
            )

        errors = []

        # Check minimum length
        min_length = self.config.get("min_length", 0)
        if len(data) < min_length:
            errors.append(f"Text must be at least {min_length} characters")

        # Check maximum length
        max_length = self.config.get("max_length", float('inf'))
        if len(data) > max_length:
            errors.append(f"Text must be at most {max_length} characters")

        # Check for required patterns
        required_words = self.config.get("required_words", [])
        for word in required_words:
            if word.lower() not in data.lower():
                errors.append(f"Text must contain '{word}'")

        context["validated"] = len(errors) == 0
        context["validation_errors"] = errors

        return ProcessorResult(
            success=len(errors) == 0,
            data=data,
            errors=errors
        )
