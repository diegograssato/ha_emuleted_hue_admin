"""YAML-backed repository for emulated_hue configuration.

Implements the Repository Pattern:
- All reads/writes go through this class
- Never reads/writes YAML directly in services
- Provides automatic backup before any mutation
"""
from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..models.config import EmulatedHueConfig
from ..models.entity import EntityConfig
from ..utils.logger import get_logger
from ..utils.yaml_utils import YamlUtils

logger = get_logger(__name__)

CONFIG_YAML_PATH_ENV = "HA_CONFIG_PATH"
BACKUP_DIR_ENV = "HA_BACKUP_DIR"
DEFAULT_CONFIG_PATH = Path("/homeassistant/configuration.yaml")
BACKUP_DIR = Path("/data/backups")
EMULATED_HUE_KEY = "emulated_hue"
ENTITIES_KEY = "entities"


class YamlConfigRepository:
    """Reads and writes the emulated_hue section of configuration.yaml."""

    def __init__(
        self,
        config_path: Optional[Path] = None,
        backup_dir: Optional[Path] = None,
    ) -> None:
        self._config_path = config_path or Path(
            os.getenv(CONFIG_YAML_PATH_ENV, str(DEFAULT_CONFIG_PATH))
        )
        self._backup_dir = backup_dir or Path(
            os.getenv(BACKUP_DIR_ENV, str(BACKUP_DIR))
        )
        logger.info("YamlConfigRepository using: %s", self._config_path)

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _load_full_yaml(self) -> Tuple[dict, Optional[str]]:
        data, err = YamlUtils.safe_load(self._config_path)
        return data or {}, err

    def _save_full_yaml(self, full_data: dict) -> Optional[str]:
        hue_dict = full_data.get(EMULATED_HUE_KEY, {})
        return YamlUtils.update_yaml_section(self._config_path, EMULATED_HUE_KEY, hue_dict)

    def _get_hue_section(self, full_data: dict) -> dict:
        section = full_data.get(EMULATED_HUE_KEY)
        if not isinstance(section, dict):
            return {}
        return section

    def _backup(self) -> Tuple[Optional[Path], Optional[str]]:
        if not self._config_path.exists():
            return None, None
        return YamlUtils.backup(self._config_path, self._backup_dir)

    # ------------------------------------------------------------------ #
    # Config operations
    # ------------------------------------------------------------------ #

    def get_config(self) -> Tuple[Optional[EmulatedHueConfig], Optional[str]]:
        full, err = self._load_full_yaml()
        if err:
            return None, err
        hue = self._get_hue_section(full)
        return EmulatedHueConfig.from_dict(hue), None

    def save_config(self, config: EmulatedHueConfig) -> Optional[str]:
        self._backup()
        full, err = self._load_full_yaml()
        if err:
            return err
        existing_hue = self._get_hue_section(full)
        entities_block = existing_hue.get(ENTITIES_KEY, {})
        hue_dict = config.to_dict()
        if entities_block:
            hue_dict[ENTITIES_KEY] = entities_block
        full[EMULATED_HUE_KEY] = hue_dict
        return self._save_full_yaml(full)

    def get_last_modified(self) -> Optional[str]:
        try:
            mtime = self._config_path.stat().st_mtime
            return datetime.fromtimestamp(mtime, UTC).isoformat(sep=" ", timespec="seconds")
        except OSError:
            return None

    # ------------------------------------------------------------------ #
    # Entity operations
    # ------------------------------------------------------------------ #

    # Keys written by older versions that HA emulated_hue rejects
    _INVALID_ENTITY_KEYS = frozenset({"type"})

    def _sanitize_entity_dict(self, data: dict) -> dict:
        """Strip keys unsupported by the HA emulated_hue integration."""
        return {k: v for k, v in data.items() if k not in self._INVALID_ENTITY_KEYS}

    def _get_entities_raw(self, hue: dict) -> dict:
        raw = hue.get(ENTITIES_KEY, {})
        return raw if isinstance(raw, dict) else {}

    def list_entities(self) -> Tuple[List[EntityConfig], Optional[str]]:
        full, err = self._load_full_yaml()
        if err:
            return [], err
        hue = self._get_hue_section(full)
        raw = self._get_entities_raw(hue)
        entities = [
            EntityConfig.from_dict(eid, props if isinstance(props, dict) else {})
            for eid, props in raw.items()
        ]
        return entities, None

    def get_entity(self, entity_id: str) -> Tuple[Optional[EntityConfig], Optional[str]]:
        full, err = self._load_full_yaml()
        if err:
            return None, err
        hue = self._get_hue_section(full)
        raw = self._get_entities_raw(hue)
        if entity_id not in raw:
            return None, None
        return EntityConfig.from_dict(entity_id, raw[entity_id] or {}), None

    def save_entity(self, entity: EntityConfig) -> Optional[str]:
        self._backup()
        full, err = self._load_full_yaml()
        if err:
            return err
        if EMULATED_HUE_KEY not in full or not isinstance(full[EMULATED_HUE_KEY], dict):
            full[EMULATED_HUE_KEY] = {}
        if ENTITIES_KEY not in full[EMULATED_HUE_KEY]:
            full[EMULATED_HUE_KEY][ENTITIES_KEY] = {}
        full[EMULATED_HUE_KEY][ENTITIES_KEY][entity.entity_id] = self._sanitize_entity_dict(
            entity.to_dict()
        )
        return self._save_full_yaml(full)

    def delete_entity(self, entity_id: str) -> Tuple[bool, Optional[str]]:
        self._backup()
        full, err = self._load_full_yaml()
        if err:
            return False, err
        hue = full.get(EMULATED_HUE_KEY, {})
        if not isinstance(hue, dict):
            return False, None
        entities = hue.get(ENTITIES_KEY, {})
        if entity_id not in entities:
            return False, None
        del entities[entity_id]
        full[EMULATED_HUE_KEY][ENTITIES_KEY] = entities
        err = self._save_full_yaml(full)
        return err is None, err

    def save_entities_bulk(self, entities: Dict[str, dict]) -> Optional[str]:
        """Overwrite the full entities block."""
        self._backup()
        full, err = self._load_full_yaml()
        if err:
            return err
        if EMULATED_HUE_KEY not in full or not isinstance(full[EMULATED_HUE_KEY], dict):
            full[EMULATED_HUE_KEY] = {}
        sanitized = {
            eid: self._sanitize_entity_dict(data if isinstance(data, dict) else {})
            for eid, data in entities.items()
        }
        full[EMULATED_HUE_KEY][ENTITIES_KEY] = sanitized
        return self._save_full_yaml(full)

    # ------------------------------------------------------------------ #
    # Raw YAML access
    # ------------------------------------------------------------------ #

    def get_raw_yaml(self) -> Tuple[Optional[str], Optional[str]]:
        """Return raw YAML string of the emulated_hue section."""
        import yaml as _yaml

        full, err = self._load_full_yaml()
        if err:
            return None, err
        hue = full.get(EMULATED_HUE_KEY, {})
        try:
            content = _yaml.dump(
                {EMULATED_HUE_KEY: hue},
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )
            return content, None
        except Exception as exc:  # noqa: BLE001
            return None, str(exc)

    def save_raw_yaml(self, yaml_content: str) -> Optional[str]:
        """Validate and merge raw YAML into configuration.yaml."""
        import yaml as _yaml

        parsed, err = YamlUtils.validate_yaml_string(yaml_content)
        if err:
            return f"YAML validation error: {err}"
        if not isinstance(parsed, dict):
            return "YAML must be a mapping at the top level."
        hue_block = parsed.get(EMULATED_HUE_KEY, parsed)
        if not isinstance(hue_block, dict):
            return "Expected 'emulated_hue' mapping."

        self._backup()
        full, err = self._load_full_yaml()
        if err:
            return err
        full[EMULATED_HUE_KEY] = hue_block
        return self._save_full_yaml(full)

    # ------------------------------------------------------------------ #
    # Config path accessor
    # ------------------------------------------------------------------ #

    @property
    def config_path(self) -> Path:
        return self._config_path

    @property
    def backup_dir(self) -> Path:
        return self._backup_dir
