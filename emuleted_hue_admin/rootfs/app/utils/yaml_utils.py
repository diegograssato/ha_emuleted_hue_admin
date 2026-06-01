"""YAML utility functions with safety wrappers."""
from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Optional, Tuple

import yaml

from .logger import get_logger

logger = get_logger(__name__)


def _build_ha_loader() -> type:
    """Return a yaml.SafeLoader subclass that tolerates HA custom tags.

    Home Assistant configuration.yaml uses tags like !include, !secret,
    !include_dir_list, etc.  Standard SafeLoader raises a constructor error
    on unknown tags.  This loader replaces every unknown tag with a plain
    string so we can still parse the rest of the document.
    """

    class HaSafeLoader(yaml.SafeLoader):  # pylint: disable=too-many-ancestors
        pass

    def _ignore_tag(loader: yaml.Loader, tag_suffix: str, node: yaml.Node) -> str:
        """Return a placeholder string for any unrecognised tag."""
        if isinstance(node, yaml.ScalarNode):
            return loader.construct_scalar(node)  # type: ignore[arg-type]
        if isinstance(node, yaml.SequenceNode):
            return loader.construct_sequence(node)  # type: ignore[arg-type]
        return loader.construct_mapping(node)  # type: ignore[arg-type]

    # Register a catch-all multi-constructor for every tag starting with "!"
    HaSafeLoader.add_multi_constructor("", _ignore_tag)

    return HaSafeLoader


_HA_LOADER = _build_ha_loader()


class YamlUtils:
    """Safe YAML read/write operations with backup support."""

    @staticmethod
    def safe_load(path: Path) -> Tuple[Optional[dict], Optional[str]]:
        """Load YAML file. Returns (data, error)."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.load(f, Loader=_HA_LOADER)
                return data or {}, None
        except FileNotFoundError:
            logger.warning("YAML file not found: %s", path)
            return {}, None
        except yaml.YAMLError as exc:
            logger.error("YAML parse error in %s: %s", path, exc)
            return None, str(exc)
        except OSError as exc:
            logger.error("OS error reading %s: %s", path, exc)
            return None, str(exc)

    @staticmethod
    def safe_dump(path: Path, data: dict) -> Optional[str]:
        """Write YAML file atomically. Returns error string or None."""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = path.with_suffix(".tmp")
            with open(tmp_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    data,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,
                )
            shutil.move(str(tmp_path), str(path))
            return None
        except OSError as exc:
            logger.error("OS error writing %s: %s", path, exc)
            return str(exc)

    @staticmethod
    def update_yaml_section(
        path: Path,
        section_key: str,
        section_data: dict,
    ) -> Optional[str]:
        """Update only *section_key* in a YAML file, leaving all other content
        (including comments, blank lines, and unrelated keys) intact.

        On the first call the existing bare key block is located by column-0
        detection and replaced; on subsequent calls the ``# --- BEGIN/END ---``
        markers are used for fast in-place replacement.
        """
        begin_marker = f"# --- BEGIN {section_key} ---"
        end_marker = f"# --- END {section_key} ---"

        section_yaml = yaml.dump(
            {section_key: section_data},
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )
        new_block = f"{begin_marker}\n{section_yaml}{end_marker}\n"

        try:
            text = path.read_text(encoding="utf-8") if path.exists() else ""
        except OSError as exc:
            return str(exc)

        if begin_marker in text and end_marker in text:
            # Fast path: replace between existing markers (inclusive)
            b_start = text.index(begin_marker)
            e_end = text.index(end_marker) + len(end_marker)
            if e_end < len(text) and text[e_end] == "\n":
                e_end += 1
            new_text = text[:b_start] + new_block + text[e_end:]
        else:
            # Locate the key at column 0 and replace its indented block
            lines = text.splitlines(keepends=True)
            sec_start = None
            for i, line in enumerate(lines):
                stripped = line.rstrip("\n\r")
                if stripped == f"{section_key}:" or stripped.startswith(f"{section_key}:"):
                    if stripped and not stripped[0].isspace():
                        sec_start = i
                        break
            if sec_start is not None:
                sec_end = len(lines)
                for i in range(sec_start + 1, len(lines)):
                    ln = lines[i].rstrip("\n\r")
                    if ln and not ln[0].isspace():
                        sec_end = i
                        break
                before = "".join(lines[:sec_start])
                after = "".join(lines[sec_end:])
                new_text = before + new_block + after
            else:
                # Key not present: append
                new_text = (text.rstrip("\n") + "\n" if text else "") + new_block

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = path.with_suffix(".tmp")
            tmp_path.write_text(new_text, encoding="utf-8")
            shutil.move(str(tmp_path), str(path))
            return None
        except OSError as exc:
            logger.error("OS error writing section %s in %s: %s", section_key, path, exc)
            return str(exc)

    @staticmethod
    def validate_yaml_string(content: str) -> Tuple[Optional[Any], Optional[str]]:
        """Validate a YAML string. Returns (parsed_data, error)."""
        try:
            data = yaml.safe_load(content)
            return data, None
        except yaml.YAMLError as exc:
            return None, str(exc)

    @staticmethod
    def backup(source_path: Path, backup_dir: Path) -> Tuple[Optional[Path], Optional[str]]:
        """Create a timestamped backup of source YAML file."""
        try:
            backup_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            filename = f"emulated_hue_backup_{timestamp}.yaml"
            dest = backup_dir / filename
            shutil.copy2(str(source_path), str(dest))
            logger.info("Backup created: %s", dest)
            return dest, None
        except OSError as exc:
            logger.error("Backup failed: %s", exc)
            return None, str(exc)
