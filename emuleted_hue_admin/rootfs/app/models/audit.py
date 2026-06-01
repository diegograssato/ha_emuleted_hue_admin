"""Domain model: AuditLog."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class AuditLog:
    """Represents a single audit log entry."""

    timestamp: datetime
    user: str
    action: str
    target: str
    details: str = ""

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(sep=" ", timespec="seconds"),
            "user": self.user,
            "action": self.action,
            "target": self.target,
            "details": self.details,
        }

    @classmethod
    def create(cls, user: str, action: str, target: str, details: str = "") -> "AuditLog":
        return cls(
            timestamp=datetime.now(UTC),
            user=user,
            action=action,
            target=target,
            details=details,
        )
