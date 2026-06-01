"""ConfigService — application service for emulated_hue general settings."""
from __future__ import annotations

from typing import Optional, Tuple

from ..models.config import EmulatedHueConfig
from ..repositories.yaml_repository import YamlConfigRepository
from ..schemas.config import ConfigRead, ConfigUpdate
from ..utils.audit import AuditLogger
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ConfigService:
    """Manages reading and updating the emulated_hue configuration section."""

    def __init__(
        self,
        repository: YamlConfigRepository,
        audit_logger: AuditLogger,
    ) -> None:
        self._repo = repository
        self._audit = audit_logger

    def get_config(self) -> Tuple[Optional[ConfigRead], Optional[str]]:
        config, err = self._repo.get_config()
        if err:
            logger.error("Failed to read config: %s", err)
            return None, err
        if config is None:
            config = EmulatedHueConfig()
        return ConfigRead(
            host_ip=config.host_ip,
            listen_port=config.listen_port,
            expose_by_default=config.expose_by_default,
            upnp_bind_multicast=config.upnp_bind_multicast,
            off_maps_to_on_domains=config.off_maps_to_on_domains,
            exposed_domains=config.exposed_domains,
        ), None

    def update_config(
        self, update: ConfigUpdate, user: str = "system"
    ) -> Tuple[Optional[ConfigRead], Optional[str]]:
        current, err = self._repo.get_config()
        if err:
            return None, err
        if current is None:
            current = EmulatedHueConfig()

        # Apply partial update
        if update.host_ip is not None:
            current.host_ip = update.host_ip
        if update.listen_port is not None:
            current.listen_port = update.listen_port
        if update.expose_by_default is not None:
            current.expose_by_default = update.expose_by_default
        if update.upnp_bind_multicast is not None:
            current.upnp_bind_multicast = update.upnp_bind_multicast
        if update.off_maps_to_on_domains is not None:
            current.off_maps_to_on_domains = update.off_maps_to_on_domains
        if update.exposed_domains is not None:
            current.exposed_domains = update.exposed_domains

        save_err = self._repo.save_config(current)
        if save_err:
            logger.error("Failed to save config: %s", save_err)
            return None, save_err

        self._audit.log(user=user, action="UPDATE_CONFIG", target="emulated_hue", details="")
        return ConfigRead(
            host_ip=current.host_ip,
            listen_port=current.listen_port,
            expose_by_default=current.expose_by_default,
            upnp_bind_multicast=current.upnp_bind_multicast,
            off_maps_to_on_domains=current.off_maps_to_on_domains,
            exposed_domains=current.exposed_domains,
        ), None

    def get_raw_yaml(self) -> Tuple[Optional[str], Optional[str]]:
        return self._repo.get_raw_yaml()

    def save_raw_yaml(self, yaml_content: str, user: str = "system") -> Optional[str]:
        err = self._repo.save_raw_yaml(yaml_content)
        if err:
            logger.error("Failed to save raw YAML: %s", err)
            return err
        self._audit.log(
            user=user, action="SAVE_RAW_YAML", target="emulated_hue", details=""
        )
        return None

    def get_last_modified(self) -> Optional[str]:
        return self._repo.get_last_modified()
