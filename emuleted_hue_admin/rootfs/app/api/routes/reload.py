"""Routes: reload Emulated Hue / HA Core."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from ...schemas.common import MessageResponse
from ...services.ha_service import HAService
from ...utils.audit import AuditLogger
from ..dependencies import get_audit_logger, get_ha_service

router = APIRouter(prefix="/api/reload", tags=["reload"])


def _user(request: Request) -> str:
    return request.headers.get("X-Remote-User", "system")


@router.get("/ping", response_model=MessageResponse)
async def ping() -> MessageResponse:
    """Health check — used by the frontend to detect when HA is back online."""
    return MessageResponse(message="ok")


@router.post("", response_model=MessageResponse)
async def reload_emulated_hue(
    request: Request,
    ha_service: HAService = Depends(get_ha_service),
    audit_logger: AuditLogger = Depends(get_audit_logger),
) -> MessageResponse:
    success, err = ha_service.reload_emulated_hue()
    user = _user(request)
    if err:
        audit_logger.log(user=user, action="RELOAD_FAILED", target="emulated_hue", details=err)
        raise HTTPException(status_code=500, detail=f"Reload failed: {err}")

    audit_logger.log(user=user, action="RELOAD", target="emulated_hue")
    return MessageResponse(message="Reinicialização do Home Assistant solicitada. Aguarde alguns instantes.")
