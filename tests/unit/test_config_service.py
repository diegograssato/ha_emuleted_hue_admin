"""Unit tests for ConfigService."""
import pytest

from emuleted_hue_admin.rootfs.app.schemas.config import ConfigUpdate
from emuleted_hue_admin.rootfs.app.services.config_service import ConfigService


@pytest.fixture
def config_service(repository, audit_logger):
    return ConfigService(repository=repository, audit_logger=audit_logger)


class TestConfigService:
    def test_get_config_returns_schema(self, config_service):
        config, err = config_service.get_config()
        assert err is None
        assert config is not None
        assert config.host_ip == "192.168.1.50"
        assert config.listen_port == 80

    def test_update_config_partial(self, config_service):
        update = ConfigUpdate(host_ip="10.10.10.10", listen_port=8080)
        updated, err = config_service.update_config(update, user="test_user")
        assert err is None
        assert updated.host_ip == "10.10.10.10"
        assert updated.listen_port == 8080
        # Untouched fields should remain
        assert updated.expose_by_default is True

    def test_update_config_boolean_flags(self, config_service):
        update = ConfigUpdate(expose_by_default=False, upnp_bind_multicast=False)
        updated, err = config_service.update_config(update, user="test")
        assert err is None
        assert updated.expose_by_default is False
        assert updated.upnp_bind_multicast is False

    def test_update_config_domains(self, config_service):
        update = ConfigUpdate(exposed_domains=["light", "fan", "climate"])
        updated, err = config_service.update_config(update, user="test")
        assert err is None
        assert "fan" in updated.exposed_domains
        assert "climate" in updated.exposed_domains

    def test_save_raw_yaml_invalid(self, config_service):
        # Use YAML with actual syntax error (unclosed bracket)
        err = config_service.save_raw_yaml("key: [unclosed bracket", user="test")
        assert err is not None
