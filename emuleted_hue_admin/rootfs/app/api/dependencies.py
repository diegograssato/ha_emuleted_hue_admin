"""Dependency injection container for FastAPI."""
from __future__ import annotations

from functools import lru_cache

from ..repositories.yaml_repository import YamlConfigRepository
from ..services.backup_service import BackupService
from ..services.config_service import ConfigService
from ..services.diagnostics_service import DiagnosticsService
from ..services.entity_service import EntityService
from ..services.ha_service import HAService
from ..utils.audit import AuditLogger


@lru_cache(maxsize=1)
def get_repository() -> YamlConfigRepository:
    return YamlConfigRepository()


@lru_cache(maxsize=1)
def get_audit_logger() -> AuditLogger:
    return AuditLogger()


@lru_cache(maxsize=1)
def get_config_service() -> ConfigService:
    return ConfigService(repository=get_repository(), audit_logger=get_audit_logger())


@lru_cache(maxsize=1)
def get_entity_service() -> EntityService:
    return EntityService(repository=get_repository(), audit_logger=get_audit_logger())


@lru_cache(maxsize=1)
def get_backup_service() -> BackupService:
    return BackupService(repository=get_repository(), audit_logger=get_audit_logger())


@lru_cache(maxsize=1)
def get_diagnostics_service() -> DiagnosticsService:
    return DiagnosticsService()


@lru_cache(maxsize=1)
def get_ha_service() -> HAService:
    return HAService()
