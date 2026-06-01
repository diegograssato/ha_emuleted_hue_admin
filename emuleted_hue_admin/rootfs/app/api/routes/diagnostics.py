"""Routes: Alexa/Emulated Hue diagnostics."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from ...schemas.common import DiagnosticsRead
from ...services.config_service import ConfigService
from ...services.diagnostics_service import DiagnosticsService
from ..dependencies import get_config_service, get_diagnostics_service

router = APIRouter(prefix="/api/diagnostics", tags=["diagnostics"])


@router.get("", response_model=DiagnosticsRead)
async def run_diagnostics(
    config_service: ConfigService = Depends(get_config_service),
    diag_service: DiagnosticsService = Depends(get_diagnostics_service),
) -> DiagnosticsRead:
    config, _ = config_service.get_config()
    host_ip = config.host_ip if config else None
    listen_port = config.listen_port if config else None

    result = diag_service.run(host_ip=host_ip, listen_port=listen_port)
    return DiagnosticsRead(**result)
