"""Routes: backup and restore."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from fastapi.responses import FileResponse

from ...schemas.common import BackupResponse, MessageResponse
from ...services.backup_service import BackupService
from ..dependencies import get_backup_service

router = APIRouter(prefix="/api/backup", tags=["backup"])


def _user(request: Request) -> str:
    return request.headers.get("X-Remote-User", "system")


@router.post("", response_model=BackupResponse)
async def create_backup(
    request: Request,
    service: BackupService = Depends(get_backup_service),
) -> BackupResponse:
    result, err = service.create_backup(user=_user(request))
    if err:
        raise HTTPException(status_code=500, detail=err)
    return BackupResponse(**result)


@router.get("/list")
async def list_backups(
    service: BackupService = Depends(get_backup_service),
) -> list:
    return service.list_backups()


@router.get("/download-config")
async def download_config(
    service: BackupService = Depends(get_backup_service),
) -> FileResponse:
    """Download the current configuration.yaml."""
    path, err = service.get_config_path()
    if err:
        raise HTTPException(status_code=404, detail=err)
    return FileResponse(
        path=str(path),
        media_type="application/x-yaml",
        filename="configuration.yaml",
        headers={"Content-Disposition": 'attachment; filename="configuration.yaml"'},
    )


@router.get("/download/{filename}")
async def download_backup(
    filename: str,
    service: BackupService = Depends(get_backup_service),
) -> FileResponse:
    """Download a specific backup file by name."""
    path, err = service.get_backup_file(filename)
    if err:
        raise HTTPException(status_code=404, detail=err)
    safe_name = path.name  # type: ignore[union-attr]
    return FileResponse(
        path=str(path),
        media_type="application/x-yaml",
        filename=safe_name,
        headers={"Content-Disposition": f'attachment; filename="{safe_name}"'},
    )


@router.post("/restore", response_model=MessageResponse)
async def restore_backup(
    request: Request,
    file: UploadFile = File(...),
    service: BackupService = Depends(get_backup_service),
) -> MessageResponse:
    if not file.filename or not file.filename.endswith(".yaml"):
        raise HTTPException(
            status_code=400, detail="Only .yaml files are accepted for restore."
        )

    # Read and size-limit the file (max 5MB)
    max_size = 5 * 1024 * 1024
    content_bytes = await file.read(max_size + 1)
    if len(content_bytes) > max_size:
        raise HTTPException(status_code=413, detail="File too large (max 5 MB).")

    yaml_content = content_bytes.decode("utf-8", errors="replace")
    err = service.restore_from_content(yaml_content, user=_user(request))
    if err:
        raise HTTPException(status_code=422, detail=err)
    return MessageResponse(message="Configuration restored successfully.")
