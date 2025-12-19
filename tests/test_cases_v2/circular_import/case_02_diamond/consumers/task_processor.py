"""Background task processor that uses authentication and storage."""
from typing import List, Dict, Any
from providers import Authenticator, StorageProvider


class TaskProcessor:
    """Processes background tasks with authentication."""

    def __init__(self):
        self._auth = Authenticator()
        self._storage = StorageProvider()
        self._task_queue: List[Dict[str, Any]] = []

    def queue_task(self, task_type: str, session_id: str, data: Dict[str, Any]) -> bool:
        """Queue a background task."""
        if self._auth.validate_session(session_id):
            task = {
                "type": task_type,
                "session_id": session_id,
                "data": data
            }
            self._task_queue.append(task)
            return True
        return False

    def process_tasks(self) -> int:
        """Process all queued tasks."""
        processed = 0
        for task in self._task_queue:
            if self._process_single_task(task):
                processed += 1
        self._task_queue.clear()
        return processed

    def _process_single_task(self, task: Dict[str, Any]) -> bool:
        """Process a single task."""
        task_type = task["type"]
        session_id = task["session_id"]
        data = task["data"]

        if not self._auth.validate_session(session_id):
            return False

        if task_type == "save":
            return self._storage.save_data(
                data.get("key"),
                data.get("value"),
                session_id
            )
        elif task_type == "delete":
            return self._storage.delete_data(
                data.get("key"),
                session_id
            )
        return False
