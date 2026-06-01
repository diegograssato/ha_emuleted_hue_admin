"""Schemas for entity management."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


ENTITY_ID_PATTERN = r"^[a-z_]+\.[a-z0-9_]+$"


class EntityBase(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    hidden: bool = False
    entity_type: Optional[str] = Field(default=None, alias="type")

    model_config = {"populate_by_name": True}


class EntityRead(EntityBase):
    """Response schema for an entity."""

    entity_id: str
    domain: str

    model_config = {"from_attributes": True, "populate_by_name": True}


class EntityCreate(EntityBase):
    """Request schema for creating a new entity."""

    entity_id: str = Field(..., pattern=ENTITY_ID_PATTERN)

    @field_validator("entity_id")
    @classmethod
    def validate_entity_id(cls, v: str) -> str:
        return v.strip().lower()


class EntityUpdate(EntityBase):
    """Request schema for updating an entity (partial)."""

    name: Optional[str] = Field(default=None, max_length=255)
    hidden: Optional[bool] = None
    entity_type: Optional[str] = Field(default=None, alias="type")


class EntityListResponse(BaseModel):
    """Paginated list of entities."""

    page: int
    page_size: int
    total: int
    items: List[EntityRead]


class BulkImportRequest(BaseModel):
    """Request schema for bulk importing entities from YAML string."""

    yaml_content: str
