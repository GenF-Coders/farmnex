from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.current_user import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.repositories.product_image_repository import ProductImageRepository
from app.schemas.product_image_schema import ProductImageCreate, ProductImageUpdate, ProductImageResponse
from app.services.product_image_service import ProductImageService

router = APIRouter(prefix="/product-images", tags=["ProductImage"])

def _service(db: AsyncSession) -> ProductImageService:
    return ProductImageService(ProductImageRepository(db))

@router.post("", response_model=ProductImageResponse, status_code=status.HTTP_201_CREATED)
async def create(payload: ProductImageCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> ProductImageResponse:
    # Ownership/authorization rules beyond the direct actor field belong in the domain service.
    entity = await _service(db).create(payload.model_dump(exclude_unset=True))
    return ProductImageResponse.model_validate(entity)

@router.get("", response_model=list[ProductImageResponse])
async def list_all(offset: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[ProductImageResponse]:
    entities, _ = await _service(db).list(offset, limit)
    return [ProductImageResponse.model_validate(x) for x in entities]

@router.get("/{public_id}", response_model=ProductImageResponse)
async def get_one(public_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> ProductImageResponse:
    entity = await _service(db).get(public_id)
    return ProductImageResponse.model_validate(entity)

@router.patch("/{public_id}", response_model=ProductImageResponse)
async def update(public_id: UUID, payload: ProductImageUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> ProductImageResponse:
    entity = await _service(db).update(public_id, payload.model_dump(exclude_unset=True))
    return ProductImageResponse.model_validate(entity)

@router.delete("/{public_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(public_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> None:
    await _service(db).delete(public_id)
