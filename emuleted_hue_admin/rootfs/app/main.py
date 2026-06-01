"""Emulated Hue Manager — FastAPI application entry point."""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .api.routes import (
    audit_router,
    backup_router,
    config_router,
    dashboard_router,
    diagnostics_router,
    entities_router,
    reload_router,
)
from .api.dependencies import get_repository
from .utils.logger import get_logger

logger = get_logger("emulated_hue_manager")

FRONTEND_DIR = Path(__file__).parent / "frontend"


def _migrate_strip_invalid_entity_keys() -> None:
    """One-shot migration: remove keys unsupported by HA emulated_hue (e.g. 'type')
    from the entities block, so HA config validation does not reject the restart."""
    try:
        repo = get_repository()
        entities, err = repo.list_entities()
        if err or not entities:
            return
        # Re-save each entity — save_entity() already calls _sanitize_entity_dict()
        for entity in entities:
            save_err = repo.save_entity(entity)
            if save_err:
                logger.warning("Migration: could not re-save %s: %s", entity.entity_id, save_err)
                return
        logger.info("Migration: stripped invalid entity keys from %d entities.", len(entities))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Migration skipped: %s", exc)


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Emulated Hue Manager started.")
    logger.info(
        "Configuration path: %s",
        os.getenv("HA_CONFIG_PATH", "/homeassistant/configuration.yaml"),
    )
    _migrate_strip_invalid_entity_keys()
    yield
    logger.info("Emulated Hue Manager stopped.")


app = FastAPI(
    title="Emulated Hue Manager",
    description="Home Assistant Add-on for managing Emulated Hue configuration",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# CORS — allow HA Ingress and local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers
app.include_router(dashboard_router)
app.include_router(config_router)
app.include_router(entities_router)
app.include_router(backup_router)
app.include_router(diagnostics_router)
app.include_router(reload_router)
app.include_router(audit_router)

# Serve frontend static files
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
