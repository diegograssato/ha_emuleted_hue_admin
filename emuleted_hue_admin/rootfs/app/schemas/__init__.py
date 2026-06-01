"""Pydantic schemas (DTOs) for Emulated Hue Manager."""
from .config import ConfigRead, ConfigUpdate
from .entity import EntityRead, EntityCreate, EntityUpdate, EntityListResponse
from .common import PaginatedResponse, MessageResponse, AuditLogRead

__all__ = [
    "ConfigRead",
    "ConfigUpdate",
    "EntityRead",
    "EntityCreate",
    "EntityUpdate",
    "EntityListResponse",
    "PaginatedResponse",
    "MessageResponse",
    "AuditLogRead",
]
