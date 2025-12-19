"""
Report generation module.
Generates reports from user and order data.
"""
from typing import Dict, Any, List
from data_processor import DataProcessor
from order_processor import OrderProcessor


class ReportGenerator:
    """Generates various data reports."""

    def __init__(self):
        self.data_processor = DataProcessor()
        self.order_processor = OrderProcessor()

    def generate_user_report(self, user_dict: Dict[str, Any]) -> str:
        """Generate user report."""
        processed = self.data_processor.process_user_profile(user_dict)
        contact = self.data_processor.extract_user_contact(user_dict)

        report = f"""
User Report
===========
ID: {processed['id']}
Name: {processed['name']}
Email: {contact['email']}
Phone: {contact['phone']}
"""
        return report.strip()

    def generate_order_report(self, order_dict: Dict[str, Any]) -> str:
        """Generate order report."""
        summary = self.order_processor.get_order_summary(order_dict)
        total_with_tax = self.order_processor.calculate_order_total(order_dict)

        report = f"""
Order Report
============
{summary}
Total (with tax): ${total_with_tax:.2f}
"""
        return report.strip()

    def generate_shipping_label(self, order_dict: Dict[str, Any]) -> str:
        """Generate shipping label from order."""
        shipping = self.order_processor.get_shipping_info(order_dict)

        if not shipping:
            return "No shipping information available"

        label = f"""
Ship To:
{shipping['city']}, {shipping['state']} {shipping['zip']}
"""
        return label.strip()
