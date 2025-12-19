"""
Pipeline management module.
Coordinates the ETL workflow across different stages.
"""

import logging
from typing import List, Dict, Any
from data_processor import validate_input_data, aggregate_results, save_to_database

logger = logging.getLogger(__name__)


class PipelineStage:
    """Base class for pipeline stages."""

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")

    def execute(self, data: Any) -> Any:
        raise NotImplementedError


class ValidationStage(PipelineStage):
    """Validation stage of the pipeline."""

    def execute(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        self.logger.info("Validating input data")

        if not validate_input_data(data):
            raise ValueError("Invalid input data format")

        return data


class TransformationStage(PipelineStage):
    """Transformation stage of the pipeline."""

    def execute(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        self.logger.info("Transforming data")
        # This import is done here to avoid circular dependencies
        from data_processor import process_data

        return process_data(data)


class AggregationStage(PipelineStage):
    """Aggregation stage of the pipeline."""

    def execute(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        self.logger.info("Aggregating results")
        return aggregate_results(data)


class PipelineManager:
    """Manages the complete ETL pipeline."""

    def __init__(self):
        self.stages = []
        self.logger = logging.getLogger(__name__)

    def add_stage(self, stage: PipelineStage):
        """Add a stage to the pipeline."""
        self.stages.append(stage)

    def run(self, input_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute the complete pipeline."""
        self.logger.info(f"Starting pipeline with {len(self.stages)} stages")

        current_data = input_data

        for stage in self.stages:
            self.logger.info(f"Executing stage: {stage.name}")
            current_data = stage.execute(current_data)

        return current_data
