"""
Main entry point for the ETL pipeline.
"""

import sys
from config import get_pipeline_config, setup_logging
from pipeline_manager import PipelineManager, ValidationStage, TransformationStage, AggregationStage
from utils import generate_report


def main():
    """Run the ETL pipeline."""
    # Setup
    config = get_pipeline_config()
    setup_logging(config)

    # Sample data
    input_data = [
        {'id': 1, 'value': 100},
        {'id': 2, 'value': 200},
        {'id': 3, 'value': 150},
        {'id': 4, 'value': 300},
    ]

    # Create pipeline
    pipeline = PipelineManager()

    if config.enable_validation:
        pipeline.add_stage(ValidationStage("validation"))

    if config.enable_transformation:
        pipeline.add_stage(TransformationStage("transformation"))

    pipeline.add_stage(AggregationStage("aggregation"))

    # Run pipeline
    try:
        results = pipeline.run(input_data)

        # Generate and print report
        report = generate_report(results)
        print(report)

        return 0
    except Exception as e:
        print(f"Pipeline failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
