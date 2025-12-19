"""Data transformation processors."""
from core import BaseProcessor, ProcessorResult


class DataTransformerProcessor(BaseProcessor):
    """Transform data between formats."""

    def __init__(self, config=None):
        super().__init__("data_transformer", config)

    def process(self, data, context, format="json"):
        """
        Transform data to specified format.

        Args:
            data: Input data to transform
            context: Processing context
            format: Target format (json, xml, csv) - NEW PARAMETER

        Returns:
            ProcessorResult with transformed data

        Note:
            BUG: This override has incompatible signature!
            Base class: process(data, context)
            This class: process(data, context, format="json")

            The additional 'format' parameter breaks the Liskov Substitution Principle.
            When called polymorphically through BaseProcessor interface,
            the format parameter won't be passed, causing TypeError.
        """
        self.validate_input(data)

        # Transform based on format
        if format == "json":
            import json
            try:
                if isinstance(data, str):
                    # Parse JSON string
                    result = json.loads(data)
                else:
                    # Convert to JSON
                    result = json.dumps(data)
            except json.JSONDecodeError as e:
                return ProcessorResult(
                    success=False,
                    data=data,
                    errors=[f"JSON transformation failed: {e}"]
                )

        elif format == "xml":
            # Simplified XML conversion
            if isinstance(data, dict):
                result = "<data>"
                for key, value in data.items():
                    result += f"<{key}>{value}</{key}>"
                result += "</data>"
            else:
                result = f"<data>{data}</data>"

        elif format == "csv":
            # Simplified CSV conversion
            if isinstance(data, list):
                result = ",".join(str(item) for item in data)
            else:
                result = str(data)

        else:
            return ProcessorResult(
                success=False,
                data=data,
                errors=[f"Unsupported format: {format}"]
            )

        context["transformed"] = True
        context["target_format"] = format

        return ProcessorResult(success=True, data=result)


class DataEnricherProcessor(BaseProcessor):
    """Enrich data with additional information."""

    def __init__(self, config=None):
        super().__init__("data_enricher", config)

    def process(self, data, context):
        """
        Enrich data with metadata and additional fields.

        Args:
            data: Input data to enrich
            context: Processing context

        Returns:
            ProcessorResult with enriched data
        """
        self.validate_input(data)

        if not isinstance(data, dict):
            return ProcessorResult(
                success=False,
                data=data,
                errors=["Input must be a dictionary"]
            )

        # Enrich with metadata
        enriched = data.copy()
        enriched["_metadata"] = {
            "processor": self.name,
            "context": context.copy(),
            "enriched_fields": []
        }

        # Add configured enrichments
        enrichments = self.config.get("enrichments", {})
        for field, value in enrichments.items():
            enriched[field] = value
            enriched["_metadata"]["enriched_fields"].append(field)

        context["enriched"] = True
        context["fields_added"] = len(enrichments)

        return ProcessorResult(success=True, data=enriched)
