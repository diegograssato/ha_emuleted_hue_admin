"""Routes: dashboard statistics."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ...schemas.common import DashboardStats, EmulatedHueStatusCheck
from ...services.config_service import ConfigService
from ...services.entity_service import EntityService
from ...services.ha_service import HAService
from ..dependencies import get_config_service, get_entity_service, get_ha_service

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardStats)
async def get_dashboard(
    config_service: ConfigService = Depends(get_config_service),
    entity_service: EntityService = Depends(get_entity_service),
) -> DashboardStats:
    config, err = config_service.get_config()
    if err:
        raise HTTPException(status_code=500, detail=err)

    stats, err = entity_service.get_stats()
    if err:
        raise HTTPException(status_code=500, detail=err)

    last_modified = config_service.get_last_modified()

    return DashboardStats(
        total_entities=stats.get("total", 0),
        exposed_entities=stats.get("exposed", 0),
        hidden_entities=stats.get("hidden", 0),
        host_ip=config.host_ip if config else None,
        listen_port=config.listen_port if config else None,
        expose_by_default=config.expose_by_default if config else True,
        last_modified=last_modified,
        emulated_hue_status="configured" if config else "unconfigured",
    )


@router.get("/status", response_model=EmulatedHueStatusCheck)
async def check_emulated_hue_status(
    ha_service: HAService = Depends(get_ha_service),
) -> EmulatedHueStatusCheck:
    """Verifica se o emulated_hue está instalado/carregado no Home Assistant."""
    result = ha_service.check_emulated_hue_installed()
    return EmulatedHueStatusCheck(**result)
