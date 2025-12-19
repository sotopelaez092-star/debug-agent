"""
Data processing utilities for ETL pipeline.
This module was recently refactored to use clearer naming conventions.
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def validate_input_data(data: List[Dict[str, Any]]) -> bool:
    """Validate input data structure."""
    if not isinstance(data, list):
        return False

    for item in data:
        if not isinstance(item, dict):
            return False
        if 'id' not in item or 'value' not in item:
            return False

    return True


def transform_data_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transform data records with new naming convention.
    RENAMED FROM: process_data (old name deprecated)
    """
    logger.info(f"Transforming {len(records)} records")

    transformed = []
    for record in records:
        transformed_record = {
            'record_id': record.get('id'),
            'processed_value': record.get('value', 0) * 2,
            'metadata': {
                'source': 'etl_pipeline',
                'transformed': True
            }
        }
        transformed.append(transformed_record)

    return transformed


def aggregate_results(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate processed results."""
    total_value = sum(item.get('processed_value', 0) for item in data)

    return {
        'total_records': len(data),
        'total_value': total_value,
        'average_value': total_value / len(data) if data else 0
    }


def save_to_database(data: List[Dict[str, Any]], table: str) -> bool:
    """Save processed data to database."""
    logger.info(f"Saving {len(data)} records to {table}")
    # Simulate database save
    return True
