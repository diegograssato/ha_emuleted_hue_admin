"""Unit tests for EntityService."""
import pytest

from emuleted_hue_admin.rootfs.app.schemas.entity import EntityCreate, EntityUpdate
from emuleted_hue_admin.rootfs.app.services.entity_service import EntityService


@pytest.fixture
def entity_service(repository, audit_logger):
    return EntityService(repository=repository, audit_logger=audit_logger)


class TestEntityServiceList:
    def test_list_default_pagination(self, entity_service):
        result, err = entity_service.list_entities()
        assert err is None
        assert result.total == 2
        assert result.page == 1
        assert result.page_size == 25

    def test_list_filter_by_hidden_true(self, entity_service):
        result, err = entity_service.list_entities(hidden=True)
        assert err is None
        assert result.total == 1
        assert result.items[0].entity_id == "switch.quarto"

    def test_list_filter_by_hidden_false(self, entity_service):
        result, err = entity_service.list_entities(hidden=False)
        assert err is None
        assert result.total == 1
        assert result.items[0].entity_id == "light.sala"

    def test_list_filter_by_domain(self, entity_service):
        result, err = entity_service.list_entities(domain="light")
        assert err is None
        assert result.total == 1

    def test_list_search_by_name(self, entity_service):
        result, err = entity_service.list_entities(search="sala")
        assert err is None
        assert result.total == 1
        assert result.items[0].entity_id == "light.sala"

    def test_list_pagination(self, entity_service):
        result, err = entity_service.list_entities(page=1, page_size=1)
        assert err is None
        assert result.total == 2
        assert len(result.items) == 1


class TestEntityServiceCRUD:
    def test_create_entity(self, entity_service):
        payload = EntityCreate(entity_id="fan.ventilador", name="Ventilador", hidden=False)
        created, err = entity_service.create_entity(payload, user="test")
        assert err is None
        assert created.entity_id == "fan.ventilador"

    def test_create_duplicate_entity_fails(self, entity_service):
        payload = EntityCreate(entity_id="light.sala", name="Sala Dup")
        _, err = entity_service.create_entity(payload, user="test")
        assert err is not None
        assert "already exists" in err

    def test_update_entity(self, entity_service):
        update = EntityUpdate(name="Sala Updated", hidden=True)
        updated, err = entity_service.update_entity("light.sala", update, user="test")
        assert err is None
        assert updated.name == "Sala Updated"
        assert updated.hidden is True

    def test_update_missing_entity_returns_none(self, entity_service):
        update = EntityUpdate(name="ghost")
        result, err = entity_service.update_entity("sensor.ghost", update)
        assert err is None
        assert result is None

    def test_delete_entity(self, entity_service):
        deleted, err = entity_service.delete_entity("switch.quarto", user="test")
        assert err is None
        assert deleted is True
        entity, _ = entity_service.get_entity("switch.quarto")
        assert entity is None

    def test_delete_missing_entity(self, entity_service):
        deleted, err = entity_service.delete_entity("sensor.ghost", user="test")
        assert err is None
        assert deleted is False

    def test_duplicate_entity(self, entity_service):
        result, err = entity_service.duplicate_entity("light.sala", "light.sala_copia", user="test")
        assert err is None
        assert result.entity_id == "light.sala_copia"
        assert result.name == "Sala"

    def test_get_stats(self, entity_service):
        stats, err = entity_service.get_stats()
        assert err is None
        assert stats["total"] == 2
        assert stats["hidden"] == 1
        assert stats["exposed"] == 1


class TestBulkImport:
    def test_bulk_import_valid_yaml(self, entity_service):
        yaml_content = """
cover.portao:
  name: "Portão"
  hidden: false
  type: cover
scene.jantar:
  name: "Jantar"
"""
        count, err = entity_service.bulk_import(yaml_content, user="test")
        assert err is None
        assert count == 2

    def test_bulk_import_invalid_yaml(self, entity_service):
        # Use YAML with actual syntax error
        count, err = entity_service.bulk_import("key: [unclosed bracket", user="test")
        assert err is not None
        assert count == 0
