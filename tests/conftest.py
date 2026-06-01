"""Pytest configuration and shared fixtures."""
import shutil
import tempfile
from pathlib import Path

import pytest
import yaml

from emuleted_hue_admin.rootfs.app.repositories.yaml_repository import YamlConfigRepository
from emuleted_hue_admin.rootfs.app.utils.audit import AuditLogger


SAMPLE_CONFIG = {
    "homeassistant": {"name": "Test HA"},
    "emulated_hue": {
        "host_ip": "192.168.1.50",
        "listen_port": 80,
        "expose_by_default": True,
        "upnp_bind_multicast": True,
        "off_maps_to_on_domains": ["script", "scene"],
        "exposed_domains": ["light", "switch"],
        "entities": {
            "light.sala": {"name": "Sala", "hidden": False, "type": "light"},
            "switch.quarto": {"name": "Quarto", "hidden": True},
        },
    },
}


@pytest.fixture
def tmp_dir():
    d = tempfile.mkdtemp()
    yield Path(d)
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def config_yaml(tmp_dir):
    p = tmp_dir / "configuration.yaml"
    p.write_text(yaml.dump(SAMPLE_CONFIG, allow_unicode=True))
    return p


@pytest.fixture
def backup_dir(tmp_dir):
    b = tmp_dir / "backups"
    b.mkdir()
    return b


@pytest.fixture
def repository(config_yaml, backup_dir):
    return YamlConfigRepository(config_path=config_yaml, backup_dir=backup_dir)


@pytest.fixture
def audit_logger(tmp_dir):
    return AuditLogger(path=tmp_dir / "audit.jsonl")
