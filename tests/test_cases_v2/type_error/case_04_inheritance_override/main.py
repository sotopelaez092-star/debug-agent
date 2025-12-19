"""Test data processing pipeline with processor plugins."""
from runners import Pipeline
from plugins import (
    TextCleanerProcessor,
    TextValidatorProcessor,
    DataTransformerProcessor,
    DataEnricherProcessor,
)


def main():
    print("=== Data Processing Pipeline Test ===\n")

    # Create processors
    cleaner = TextCleanerProcessor({"lowercase": True})
    validator = TextValidatorProcessor({"min_length": 5, "max_length": 100})
    transformer = DataTransformerProcessor({"default_format": "json"})
    enricher = DataEnricherProcessor({"enrichments": {"version": "1.0", "processed": True}})

    # Create pipeline
    pipeline = Pipeline("data_pipeline")
    pipeline.add_processor(cleaner)
    pipeline.add_processor(validator)
    pipeline.add_processor(transformer)  # This will cause TypeError
    pipeline.add_processor(enricher)

    print("Pipeline configuration:")
    for info in pipeline.get_processors():
        print(f"  - {info['name']} ({info['type']})")
    print()

    # Test data
    test_data = "  Hello World from Processing Pipeline!  "

    # Execute pipeline
    # This will trigger TypeError when DataTransformerProcessor.process()
    # is called with only (data, context) but expects (data, context, format)
    try:
        result = pipeline.execute(test_data)

        if result.success:
            print("Pipeline Result:")
            print(f"  Success: {result.success}")
            print(f"  Final data: {result.data}")
            print(f"  Stages completed: {len(result.context['stages'])}")
        else:
            print("Pipeline Failed:")
            print(f"  Failed at: {result.failed_at}")
            print(f"  Error: {result.error}")

    except Exception as e:
        print(f"\nError: {type(e).__name__}: {e}")
        raise


if __name__ == "__main__":
    main()
