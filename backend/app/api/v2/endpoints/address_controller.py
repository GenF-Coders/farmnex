from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies.address import get_address_service
from app.api.dependencies.current_user import get_current_user
from app.models.user import User
from app.schemas.address_schema import (
    AddressCreateRequest,
    AddressListResponse,
    AddressResponse,
    AddressUpdateRequest,
)
from app.services.address_service import AddressService
from app.services.exceptions import (
    ConflictError,
    ResourceAlreadyExistsError,
    ResourceNotFoundError,
    ValidationError,
)


router = APIRouter(
    prefix="/addresses",
    tags=["Addresses"],
)


@router.get(
    "",
    response_model=AddressListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_my_addresses(
    offset: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    active_only: bool = Query(
        default=True,
    ),
    current_user: User = Depends(get_current_user),
    service: AddressService = Depends(get_address_service),
) -> AddressListResponse:
    items, total = await service.list_addresses(
        current_user=current_user,
        offset=offset,
        limit=limit,
        active_only=active_only,
    )

    return AddressListResponse(
        items=items,
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{address_public_id}",
    response_model=AddressResponse,
    status_code=status.HTTP_200_OK,
)
async def get_my_address(
    address_public_id: UUID,
    current_user: User = Depends(get_current_user),
    service: AddressService = Depends(get_address_service),
) -> AddressResponse:
    try:
        return await service.get_address(
            current_user=current_user,
            address_public_id=address_public_id,
        )

    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post(
    "",
    response_model=AddressResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_my_address(
    payload: AddressCreateRequest,
    current_user: User = Depends(get_current_user),
    service: AddressService = Depends(get_address_service),
) -> AddressResponse:
    try:
        return await service.create_address(
            current_user=current_user,
            data=payload.model_dump(exclude_unset=True),
        )

    except ResourceAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except ConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.patch(
    "/{address_public_id}",
    response_model=AddressResponse,
    status_code=status.HTTP_200_OK,
)
async def update_my_address(
    address_public_id: UUID,
    payload: AddressUpdateRequest,
    current_user: User = Depends(get_current_user),
    service: AddressService = Depends(get_address_service),
) -> AddressResponse:
    try:
        return await service.update_address(
            current_user=current_user,
            address_public_id=address_public_id,
            data=payload.model_dump(exclude_unset=True),
        )

    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except ResourceAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except ConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.post(
    "/{address_public_id}/default",
    response_model=AddressResponse,
    status_code=status.HTTP_200_OK,
)
async def set_default_address(
    address_public_id: UUID,
    current_user: User = Depends(get_current_user),
    service: AddressService = Depends(get_address_service),
) -> AddressResponse:
    try:
        return await service.set_default_address(
            current_user=current_user,
            address_public_id=address_public_id,
        )

    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except ConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.delete(
    "/{address_public_id}/default",
    response_model=AddressResponse,
    status_code=status.HTTP_200_OK,
)
async def clear_default_address(
    address_public_id: UUID,
    current_user: User = Depends(get_current_user),
    service: AddressService = Depends(get_address_service),
) -> AddressResponse:
    try:
        return await service.clear_default_address(
            current_user=current_user,
            address_public_id=address_public_id,
        )

    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except ConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.post(
    "/{address_public_id}/deactivate",
    response_model=AddressResponse,
    status_code=status.HTTP_200_OK,
)
async def deactivate_address(
    address_public_id: UUID,
    current_user: User = Depends(get_current_user),
    service: AddressService = Depends(get_address_service),
) -> AddressResponse:
    try:
        return await service.deactivate_address(
            current_user=current_user,
            address_public_id=address_public_id,
        )

    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except ConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.post(
    "/{address_public_id}/activate",
    response_model=AddressResponse,
    status_code=status.HTTP_200_OK,
)
async def activate_address(
    address_public_id: UUID,
    current_user: User = Depends(get_current_user),
    service: AddressService = Depends(get_address_service),
) -> AddressResponse:
    try:
        return await service.activate_address(
            current_user=current_user,
            address_public_id=address_public_id,
        )

    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except ConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.delete(
    "/{address_public_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_my_address(
    address_public_id: UUID,
    current_user: User = Depends(get_current_user),
    service: AddressService = Depends(get_address_service),
) -> None:
    try:
        await service.delete_address(
            current_user=current_user,
            address_public_id=address_public_id,
        )

    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except ConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc