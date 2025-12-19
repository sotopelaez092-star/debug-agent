"""
Utility functions for the ETL pipeline.
"""

import json
from typing import List, Dict, Any
from datetime import datetime


def load_data_from_file(filepath: str) -> List[Dict[str, Any]]:
    """Load data from a JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def save_data_to_file(data: Any, filepath: str):
    """Save data to a JSON file."""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)


def generate_report(results: Dict[str, Any]) -> str:
    """Generate a text report from results."""
    report = []
    report.append("=" * 50)
    report.append("ETL Pipeline Execution Report")
    report.append("=" * 50)
    report.append(f"Generated: {datetime.now().isoformat()}")
    report.append("")

    if 'total_records' in results:
        report.append(f"Total Records Processed: {results['total_records']}")
    if 'total_value' in results:
        report.append(f"Total Value: {results['total_value']}")
    if 'average_value' in results:
        report.append(f"Average Value: {results['average_value']:.2f}")

    report.append("=" * 50)

    return "\n".join(report)


def validate_file_path(filepath: str) -> bool:
    """Validate that a file path exists and is readable."""
    import os
    return os.path.exists(filepath) and os.path.isfile(filepath)
