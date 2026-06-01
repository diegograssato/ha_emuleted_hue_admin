"""HAService — interacts with Home Assistant Supervisor API."""
from __future__ import annotations

import http.client
import json
import os
import urllib.error
import urllib.request
from typing import Optional, Tuple

from ..utils.logger import get_logger

logger = get_logger(__name__)

HA_TOKEN_ENV = "SUPERVISOR_TOKEN"
SUPERVISOR_BASE = "http://supervisor"
REQUEST_TIMEOUT = 10


# Generic proxy/aiohttp 500 body fragments that indicate HA dropped the connection
# while restarting — these are NOT real application errors.
_PROXY_ERROR_FRAGMENTS = frozenset({
    "server got itself in trouble",
    "internal server error",
    "upstream connect error",
    "bad gateway",
    "service unavailable",
})


class HAService:
    """Calls the Home Assistant Supervisor REST API."""

    def __init__(self, token: Optional[str] = None) -> None:
        self._token = token or os.getenv(HA_TOKEN_ENV, "")

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    def _request(
        self, method: str, path: str, body: Optional[dict] = None,
        ignore_disconnect: bool = False,
    ) -> Tuple[Optional[dict], Optional[str]]:
        url = f"{SUPERVISOR_BASE}{path}"
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(
            url, data=data, headers=self._headers(), method=method
        )
        try:
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:  # noqa: S310
                content = resp.read().decode("utf-8")
                return json.loads(content) if content else {}, None
        except urllib.error.HTTPError as exc:
            if ignore_disconnect and exc.code == 500:
                # Try to read the error body — if it contains a meaningful message
                # HA explicitly rejected the request (e.g. config validation).
                # If the body is empty/unreadable the Supervisor proxy dropped the
                # connection because HA is already shutting down (treat as success).
                try:
                    body_raw = exc.read()
                    body = body_raw.decode("utf-8", errors="replace").strip() if body_raw else ""
                except Exception:
                    body = ""

                if body:
                    # Check if the body is just a generic proxy/aiohttp error
                    # (meaning HA dropped the connection while restarting)
                    body_lower = body.lower()
                    is_proxy_noise = any(frag in body_lower for frag in _PROXY_ERROR_FRAGMENTS)
                    if is_proxy_noise:
                        logger.info(
                            "HTTP 500 with generic proxy body [%s %s] — HA restarting: %r",
                            method, path, body[:120],
                        )
                        return {}, None

                    # Extract detail from JSON if possible
                    try:
                        detail = json.loads(body).get("message") or json.loads(body).get("detail") or body
                    except Exception:
                        detail = body
                    logger.error("Restart rejected by HA [%s %s]: %s", method, path, detail)
                    return None, detail

                logger.info(
                    "HTTP 500 with empty body on restart [%s %s] — HA likely restarting.",
                    method, path,
                )
                return {}, None

            msg = f"HTTP {exc.code}: {exc.reason}"
            logger.error("Supervisor API error [%s %s]: %s", method, path, msg)
            return None, msg
        except (
            http.client.RemoteDisconnected,
            ConnectionResetError,
            BrokenPipeError,
            ConnectionAbortedError,
        ) as exc:
            if ignore_disconnect:
                logger.info("Connection dropped during restart — likely successful: %s", exc)
                return {}, None
            logger.error("Supervisor API request failed: %s", exc)
            return None, str(exc)
        except urllib.error.URLError as exc:
            if ignore_disconnect and isinstance(
                exc.reason, (ConnectionResetError, BrokenPipeError, ConnectionAbortedError, OSError)
            ):
                logger.info("Connection dropped during restart — likely successful: %s", exc)
                return {}, None
            logger.error("Supervisor API request failed: %s", exc)
            return None, str(exc)
        except Exception as exc:  # noqa: BLE001
            if ignore_disconnect and any(
                s in str(exc).lower()
                for s in ("remote disconnected", "connection reset", "broken pipe", "econnreset")
            ):
                logger.info("Connection dropped during restart — likely successful: %s", exc)
                return {}, None
            logger.error("Supervisor API request failed: %s", exc)
            return None, str(exc)

    def reload_emulated_hue(self) -> Tuple[bool, Optional[str]]:
        """Restart HA Core by calling the homeassistant.restart service
        through the HA REST API (requires homeassistant_api: true).

        Falls back to the Supervisor /core/restart endpoint which needs
        hassio_role: manager.
        """
        # Primary: HA REST API service call — works with homeassistant_api: true
        _, err = self._request(
            "POST", "/core/api/services/homeassistant/restart", body={}, ignore_disconnect=True
        )
        if err is None:
            logger.info("HA Core restart triggered via homeassistant.restart service.")
            return True, None

        logger.warning("homeassistant.restart service failed (%s), trying Supervisor API.", err)

        # Fallback: Supervisor /core/restart (needs hassio_role: manager)
        _, err2 = self._request("POST", "/core/restart", ignore_disconnect=True)
        if err2 is None:
            logger.info("HA Core restart triggered via Supervisor API.")
            return True, None

        combined = f"REST API: {err} | Supervisor: {err2}"
        logger.error("All restart methods failed: %s", combined)
        return False, combined

    def get_ha_states(self) -> Tuple[Optional[list], Optional[str]]:
        """Fetch all entity states from HA REST API."""
        result, err = self._request("GET", "/core/api/states")
        if err:
            return None, err
        if isinstance(result, dict) and "data" in result:
            return result["data"], None
        if isinstance(result, list):
            return result, None
        return [], None

    def is_supervisor_available(self) -> bool:
        _, err = self._request("GET", "/info")
        return err is None

    def check_emulated_hue_installed(self) -> dict:
        """
        Verifica se o emulated_hue está configurado no configuration.yaml do HA.

        Retorna um dict com:
        - installed: bool — se a chave emulated_hue existe no config
        - enabled: bool — se há ao menos uma entrada configurada
        - component_loaded: bool — se o componente está carregado no core
        - suggestion: str | None — mensagem de instalação caso não esteja presente
        """
        # Verifica se o componente está carregado via API de configuração do core
        result, err = self._request("GET", "/core/api/config")
        component_loaded = False
        if err is None and isinstance(result, dict):
            components = result.get("components", [])
            component_loaded = "emulated_hue" in components

        return {
            "component_loaded": component_loaded,
            "suggestion": None if component_loaded else (
                "O componente 'emulated_hue' não está carregado no Home Assistant. "
                "Adicione a seguinte configuração ao seu configuration.yaml e reinicie o HA:\n\n"
                "emulated_hue:\n"
                "  host_ip: 192.168.1.X\n"
                "  listen_port: 80\n"
                "  expose_by_default: false\n"
                "  exposed_domains:\n"
                "    - light\n"
                "    - switch\n"
                "    - scene\n"
                "    - script"
            ),
        }
