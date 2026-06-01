"""BackupService — creates and restores YAML backups."""
from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path
from typing import List, Optional, Tuple

from ..repositories.yaml_repository import YamlConfigRepository
from ..utils.audit import AuditLogger
from ..utils.logger import get_logger
from ..utils.yaml_utils import YamlUtils

logger = get_logger(__name__)


class BackupService:
    """Handles backup generation and restore from file upload."""

    def __init__(
        self,
        repository: YamlConfigRepository,
        audit_logger: AuditLogger,
    ) -> None:
        self._repo = repository
        self._audit = audit_logger

    def create_backup(self, user: str = "system") -> Tuple[Optional[dict], Optional[str]]:
        dest, err = YamlUtils.backup(self._repo.config_path, self._repo.backup_dir)
        if err:
            return None, err

        stat = dest.stat()
        self._audit.log(user=user, action="BACKUP", target=str(dest))

        return {
            "filename": dest.name,
            "path": str(dest),
            "size_bytes": stat.st_size,
            "created_at": datetime.fromtimestamp(stat.st_mtime, UTC).isoformat(
                sep=" ", timespec="seconds"
            ),
        }, None

    def list_backups(self) -> List[dict]:
        backup_dir = self._repo.backup_dir
        if not backup_dir.exists():
            return []
        backups = []
        for f in sorted(backup_dir.glob("emulated_hue_backup_*.yaml"), reverse=True):
            stat = f.stat()
            backups.append(
                {
                    "filename": f.name,
                    "path": str(f),
                    "size_bytes": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_mtime, UTC).isoformat(
                        sep=" ", timespec="seconds"
                    ),
                }
            )
        return backups

    def restore_from_content(
        self, yaml_content: str, user: str = "system"
    ) -> Optional[str]:
        """Restore configuration from uploaded YAML content."""
        parsed, err = YamlUtils.validate_yaml_string(yaml_content)
        if err:
            return f"Invalid YAML: {err}"
        if not isinstance(parsed, dict):
            return "Restore content must be a YAML mapping."

        # Create backup of current state before restore
        YamlUtils.backup(self._repo.config_path, self._repo.backup_dir)

        save_err = YamlUtils.safe_dump(self._repo.config_path, parsed)
        if save_err:
            return save_err

        self._audit.log(
            user=user,
            action="RESTORE",
            target="configuration.yaml",
            details="Restored from uploaded YAML",
        )
        return None

    def get_backup_file(self, filename: str) -> Tuple[Optional[Path], Optional[str]]:
        """Return the path of a backup file, guarding against path traversal."""
        safe_name = Path(filename).name
        if safe_name != filename or not safe_name.endswith(".yaml"):
            return None, "Nome de arquivo inválido."
        path = self._repo.backup_dir / safe_name
        if not path.exists():
            return None, f"Arquivo de backup não encontrado: {safe_name}"
        return path, None

    def get_config_path(self) -> Tuple[Optional[Path], Optional[str]]:
        """Return the config.yaml path if it exists."""
        path = self._repo.config_path
        if not path.exists():
            return None, "Arquivo de configuração não encontrado."
        return path, None
