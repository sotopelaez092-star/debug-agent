"""
Report generation module.
Creates various reports using query builders.
"""

import logging
from typing import List, Dict, Any
from aggregation_builder import AggregationBuilder

logger = logging.getLogger(__name__)


class ReportConfig:
    """Configuration for report generation."""

    def __init__(self):
        self.include_totals = True
        self.include_averages = True
        self.include_breakdown = True
        self.group_by_category = True
        self.limit_results = 100


class ReportGenerator:
    """Generates various analytical reports."""

    def __init__(self, config: ReportConfig = None):
        self.config = config or ReportConfig()
        logger.info("ReportGenerator initialized")

    def generate_sales_report(self, date_from: str, date_to: str) -> str:
        """Generate a sales report for the given date range."""
        logger.info(f"Generating sales report: {date_from} to {date_to}")

        # Build query with aggregations
        query = (
            AggregationBuilder('sales')
            .select('product_id', 'category')
            .where(f"sale_date >= '{date_from}'")
            .where(f"sale_date <= '{date_to}'")
            .sum('amount', 'total_sales')
            .count('*', 'total_transactions')
            .avg('amount', 'average_sale')
            .group_by('product_id', 'category')
            .order_by('total_sales', 'DESC')
            .limit(self.config.limit_results)
            .build()
        )

        return query

    def generate_customer_report(self, min_purchases: int = 1) -> str:
        """Generate a customer activity report."""
        logger.info(f"Generating customer report (min purchases: {min_purchases})")

        # Build query with customer aggregations
        query = (
            AggregationBuilder('customers')
            .select('customer_id', 'customer_name', 'region')
            .join('orders', 'customers.customer_id = orders.customer_id')
            .count('orders.order_id', 'total_orders')
            .sum('orders.total_amount', 'total_spent')
            .avg('orders.total_amount', 'average_order_value')
            .group_by('customers.customer_id', 'customer_name', 'region')
            .having(f"COUNT(orders.order_id) >= {min_purchases}")
            .order_by('total_spent', 'DESC')
            .build()
        )

        return query

    def generate_inventory_report(self, category: str = None) -> str:
        """Generate an inventory status report."""
        logger.info(f"Generating inventory report for category: {category or 'all'}")

        builder = (
            AggregationBuilder('inventory')
            .select('product_id', 'product_name', 'category', 'warehouse')
            .sum('quantity', 'total_quantity')
            .min('quantity', 'min_quantity')
            .max('quantity', 'max_quantity')
            .avg('quantity', 'avg_quantity')
        )

        if category:
            builder.where(f"category = '{category}'")

        query = (
            builder
            .group_by('product_id', 'product_name', 'category', 'warehouse')
            .having('SUM(quantity) > 0')
            .order_by('total_quantity', 'ASC')
            .build()
        )

        return query

    def generate_trend_report(self, metric: str, group_by_period: str = 'month') -> str:
        """
        Generate a trend analysis report.

        Args:
            metric: The metric to analyze (sales, orders, customers)
            group_by_period: Time period for grouping (day, week, month, year)
        """
        logger.info(f"Generating trend report for {metric} by {group_by_period}")

        # Map period to SQL date function
        period_functions = {
            'day': 'DATE(created_at)',
            'week': 'WEEK(created_at)',
            'month': 'MONTH(created_at)',
            'year': 'YEAR(created_at)'
        }

        period_field = period_functions.get(group_by_period, 'DATE(created_at)')

        # Build trend query
        builder = AggregationBuilder(metric)

        # Add time period field
        builder.select(f"{period_field} AS period")

        # Add metric-specific aggregations
        if metric == 'sales':
            builder.sum('amount', 'total_amount')
            builder.count('*', 'transaction_count')
            builder.avg('amount', 'average_amount')
        elif metric == 'orders':
            builder.count('*', 'order_count')
            builder.sum('total_amount', 'revenue')
        elif metric == 'customers':
            builder.distinct_count('customer_id', 'unique_customers')

        # This is where the typo occurs - should be group_by not groupby
        query = (
            builder
            .groupby(period_field)  # TYPO: should be group_by
            .order_by('period', 'ASC')
            .build()
        )

        return query


class ReportFormatter:
    """Formats reports for display."""

    @staticmethod
    def format_query_result(query: str, description: str) -> str:
        """Format a query result for display."""
        output = []
        output.append("=" * 80)
        output.append(description)
        output.append("=" * 80)
        output.append("")
        output.append("Generated SQL:")
        output.append("-" * 80)
        output.append(query)
        output.append("-" * 80)
        output.append("")

        return "\n".join(output)
