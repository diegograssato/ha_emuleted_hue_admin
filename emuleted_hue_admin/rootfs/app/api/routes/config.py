"""Routes: emulated_hue general configuration."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from ...schemas.common import MessageResponse, YamlEditorRead, YamlEditorUpdate
from ...schemas.config import ConfigRead, ConfigUpdate
from ...services.config_service import ConfigService
from ...utils.yaml_utils import YamlUtils
from ..dependencies import get_config_service

router = APIRouter(prefix="/api/config", tags=["config"])


def _user(request: Request) -> str:
    return request.headers.get("X-Remote-User", "system")


@router.get("", response_model=ConfigRead)
async def read_config(
    request: Request,
    service: ConfigService = Depends(get_config_service),
) -> ConfigRead:
    config, err = service.get_config()
    if err:
        raise HTTPException(status_code=500, detail=err)
    return config


@router.put("", response_model=ConfigRead)
async def update_config(
    payload: ConfigUpdate,
    request: Request,
    service: ConfigService = Depends(get_config_service),
) -> ConfigRead:
    updated, err = service.update_config(payload, user=_user(request))
    if err:
        raise HTTPException(status_code=500, detail=err)
    return updated


@router.get("/yaml", response_model=YamlEditorRead)
async def get_yaml(
    service: ConfigService = Depends(get_config_service),
) -> YamlEditorRead:
    content, err = service.get_raw_yaml()
    if err:
        return YamlEditorRead(yaml_content="", is_valid=False, error=err)
    _, parse_err = YamlUtils.validate_yaml_string(content or "")
    return YamlEditorRead(
        yaml_content=content or "",
        is_valid=parse_err is None,
        error=parse_err,
    )


@router.put("/yaml", response_model=MessageResponse)
async def save_yaml(
    payload: YamlEditorUpdate,
    request: Request,
    service: ConfigService = Depends(get_config_service),
) -> MessageResponse:
    _, parse_err = YamlUtils.validate_yaml_string(payload.yaml_content)
    if parse_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid YAML: {parse_err}",
        )
    err = service.save_raw_yaml(payload.yaml_content, user=_user(request))
    if err:
        raise HTTPException(status_code=500, detail=err)
    return MessageResponse(message="YAML saved successfully.")
