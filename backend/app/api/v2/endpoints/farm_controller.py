from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import Response

from app.api.dependencies.current_user import get_current_user
from app.api.dependencies.farm import get_farm_service
from app.models.user import User
from app.schemas.farm_schema import FarmCreateRequest, FarmFileResponse, FarmFileUrlResponse, FarmListResponse, FarmResponse, FarmUpdateRequest, MessageResponse
from app.services.exceptions import ConflictError, ForbiddenOperationError, ResourceAlreadyExistsError, ResourceNotFoundError, ValidationError
from app.services.farm_service import FarmService

router = APIRouter(prefix="/farms", tags=["Farms"])


def _raise(exc: Exception) -> None:
    if isinstance(exc, ForbiddenOperationError): raise HTTPException(403, str(exc)) from exc
    if isinstance(exc, ResourceNotFoundError): raise HTTPException(404, str(exc)) from exc
    if isinstance(exc, (ConflictError, ResourceAlreadyExistsError)): raise HTTPException(409, str(exc)) from exc
    if isinstance(exc, ValidationError): raise HTTPException(422, str(exc)) from exc
    raise exc


@router.get("", response_model=FarmListResponse)
async def list_my_farms(offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100), current_user: User = Depends(get_current_user), service: FarmService = Depends(get_farm_service)) -> FarmListResponse:
    try:
        items, total = await service.list_farms(current_user=current_user, offset=offset, limit=limit)
        return FarmListResponse(items=items, total=total, offset=offset, limit=limit)
    except Exception as exc: _raise(exc)
    raise AssertionError


@router.post("", response_model=FarmResponse, status_code=status.HTTP_201_CREATED)
async def create_my_farm(payload: FarmCreateRequest, current_user: User = Depends(get_current_user), service: FarmService = Depends(get_farm_service)) -> FarmResponse:
    try: return await service.create_farm(current_user=current_user, farm_data=payload.model_dump(exclude_unset=True))
    except Exception as exc: _raise(exc)
    raise AssertionError


@router.get("/{farm_public_id}", response_model=FarmResponse)
async def get_my_farm(farm_public_id: UUID, current_user: User = Depends(get_current_user), service: FarmService = Depends(get_farm_service)) -> FarmResponse:
    try: return await service.get_farm(current_user=current_user, farm_public_id=farm_public_id)
    except Exception as exc: _raise(exc)
    raise AssertionError


@router.patch("/{farm_public_id}", response_model=FarmResponse)
async def update_my_farm(farm_public_id: UUID, payload: FarmUpdateRequest, current_user: User = Depends(get_current_user), service: FarmService = Depends(get_farm_service)) -> FarmResponse:
    try: return await service.update_farm(current_user=current_user, farm_public_id=farm_public_id, farm_data=payload.model_dump(exclude_unset=True))
    except Exception as exc: _raise(exc)
    raise AssertionError


@router.post("/{farm_public_id}/file", response_model=FarmResponse, status_code=status.HTTP_200_OK)
async def upload_farm_file(farm_public_id: UUID, file: UploadFile = File(...), current_user: User = Depends(get_current_user), service: FarmService = Depends(get_farm_service)) -> FarmResponse:
    try:
        data = await file.read()
        return await service.upload_farm_file(current_user=current_user, farm_public_id=farm_public_id, file_bytes=data, content_type=file.content_type or "")
    except Exception as exc: _raise(exc)
    finally: await file.close()


@router.put("/{farm_public_id}/file", response_model=FarmResponse)
async def replace_farm_file(farm_public_id: UUID, file: UploadFile = File(...), current_user: User = Depends(get_current_user), service: FarmService = Depends(get_farm_service)) -> FarmResponse:
    try:
        data = await file.read()
        return await service.replace_farm_file(current_user=current_user, farm_public_id=farm_public_id, file_bytes=data, content_type=file.content_type or "")
    except Exception as exc: _raise(exc)
    finally: await file.close()


@router.get("/{farm_public_id}/file", response_model=FarmFileResponse)
async def get_farm_file(farm_public_id: UUID, current_user: User = Depends(get_current_user), service: FarmService = Depends(get_farm_service)) -> FarmFileResponse:
    try:
        farm, url, _ = await service.get_farm_file_url(current_user=current_user, farm_public_id=farm_public_id)
        return FarmFileResponse(farm=farm, farm_file_url=url)
    except Exception as exc: _raise(exc)
    raise AssertionError


@router.get("/{farm_public_id}/file/download")
async def download_farm_file(farm_public_id: UUID, current_user: User = Depends(get_current_user), service: FarmService = Depends(get_farm_service)) -> Response:
    try:
        farm, data, content_type = await service.download_farm_file(current_user=current_user, farm_public_id=farm_public_id)
        filename = farm.farm_file_path.rsplit("/", 1)[-1] if farm.farm_file_path else "farm-file"
        return Response(content=data, media_type=content_type, headers={"Content-Disposition": f'attachment; filename="{filename}"'})
    except Exception as exc: _raise(exc)
    raise AssertionError


@router.delete("/{farm_public_id}/file", response_model=MessageResponse)
async def delete_farm_file(farm_public_id: UUID, current_user: User = Depends(get_current_user), service: FarmService = Depends(get_farm_service)) -> MessageResponse:
    try:
        await service.delete_farm_file(current_user=current_user, farm_public_id=farm_public_id)
        return MessageResponse(message="Farm file deleted successfully.")
    except Exception as exc: _raise(exc)
    raise AssertionError


@router.delete("/{farm_public_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_farm(farm_public_id: UUID, current_user: User = Depends(get_current_user), service: FarmService = Depends(get_farm_service)) -> None:
    try: await service.delete_farm(current_user=current_user, farm_public_id=farm_public_id)
    except Exception as exc: _raise(exc)
