from datetime import datetime
from typing import Optional


class TimestampMixin:
    """Mixin that adds timestamp tracking."""

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def touch(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now()

    def mark_created(self) -> None:
        """Set the created_at timestamp."""
        now = datetime.now()
        self.created_at = now
        self.updated_at = now

    def get_age_seconds(self) -> float:
        """Get age in seconds since creation."""
        if self.created_at is None:
            return 0.0
        return (datetime.now() - self.created_at).total_seconds()
