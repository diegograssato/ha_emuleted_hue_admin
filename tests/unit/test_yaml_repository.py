"""Unit tests for YamlConfigRepository."""
import pytest
import yaml

from emuleted_hue_admin.rootfs.app.models.config import EmulatedHueConfig
from emuleted_hue_admin.rootfs.app.models.entity import EntityConfig


class TestGetConfig:
    def test_reads_config(self, repository):
        config, err = repository.get_config()
        assert err is None
        assert config is not None
        assert config.host_ip == "192.168.1.50"
        assert config.listen_port == 80
        assert config.expose_by_default is True

    def test_returns_default_if_key_missing(self, tmp_dir):
        from emuleted_hue_admin.rootfs.app.repositories.yaml_repository import YamlConfigRepository
        p = tmp_dir / "config.yaml"
        p.write_text("homeassistant:\n  name: Test\n")
        repo = YamlConfigRepository(config_path=p, backup_dir=tmp_dir / "bk")
        config, err = repo.get_config()
        assert err is None
        assert config is not None
        assert config.expose_by_default is True  # default


class TestSaveConfig:
    def test_saves_config(self, repository, config_yaml):
        config = EmulatedHueConfig(
            host_ip="10.0.0.1",
            listen_port=8080,
            expose_by_default=False,
            upnp_bind_multicast=False,
            off_maps_to_on_domains=["script"],
            exposed_domains=["light"],
        )
        err = repository.save_config(config)
        assert err is None

        # Verify persisted
        with open(config_yaml) as f:
            data = yaml.safe_load(f)
        hue = data["emulated_hue"]
        assert hue["host_ip"] == "10.0.0.1"
        assert hue["listen_port"] == 8080
        assert hue["expose_by_default"] is False

    def test_preserves_entities_on_config_save(self, repository, config_yaml):
        config = EmulatedHueConfig(host_ip="1.2.3.4")
        repository.save_config(config)

        with open(config_yaml) as f:
            data = yaml.safe_load(f)
        assert "light.sala" in data["emulated_hue"]["entities"]


class TestEntityCRUD:
    def test_list_entities(self, repository):
        entities, err = repository.list_entities()
        assert err is None
        assert len(entities) == 2
        ids = {e.entity_id for e in entities}
        assert "light.sala" in ids
        assert "switch.quarto" in ids

    def test_get_entity_existing(self, repository):
        entity, err = repository.get_entity("light.sala")
        assert err is None
        assert entity is not None
        assert entity.name == "Sala"
        assert entity.hidden is False
        assert entity.entity_type == "light"

    def test_get_entity_missing_returns_none(self, repository):
        entity, err = repository.get_entity("sensor.nao_existe")
        assert err is None
        assert entity is None

    def test_save_new_entity(self, repository):
        entity = EntityConfig(
            entity_id="scene.jantar",
            name="Jantar",
            hidden=False,
            entity_type="scene",
        )
        err = repository.save_entity(entity)
        assert err is None

        saved, _ = repository.get_entity("scene.jantar")
        assert saved is not None
        assert saved.name == "Jantar"

    def test_delete_entity(self, repository):
        deleted, err = repository.delete_entity("light.sala")
        assert err is None
        assert deleted is True

        entity, _ = repository.get_entity("light.sala")
        assert entity is None

    def test_delete_nonexistent_entity(self, repository):
        deleted, err = repository.delete_entity("binary_sensor.ghost")
        assert err is None
        assert deleted is False


class TestRawYaml:
    def test_get_raw_yaml(self, repository):
        content, err = repository.get_raw_yaml()
        assert err is None
        assert "emulated_hue" in content
        assert "host_ip" in content

    def test_save_raw_yaml_valid(self, repository):
        yaml_content = """
emulated_hue:
  host_ip: "9.9.9.9"
  listen_port: 9090
  expose_by_default: false
  upnp_bind_multicast: true
  off_maps_to_on_domains:
    - script
  exposed_domains:
    - light
"""
        err = repository.save_raw_yaml(yaml_content)
        assert err is None
        config, _ = repository.get_config()
        assert config.host_ip == "9.9.9.9"

    def test_save_raw_yaml_invalid(self, repository):
        err = repository.save_raw_yaml("invalid: yaml: : :")
        assert err is not None
