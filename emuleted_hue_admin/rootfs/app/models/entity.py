"""Domain model: EntityConfig."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


VALID_ENTITY_TYPES = frozenset(
    {"light", "switch", "script", "scene", "cover", "media_player", "fan", "climate"}
)

VALID_DOMAINS = frozenset(
    {"light", "switch", "script", "scene", "cover", "media_player", "fan", "climate", "group"}
)


@dataclass
class EntityConfig:
    """Represents a single entity entry under emulated_hue.entities."""

    entity_id: str
    name: Optional[str] = None
    hidden: bool = False
    entity_type: Optional[str] = None

    @property
    def domain(self) -> str:
        return self.entity_id.split(".")[0] if "." in self.entity_id else ""

    def to_dict(self) -> dict:
        data: dict = {}
        if self.name is not None:
            data["name"] = self.name
        data["hidden"] = self.hidden
        # NOTE: entity_type is an app-only concept used for filtering in the UI.
        # The HA emulated_hue integration only accepts 'name' and 'hidden' per entity.
        return data

    @classmethod
    def from_dict(cls, entity_id: str, data: dict) -> "EntityConfig":
        return cls(
            entity_id=entity_id,
            name=data.get("name"),
            hidden=bool(data.get("hidden", False)),
            entity_type=data.get("type"),
        )
