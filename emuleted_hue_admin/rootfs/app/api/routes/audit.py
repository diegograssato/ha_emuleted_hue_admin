"""Routes: audit log."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from ...utils.audit import AuditLogger
from ..dependencies import get_audit_logger

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("")
async def get_audit_log(
    limit: int = Query(default=100, ge=1, le=500),
    audit_logger: AuditLogger = Depends(get_audit_logger),
) -> list:
    return audit_logger.recent(limit=limit)
