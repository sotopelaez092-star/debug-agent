"""Pipeline runner for executing processor chains."""
from core import BaseProcessor, ProcessorResult


class Pipeline:
    """Execute a chain of processors."""

    def __init__(self, name, processors=None):
        self.name = name
        self.processors = processors or []

    def add_processor(self, processor):
        """Add a processor to the pipeline."""
        if not isinstance(processor, BaseProcessor):
            raise TypeError("Processor must inherit from BaseProcessor")
        self.processors.append(processor)

    def remove_processor(self, processor_name):
        """Remove a processor from the pipeline."""
        self.processors = [p for p in self.processors if p.name != processor_name]

    def execute(self, initial_data):
        """
        Execute the pipeline on input data.

        Args:
            initial_data: Initial input data

        Returns:
            PipelineResult with final data and execution details
        """
        context = {
            "pipeline": self.name,
            "stages": [],
        }

        current_data = initial_data
        results = []

        print(f"Executing pipeline: {self.name}")
        print(f"Initial data: {current_data}")
        print(f"Processors: {len(self.processors)}\n")

        for i, processor in enumerate(self.processors):
            if not processor.is_enabled():
                print(f"[{i+1}] Skipping {processor.name} (disabled)")
                continue

            print(f"[{i+1}] Running {processor.name}...")

            try:
                # BUG: This polymorphic call assumes all processors follow
                # the base interface: process(data, context)
                # DataTransformerProcessor has incompatible signature with 'format' parameter
                result = processor.process(current_data, context)

                if result.success:
                    current_data = result.data
                    print(f"     Success: {result}")
                else:
                    print(f"     Failed: {result}")
                    print(f"     Errors: {result.errors}")
                    return PipelineResult(
                        success=False,
                        data=current_data,
                        context=context,
                        failed_at=processor.name,
                        error=result.errors
                    )

                results.append({
                    "processor": processor.name,
                    "success": result.success,
                    "result": result,
                })

                context["stages"].append({
                    "processor": processor.name,
                    "success": result.success,
                })

            except Exception as e:
                print(f"     Exception: {type(e).__name__}: {e}")
                return PipelineResult(
                    success=False,
                    data=current_data,
                    context=context,
                    failed_at=processor.name,
                    error=str(e)
                )

        print(f"\nPipeline completed successfully")
        print(f"Final data: {current_data}\n")

        return PipelineResult(
            success=True,
            data=current_data,
            context=context,
            failed_at=None,
            error=None
        )

    def get_processors(self):
        """Get list of processors in pipeline."""
        return [p.get_info() for p in self.processors]


class PipelineResult:
    """Result of pipeline execution."""

    def __init__(self, success, data, context, failed_at=None, error=None):
        self.success = success
        self.data = data
        self.context = context
        self.failed_at = failed_at
        self.error = error

    def __repr__(self):
        if self.success:
            return f"PipelineResult(success=True, stages={len(self.context['stages'])})"
        else:
            return f"PipelineResult(success=False, failed_at={self.failed_at})"
