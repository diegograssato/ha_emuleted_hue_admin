"""Common/shared schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str
    success: bool = True
    data: Optional[Any] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""

    page: int
    page_size: int
    total: int
    items: List[T]


class AuditLogRead(BaseModel):
    """Response schema for an audit log entry."""

    timestamp: str
    user: str
    action: str
    target: str
    details: str


class DiagnosticsRead(BaseModel):
    """Response schema for diagnostics check."""

    description_xml_url: str
    reachable: bool
    port_open: bool
    xml_valid: bool
    friendly_name: Optional[str] = None
    error: Optional[str] = None


class DashboardStats(BaseModel):
    """Response schema for dashboard statistics."""

    total_entities: int
    exposed_entities: int
    hidden_entities: int
    host_ip: Optional[str]
    listen_port: Optional[int]
    expose_by_default: bool
    last_modified: Optional[str]
    emulated_hue_status: str


class YamlEditorRead(BaseModel):
    """Response schema for raw YAML editor."""

    yaml_content: str
    is_valid: bool
    error: Optional[str] = None


class YamlEditorUpdate(BaseModel):
    """Request schema for saving raw YAML."""

    yaml_content: str


class BackupResponse(BaseModel):
    """Response for backup operation."""

    filename: str
    path: str
    size_bytes: int
    created_at: str


class EmulatedHueStatusCheck(BaseModel):
    """Response for the emulated_hue installation check."""

    component_loaded: bool
    suggestion: Optional[str] = None
