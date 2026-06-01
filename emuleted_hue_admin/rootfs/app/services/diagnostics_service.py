"""DiagnosticsService — checks Alexa/Emulated Hue discoverability."""
from __future__ import annotations

import socket
import urllib.request
import xml.etree.ElementTree as ET
from typing import Optional, Tuple

from ..utils.logger import get_logger

logger = get_logger(__name__)

REQUEST_TIMEOUT = 5  # seconds


class DiagnosticsService:
    """Validates that the Emulated Hue UPnP endpoint is reachable."""

    def run(
        self, host_ip: Optional[str], listen_port: Optional[int]
    ) -> dict:
        ip = host_ip or "127.0.0.1"
        port = listen_port or 80
        description_url = f"http://{ip}:{port}/description.xml"

        port_open = self._check_port(ip, port)
        reachable, xml_valid, friendly_name, fetch_error = self._fetch_description(
            description_url
        )

        return {
            "description_xml_url": description_url,
            "reachable": reachable,
            "port_open": port_open,
            "xml_valid": xml_valid,
            "friendly_name": friendly_name,
            "error": fetch_error,
        }

    def _check_port(self, host: str, port: int) -> bool:
        try:
            with socket.create_connection((host, port), timeout=REQUEST_TIMEOUT):
                return True
        except OSError:
            return False

    def _fetch_description(
        self, url: str
    ) -> Tuple[bool, bool, Optional[str], Optional[str]]:
        try:
            with urllib.request.urlopen(url, timeout=REQUEST_TIMEOUT) as resp:  # noqa: S310
                if resp.status != 200:
                    return True, False, None, f"HTTP {resp.status}"
                body = resp.read().decode("utf-8", errors="replace")
                xml_valid, friendly_name = self._parse_description(body)
                return True, xml_valid, friendly_name, None
        except Exception as exc:  # noqa: BLE001
            logger.warning("Diagnostics fetch failed: %s", exc)
            return False, False, None, str(exc)

    def _parse_description(self, body: str) -> Tuple[bool, Optional[str]]:
        try:
            root = ET.fromstring(body)  # noqa: S314
            ns = {"d": "urn:schemas-upnp-org:device-1-0"}
            friendly_name = root.findtext(".//d:friendlyName", namespaces=ns)
            return True, friendly_name
        except ET.ParseError as exc:
            logger.warning("XML parse error: %s", exc)
            return False, None
