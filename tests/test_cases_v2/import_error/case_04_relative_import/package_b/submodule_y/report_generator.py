"""
Report generator in submodule Y.
"""

# Problematic relative import - trying to go up to package_a from package_b
# This won't work because package_a and package_b are siblings
from ...package_a.utilities import serialize_data
from ...package_a.constants import VERSION, APP_NAME
from ..helpers import format_output, log_message


class ReportGenerator:
    """Generate reports from processed data."""

    def __init__(self):
        self.reports = []

    def generate_report(self, title, data):
        """Generate a report with the given title and data."""
        log_message(f"Generating report: {title}")

        report = {
            "title": title,
            "app_name": APP_NAME,
            "app_version": VERSION,
            "data": data
        }

        # Serialize the report
        serialized = serialize_data(report)
        self.reports.append(serialized)

        return serialized

    def export_all(self, format_type="json"):
        """Export all reports in specified format."""
        all_reports = {"reports": self.reports, "count": len(self.reports)}
        return format_output(all_reports, format_type)

    def clear(self):
        """Clear all reports."""
        self.reports = []
        log_message("All reports cleared")
