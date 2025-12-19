"""
Analytics dashboard module.
Coordinates multiple reports and visualizations.
"""

import logging
from typing import List, Dict, Any
from report_generator import ReportGenerator, ReportConfig, ReportFormatter

logger = logging.getLogger(__name__)


class DashboardWidget:
    """Base class for dashboard widgets."""

    def __init__(self, title: str):
        self.title = title

    def render(self) -> str:
        raise NotImplementedError


class QueryWidget(DashboardWidget):
    """Widget that displays a SQL query result."""

    def __init__(self, title: str, query: str):
        super().__init__(title)
        self.query = query

    def render(self) -> str:
        """Render the widget."""
        return ReportFormatter.format_query_result(self.query, self.title)


class Dashboard:
    """Analytics dashboard with multiple widgets."""

    def __init__(self, name: str):
        self.name = name
        self.widgets: List[DashboardWidget] = []
        logger.info(f"Dashboard created: {name}")

    def add_widget(self, widget: DashboardWidget):
        """Add a widget to the dashboard."""
        self.widgets.append(widget)
        logger.debug(f"Widget added: {widget.title}")

    def render(self) -> str:
        """Render the complete dashboard."""
        output = []

        output.append("\n" + "=" * 80)
        output.append(f"DASHBOARD: {self.name}")
        output.append("=" * 80)
        output.append("")

        for widget in self.widgets:
            output.append(widget.render())
            output.append("")

        output.append("=" * 80)
        output.append(f"Total widgets: {len(self.widgets)}")
        output.append("=" * 80)

        return "\n".join(output)


class AnalyticsDashboard:
    """Main analytics dashboard coordinator."""

    def __init__(self):
        self.report_generator = ReportGenerator()
        logger.info("AnalyticsDashboard initialized")

    def create_executive_dashboard(self) -> Dashboard:
        """Create an executive summary dashboard."""
        logger.info("Creating executive dashboard")

        dashboard = Dashboard("Executive Summary")

        # Sales overview
        sales_query = self.report_generator.generate_sales_report('2024-01-01', '2024-12-31')
        dashboard.add_widget(QueryWidget("Annual Sales Report", sales_query))

        # Customer overview
        customer_query = self.report_generator.generate_customer_report(min_purchases=5)
        dashboard.add_widget(QueryWidget("Top Customers (5+ purchases)", customer_query))

        # Inventory status
        inventory_query = self.report_generator.generate_inventory_report()
        dashboard.add_widget(QueryWidget("Current Inventory Status", inventory_query))

        return dashboard

    def create_trends_dashboard(self) -> Dashboard:
        """Create a trends analysis dashboard."""
        logger.info("Creating trends dashboard")

        dashboard = Dashboard("Trends Analysis")

        # Monthly sales trend
        sales_trend = self.report_generator.generate_trend_report('sales', 'month')
        dashboard.add_widget(QueryWidget("Monthly Sales Trend", sales_trend))

        # Weekly order trend
        order_trend = self.report_generator.generate_trend_report('orders', 'week')
        dashboard.add_widget(QueryWidget("Weekly Order Trend", order_trend))

        # Daily customer trend
        customer_trend = self.report_generator.generate_trend_report('customers', 'day')
        dashboard.add_widget(QueryWidget("Daily Customer Trend", customer_trend))

        return dashboard

    def create_category_dashboard(self, category: str) -> Dashboard:
        """Create a category-specific dashboard."""
        logger.info(f"Creating category dashboard: {category}")

        dashboard = Dashboard(f"Category Analysis: {category}")

        # Category inventory
        inventory_query = self.report_generator.generate_inventory_report(category)
        dashboard.add_widget(QueryWidget(f"{category} Inventory", inventory_query))

        return dashboard
