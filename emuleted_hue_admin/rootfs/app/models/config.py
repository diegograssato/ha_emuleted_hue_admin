"""Domain model: EmulatedHueConfig."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class EmulatedHueConfig:
    """Represents the emulated_hue top-level configuration block."""

    host_ip: Optional[str] = None
    listen_port: Optional[int] = 80
    expose_by_default: bool = True
    upnp_bind_multicast: bool = True
    off_maps_to_on_domains: List[str] = field(default_factory=lambda: ["script", "scene"])
    exposed_domains: List[str] = field(
        default_factory=lambda: ["light", "switch", "script", "scene", "cover"]
    )

    def to_dict(self) -> dict:
        return {
            "host_ip": self.host_ip,
            "listen_port": self.listen_port,
            "expose_by_default": self.expose_by_default,
            "upnp_bind_multicast": self.upnp_bind_multicast,
            "off_maps_to_on_domains": self.off_maps_to_on_domains,
            "exposed_domains": self.exposed_domains,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EmulatedHueConfig":
        return cls(
            host_ip=data.get("host_ip"),
            listen_port=data.get("listen_port", 80),
            expose_by_default=data.get("expose_by_default", True),
            upnp_bind_multicast=data.get("upnp_bind_multicast", True),
            off_maps_to_on_domains=data.get("off_maps_to_on_domains", ["script", "scene"]),
            exposed_domains=data.get(
                "exposed_domains", ["light", "switch", "script", "scene", "cover"]
            ),
        )
