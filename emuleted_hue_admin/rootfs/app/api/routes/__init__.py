"""API routes package."""
from .config import router as config_router
from .entities import router as entities_router
from .backup import router as backup_router
from .diagnostics import router as diagnostics_router
from .reload import router as reload_router
from .dashboard import router as dashboard_router
from .audit import router as audit_router

__all__ = [
    "config_router",
    "entities_router",
    "backup_router",
    "diagnostics_router",
    "reload_router",
    "dashboard_router",
    "audit_router",
]
