"""Schemas for EmulatedHue general configuration."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class ConfigRead(BaseModel):
    """Response schema for reading emulated_hue config."""

    host_ip: Optional[str] = None
    listen_port: Optional[int] = Field(default=80, ge=1, le=65535)
    expose_by_default: bool = True
    upnp_bind_multicast: bool = True
    off_maps_to_on_domains: List[str] = Field(default_factory=list)
    exposed_domains: List[str] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class ConfigUpdate(BaseModel):
    """Request schema for updating emulated_hue config."""

    host_ip: Optional[str] = None
    listen_port: Optional[int] = Field(default=None, ge=1, le=65535)
    expose_by_default: Optional[bool] = None
    upnp_bind_multicast: Optional[bool] = None
    off_maps_to_on_domains: Optional[List[str]] = None
    exposed_domains: Optional[List[str]] = None

    @field_validator("off_maps_to_on_domains", "exposed_domains", mode="before")
    @classmethod
    def validate_domains(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return v
        return [d.strip().lower() for d in v if d.strip()]
