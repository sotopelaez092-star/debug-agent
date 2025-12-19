"""
Main application demonstrating cross-package imports.
This will fail due to incorrect relative import in report_generator.py
"""

from package_a.submodule_x import DataProcessor, DataAnalyzer
from package_b import TaskCoordinator
from package_b.submodule_y import ReportGenerator


def main():
    """Main function."""
    print("=== Cross-Package Import Demo ===\n")

    # Initialize coordinator
    coordinator = TaskCoordinator()

    # Add some tasks
    coordinator.add_task("process_data", {"user": "alice", "score": 95})
    coordinator.add_task("analyze_numbers", [10, 20, 30, 40, 50])

    # Execute tasks
    print("\n--- Executing Tasks ---")
    results = coordinator.execute_tasks()
    print(f"Results: {results}")

    # Get summary
    print("\n--- Summary ---")
    summary = coordinator.get_summary()
    print(f"Summary: {summary}")

    # Generate report - this will FAIL due to import error
    print("\n--- Generating Report ---")
    try:
        report_gen = ReportGenerator()
        report = report_gen.generate_report("Task Summary", summary)
        print(f"Report: {report}")
    except Exception as e:
        print(f"ERROR: {e}")


if __name__ == "__main__":
    main()
