"""Routes: entity CRUD, pagination, filtering, bulk import/export."""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import PlainTextResponse

from ...schemas.entity import (
    BulkImportRequest,
    EntityCreate,
    EntityListResponse,
    EntityRead,
    EntityUpdate,
)
from ...schemas.common import MessageResponse
from ...services.entity_service import EntityService
from ...services.ha_service import HAService
from ..dependencies import get_entity_service, get_ha_service

router = APIRouter(prefix="/api/entities", tags=["entities"])


def _user(request: Request) -> str:
    return request.headers.get("X-Remote-User", "system")


@router.get("", response_model=EntityListResponse)
async def list_entities(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    search: Optional[str] = Query(default=None),
    hidden: Optional[bool] = Query(default=None),
    entity_type: Optional[str] = Query(default=None, alias="type"),
    domain: Optional[str] = Query(default=None),
    service: EntityService = Depends(get_entity_service),
) -> EntityListResponse:
    result, err = service.list_entities(
        page=page,
        page_size=page_size,
        search=search,
        hidden=hidden,
        entity_type=entity_type,
        domain=domain,
    )
    if err:
        raise HTTPException(status_code=500, detail=err)
    return result


@router.get("/export", response_class=PlainTextResponse)
async def export_entities(
    service: EntityService = Depends(get_entity_service),
) -> str:
    content, err = service.export_yaml()
    if err:
        raise HTTPException(status_code=500, detail=err)
    return content


@router.get("/ha-states", response_model=List[dict])
async def ha_states(
    ha_service: HAService = Depends(get_ha_service),
) -> List[dict]:
    """Return entity_id + friendly_name for all HA states (for autocomplete)."""
    states, err = ha_service.get_ha_states()
    if err or states is None:
        # Not fatal — return empty list so the form still works without HA
        return []
    result = []
    for s in states:
        if not isinstance(s, dict):
            continue
        entity_id = s.get("entity_id", "")
        if not entity_id:
            continue
        friendly = (s.get("attributes") or {}).get("friendly_name") or ""
        result.append({"entity_id": entity_id, "friendly_name": friendly})
    result.sort(key=lambda x: x["entity_id"])
    return result


@router.get("/{entity_id:path}", response_model=EntityRead)
async def get_entity(
    entity_id: str,
    service: EntityService = Depends(get_entity_service),
) -> EntityRead:
    entity, err = service.get_entity(entity_id)
    if err:
        raise HTTPException(status_code=500, detail=err)
    if entity is None:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found.")
    return entity


@router.post("", response_model=EntityRead, status_code=status.HTTP_201_CREATED)
async def create_entity(
    payload: EntityCreate,
    request: Request,
    service: EntityService = Depends(get_entity_service),
) -> EntityRead:
    created, err = service.create_entity(payload, user=_user(request))
    if err:
        if "already exists" in (err or ""):
            raise HTTPException(status_code=409, detail=err)
        raise HTTPException(status_code=500, detail=err)
    return created


@router.put("/{entity_id:path}", response_model=EntityRead)
async def update_entity(
    entity_id: str,
    payload: EntityUpdate,
    request: Request,
    service: EntityService = Depends(get_entity_service),
) -> EntityRead:
    updated, err = service.update_entity(entity_id, payload, user=_user(request))
    if err:
        raise HTTPException(status_code=500, detail=err)
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found.")
    return updated


@router.delete("/{entity_id:path}", response_model=MessageResponse)
async def delete_entity(
    entity_id: str,
    request: Request,
    service: EntityService = Depends(get_entity_service),
) -> MessageResponse:
    deleted, err = service.delete_entity(entity_id, user=_user(request))
    if err:
        raise HTTPException(status_code=500, detail=err)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found.")
    return MessageResponse(message=f"Entity '{entity_id}' deleted.")


@router.post("/duplicate", response_model=EntityRead, status_code=status.HTTP_201_CREATED)
async def duplicate_entity(
    source_id: str = Query(...),
    new_id: str = Query(...),
    request: Request = None,
    service: EntityService = Depends(get_entity_service),
) -> EntityRead:
    result, err = service.duplicate_entity(source_id, new_id, user=_user(request))
    if err:
        raise HTTPException(status_code=400, detail=err)
    return result


@router.post("/import", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def bulk_import(
    payload: BulkImportRequest,
    request: Request,
    service: EntityService = Depends(get_entity_service),
) -> MessageResponse:
    count, err = service.bulk_import(payload.yaml_content, user=_user(request))
    if err:
        raise HTTPException(status_code=422, detail=err)
    return MessageResponse(message=f"Imported {count} entities.", data={"count": count})
