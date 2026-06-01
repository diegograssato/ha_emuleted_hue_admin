"""EntityService — application service for CRUD on emulated_hue entities."""
from __future__ import annotations

from typing import List, Optional, Tuple

import yaml

from ..models.entity import EntityConfig
from ..repositories.yaml_repository import YamlConfigRepository
from ..schemas.entity import EntityCreate, EntityListResponse, EntityRead, EntityUpdate
from ..utils.audit import AuditLogger
from ..utils.logger import get_logger
from ..utils.yaml_utils import YamlUtils

logger = get_logger(__name__)


def _to_read(entity: EntityConfig) -> EntityRead:
    return EntityRead(
        entity_id=entity.entity_id,
        domain=entity.domain,
        name=entity.name,
        hidden=entity.hidden,
        type=entity.entity_type,
    )


class EntityService:
    """CRUD + pagination + filtering for emulated_hue entities."""

    def __init__(
        self,
        repository: YamlConfigRepository,
        audit_logger: AuditLogger,
    ) -> None:
        self._repo = repository
        self._audit = audit_logger

    # ------------------------------------------------------------------ #
    # List with pagination and filtering
    # ------------------------------------------------------------------ #

    def list_entities(
        self,
        page: int = 1,
        page_size: int = 25,
        search: Optional[str] = None,
        hidden: Optional[bool] = None,
        entity_type: Optional[str] = None,
        domain: Optional[str] = None,
    ) -> Tuple[Optional[EntityListResponse], Optional[str]]:
        all_entities, err = self._repo.list_entities()
        if err:
            return None, err

        filtered = self._apply_filters(all_entities, search, hidden, entity_type, domain)
        total = len(filtered)

        # Server-side pagination
        start = (page - 1) * page_size
        end = start + page_size
        page_items = filtered[start:end]

        return EntityListResponse(
            page=page,
            page_size=page_size,
            total=total,
            items=[_to_read(e) for e in page_items],
        ), None

    def _apply_filters(
        self,
        entities: List[EntityConfig],
        search: Optional[str],
        hidden: Optional[bool],
        entity_type: Optional[str],
        domain: Optional[str],
    ) -> List[EntityConfig]:
        result = entities

        if search:
            q = search.lower()
            result = [
                e
                for e in result
                if q in e.entity_id.lower() or (e.name and q in e.name.lower())
            ]
        if hidden is not None:
            result = [e for e in result if e.hidden == hidden]
        if entity_type:
            result = [e for e in result if e.entity_type == entity_type]
        if domain:
            result = [e for e in result if e.domain == domain]

        return result

    # ------------------------------------------------------------------ #
    # CRUD
    # ------------------------------------------------------------------ #

    def get_entity(self, entity_id: str) -> Tuple[Optional[EntityRead], Optional[str]]:
        entity, err = self._repo.get_entity(entity_id)
        if err:
            return None, err
        if entity is None:
            return None, None
        return _to_read(entity), None

    def create_entity(
        self, data: EntityCreate, user: str = "system"
    ) -> Tuple[Optional[EntityRead], Optional[str]]:
        existing, err = self._repo.get_entity(data.entity_id)
        if err:
            return None, err
        if existing is not None:
            return None, f"Entity '{data.entity_id}' already exists."

        entity = EntityConfig(
            entity_id=data.entity_id,
            name=data.name,
            hidden=data.hidden,
            entity_type=data.entity_type,
        )
        save_err = self._repo.save_entity(entity)
        if save_err:
            return None, save_err

        self._audit.log(user=user, action="CREATE_ENTITY", target=data.entity_id)
        return _to_read(entity), None

    def update_entity(
        self, entity_id: str, data: EntityUpdate, user: str = "system"
    ) -> Tuple[Optional[EntityRead], Optional[str]]:
        entity, err = self._repo.get_entity(entity_id)
        if err:
            return None, err
        if entity is None:
            return None, None

        if data.name is not None:
            entity.name = data.name
        if data.hidden is not None:
            entity.hidden = data.hidden
        if data.entity_type is not None:
            entity.entity_type = data.entity_type

        save_err = self._repo.save_entity(entity)
        if save_err:
            return None, save_err

        self._audit.log(user=user, action="UPDATE_ENTITY", target=entity_id)
        return _to_read(entity), None

    def delete_entity(
        self, entity_id: str, user: str = "system"
    ) -> Tuple[bool, Optional[str]]:
        deleted, err = self._repo.delete_entity(entity_id)
        if err:
            return False, err
        if deleted:
            self._audit.log(user=user, action="DELETE_ENTITY", target=entity_id)
        return deleted, None

    def duplicate_entity(
        self, source_id: str, new_id: str, user: str = "system"
    ) -> Tuple[Optional[EntityRead], Optional[str]]:
        source, err = self._repo.get_entity(source_id)
        if err:
            return None, err
        if source is None:
            return None, f"Source entity '{source_id}' not found."

        new_entity = EntityConfig(
            entity_id=new_id,
            name=source.name,
            hidden=source.hidden,
            entity_type=source.entity_type,
        )
        save_err = self._repo.save_entity(new_entity)
        if save_err:
            return None, save_err

        self._audit.log(
            user=user,
            action="DUPLICATE_ENTITY",
            target=new_id,
            details=f"source={source_id}",
        )
        return _to_read(new_entity), None

    # ------------------------------------------------------------------ #
    # Bulk import
    # ------------------------------------------------------------------ #

    def bulk_import(
        self, yaml_content: str, user: str = "system"
    ) -> Tuple[int, Optional[str]]:
        """Import entities from a YAML string. Returns (count_imported, error)."""
        parsed, err = YamlUtils.validate_yaml_string(yaml_content)
        if err:
            return 0, f"Invalid YAML: {err}"
        if not isinstance(parsed, dict):
            return 0, "Expected a YAML mapping of entity_id: {props}"

        count = 0
        for entity_id, props in parsed.items():
            if not isinstance(props, dict):
                props = {}
            entity = EntityConfig.from_dict(str(entity_id), props)
            save_err = self._repo.save_entity(entity)
            if save_err:
                logger.warning("Failed to import %s: %s", entity_id, save_err)
                continue
            count += 1

        self._audit.log(
            user=user,
            action="BULK_IMPORT",
            target="emulated_hue.entities",
            details=f"imported={count}",
        )
        return count, None

    # ------------------------------------------------------------------ #
    # Export
    # ------------------------------------------------------------------ #

    def export_yaml(self) -> Tuple[Optional[str], Optional[str]]:
        entities, err = self._repo.list_entities()
        if err:
            return None, err
        export_data = {e.entity_id: e.to_dict() for e in entities}
        try:
            content = yaml.dump(
                export_data,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=True,
            )
            return content, None
        except Exception as exc:  # noqa: BLE001
            return None, str(exc)

    # ------------------------------------------------------------------ #
    # Dashboard stats
    # ------------------------------------------------------------------ #

    def get_stats(self) -> Tuple[dict, Optional[str]]:
        entities, err = self._repo.list_entities()
        if err:
            return {}, err
        total = len(entities)
        hidden = sum(1 for e in entities if e.hidden)
        exposed = total - hidden
        return {"total": total, "exposed": exposed, "hidden": hidden}, None
