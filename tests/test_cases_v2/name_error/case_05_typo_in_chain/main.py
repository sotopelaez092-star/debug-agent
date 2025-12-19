"""
Main entry point for the analytics dashboard application.
"""

import sys
import logging
from analytics_dashboard import AnalyticsDashboard


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def main():
    """Run the analytics dashboard."""
    setup_logging()

    print("=" * 80)
    print("Analytics Dashboard Application")
    print("=" * 80)

    # Create analytics dashboard
    analytics = AnalyticsDashboard()

    # Test 1: Executive Dashboard
    print("\n" + "-" * 80)
    print("Creating Executive Dashboard...")
    print("-" * 80)

    try:
        exec_dashboard = analytics.create_executive_dashboard()
        print(exec_dashboard.render())
    except Exception as e:
        print(f"✗ Failed to create executive dashboard: {e}")
        import traceback
        traceback.print_exc()

    # Test 2: Trends Dashboard
    print("\n" + "-" * 80)
    print("Creating Trends Dashboard...")
    print("-" * 80)

    try:
        trends_dashboard = analytics.create_trends_dashboard()
        print(trends_dashboard.render())
    except Exception as e:
        print(f"✗ Failed to create trends dashboard: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Test 3: Category Dashboard
    print("\n" + "-" * 80)
    print("Creating Category Dashboard...")
    print("-" * 80)

    try:
        category_dashboard = analytics.create_category_dashboard("Electronics")
        print(category_dashboard.render())
    except Exception as e:
        print(f"✗ Failed to create category dashboard: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 80)
    print("Dashboard generation complete!")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
