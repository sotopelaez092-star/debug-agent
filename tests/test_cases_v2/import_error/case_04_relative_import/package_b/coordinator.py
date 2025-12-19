"""
Task coordinator for package B.
"""

from .helpers import log_message, merge_results
# Import from package_a
from package_a.submodule_x import DataProcessor, DataAnalyzer


class TaskCoordinator:
    """Coordinates tasks across multiple components."""

    def __init__(self):
        self.processor = DataProcessor()
        self.analyzer = DataAnalyzer()
        self.tasks = []

    def add_task(self, task_name, task_data):
        """Add a task to the queue."""
        log_message(f"Adding task: {task_name}")
        self.tasks.append({
            "name": task_name,
            "data": task_data,
            "status": "pending"
        })

    def execute_tasks(self):
        """Execute all pending tasks."""
        results = []
        for task in self.tasks:
            if task["status"] == "pending":
                log_message(f"Executing task: {task['name']}")
                try:
                    # Process the task data
                    processed = self.processor.process(task["data"])

                    # Analyze if numeric
                    if isinstance(task["data"], (list, int, float)):
                        self.analyzer.add_data(task["data"])

                    task["status"] = "completed"
                    results.append({"task": task["name"], "result": processed})
                except Exception as e:
                    log_message(f"Task failed: {e}", "ERROR")
                    task["status"] = "failed"

        return results

    def get_summary(self):
        """Get summary of all tasks and analysis."""
        stats = self.processor.get_stats()
        analysis = self.analyzer.analyze()

        return merge_results(
            {"tasks": len(self.tasks)},
            {"processor_stats": stats},
            {"analysis": analysis}
        )
