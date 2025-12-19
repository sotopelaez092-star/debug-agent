from typing import Optional, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AuditEntry:
    action: str
    timestamp: datetime
    user_id: Optional[str] = None
    details: Optional[str] = None


class AuditMixin:
    """Mixin that adds audit trail functionality."""

    _audit_log: List[AuditEntry] = field(default_factory=list)

    def log_action(self, action: str, user_id: Optional[str] = None, details: Optional[str] = None) -> None:
        """Log an action to the audit trail."""
        if not hasattr(self, '_audit_log') or self._audit_log is None:
            self._audit_log = []
        entry = AuditEntry(
            action=action,
            timestamp=datetime.now(),
            user_id=user_id,
            details=details
        )
        self._audit_log.append(entry)

    def get_audit_trail(self) -> List[AuditEntry]:
        """Get the full audit trail."""
        if not hasattr(self, '_audit_log'):
            return []
        return self._audit_log.copy()

    def clear_audit_log(self) -> None:
        """Clear the audit trail."""
        self._audit_log = []
