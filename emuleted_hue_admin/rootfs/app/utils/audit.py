"""Audit logger — persists audit log entries to a JSONL file."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

from ..models.audit import AuditLog
from .logger import get_logger

logger = get_logger(__name__)

DEFAULT_AUDIT_PATH = Path("/data/audit.jsonl")


class AuditLogger:
    """Append-only audit log backed by a JSONL file."""

    def __init__(self, path: Path = DEFAULT_AUDIT_PATH) -> None:
        self._path = path

    def log(self, user: str, action: str, target: str, details: str = "") -> None:
        entry = AuditLog.create(user=user, action=action, target=target, details=details)
        self._append(entry)
        logger.info(
            "AUDIT | user=%s | action=%s | target=%s | details=%s",
            user,
            action,
            target,
            details,
        )

    def recent(self, limit: int = 100) -> List[dict]:
        if not self._path.exists():
            return []
        lines: List[dict] = []
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        lines.append(json.loads(line))
        except OSError as exc:
            logger.error("Failed to read audit log: %s", exc)
        return lines[-limit:]

    def _append(self, entry: AuditLog) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry.to_dict()) + "\n")
        except OSError as exc:
            logger.error("Failed to write audit log: %s", exc)
