"""Integration tests for the FastAPI application."""
import shutil
import tempfile
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

# Patch environment before importing app
import os

SAMPLE_CONFIG = {
    "emulated_hue": {
        "host_ip": "192.168.1.50",
        "listen_port": 80,
        "expose_by_default": True,
        "upnp_bind_multicast": True,
        "off_maps_to_on_domains": ["script"],
        "exposed_domains": ["light", "switch"],
        "entities": {
            "light.sala": {"name": "Sala", "hidden": False, "type": "light"},
        },
    }
}


@pytest.fixture(scope="module")
def client():
    tmp = tempfile.mkdtemp()
    cfg_path = Path(tmp) / "configuration.yaml"
    cfg_path.write_text(yaml.dump(SAMPLE_CONFIG, allow_unicode=True))
    backup_path = Path(tmp) / "backups"
    backup_path.mkdir()
    os.environ["HA_CONFIG_PATH"] = str(cfg_path)
    os.environ["HA_BACKUP_DIR"] = str(backup_path)

    from emuleted_hue_admin.rootfs.app.api.dependencies import (
        get_repository, get_audit_logger,
        get_config_service, get_entity_service,
        get_backup_service, get_diagnostics_service, get_ha_service,
    )
    for fn in [get_repository, get_audit_logger, get_config_service,
               get_entity_service, get_backup_service, get_diagnostics_service, get_ha_service]:
        fn.cache_clear()

    from emuleted_hue_admin.rootfs.app.main import app
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c

    shutil.rmtree(tmp, ignore_errors=True)


class TestDashboardAPI:
    def test_dashboard_ok(self, client):
        r = client.get("/api/dashboard")
        assert r.status_code == 200
        data = r.json()
        assert "total_entities" in data
        assert data["host_ip"] == "192.168.1.50"


class TestConfigAPI:
    def test_get_config(self, client):
        r = client.get("/api/config")
        assert r.status_code == 200
        data = r.json()
        assert data["host_ip"] == "192.168.1.50"
        assert data["listen_port"] == 80

    def test_update_config(self, client):
        r = client.put("/api/config", json={"host_ip": "10.0.0.99", "listen_port": 8080})
        assert r.status_code == 200
        data = r.json()
        assert data["host_ip"] == "10.0.0.99"
        assert data["listen_port"] == 8080


class TestEntitiesAPI:
    def test_list_entities(self, client):
        r = client.get("/api/entities")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= 1
        assert "items" in data

    def test_create_entity(self, client):
        r = client.post("/api/entities", json={
            "entity_id": "switch.test_switch",
            "name": "Test Switch",
            "hidden": False,
            "type": "switch",
        })
        assert r.status_code == 201
        data = r.json()
        assert data["entity_id"] == "switch.test_switch"

    def test_create_duplicate_entity_conflict(self, client):
        client.post("/api/entities", json={"entity_id": "light.dup_test"})
        r = client.post("/api/entities", json={"entity_id": "light.dup_test"})
        assert r.status_code == 409

    def test_get_entity(self, client):
        r = client.get("/api/entities/light.sala")
        assert r.status_code == 200
        assert r.json()["entity_id"] == "light.sala"

    def test_get_missing_entity_404(self, client):
        r = client.get("/api/entities/sensor.ghost_missing")
        assert r.status_code == 404

    def test_update_entity(self, client):
        r = client.put("/api/entities/light.sala", json={"name": "Sala Updated", "hidden": True})
        assert r.status_code == 200
        assert r.json()["name"] == "Sala Updated"
        assert r.json()["hidden"] is True

    def test_delete_entity(self, client):
        client.post("/api/entities", json={"entity_id": "fan.to_delete"})
        r = client.delete("/api/entities/fan.to_delete")
        assert r.status_code == 200
        r2 = client.get("/api/entities/fan.to_delete")
        assert r2.status_code == 404


class TestYamlEditorAPI:
    def test_get_yaml(self, client):
        r = client.get("/api/config/yaml")
        assert r.status_code == 200
        data = r.json()
        assert "emulated_hue" in data["yaml_content"]
        assert data["is_valid"] is True

    def test_save_valid_yaml(self, client):
        yaml_content = """emulated_hue:
  host_ip: "1.2.3.4"
  listen_port: 9000
  expose_by_default: true
  upnp_bind_multicast: true
  off_maps_to_on_domains: []
  exposed_domains:
    - light
"""
        r = client.put("/api/config/yaml", json={"yaml_content": yaml_content})
        assert r.status_code == 200

    def test_save_invalid_yaml_422(self, client):
        r = client.put("/api/config/yaml", json={"yaml_content": "key: [unclosed bracket"})
        assert r.status_code == 422


class TestBackupAPI:
    def test_create_backup(self, client):
        r = client.post("/api/backup")
        assert r.status_code == 200
        data = r.json()
        assert "filename" in data
        assert data["filename"].startswith("emulated_hue_backup_")

    def test_list_backups(self, client):
        client.post("/api/backup")
        r = client.get("/api/backup/list")
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        assert len(r.json()) >= 1


class TestAuditAPI:
    def test_get_audit_log(self, client):
        r = client.get("/api/audit")
        assert r.status_code == 200
        assert isinstance(r.json(), list)


class TestEmulatedHueStatusAPI:
    def test_status_when_component_not_loaded(self, client):
        """Quando o Supervisor não está disponível, component_loaded=False e suggestion contém o guia."""
        r = client.get("/api/dashboard/status")
        assert r.status_code == 200
        data = r.json()
        assert "component_loaded" in data
        # Em ambiente de testes sem Supervisor, o componente nunca está carregado
        assert data["component_loaded"] is False
        assert data["suggestion"] is not None
        assert "emulated_hue:" in data["suggestion"]

    def test_status_when_component_loaded(self, client, monkeypatch):
        """Quando o Supervisor retorna emulated_hue em components, component_loaded=True."""
        from emuleted_hue_admin.rootfs.app.services.ha_service import HAService

        def fake_check(self):
            return {"component_loaded": True, "suggestion": None}

        monkeypatch.setattr(HAService, "check_emulated_hue_installed", fake_check)
        r = client.get("/api/dashboard/status")
        assert r.status_code == 200
        data = r.json()
        assert data["component_loaded"] is True
        assert data["suggestion"] is None
