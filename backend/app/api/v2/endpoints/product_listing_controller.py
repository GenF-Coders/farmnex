from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.current_user import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.repositories.product_listing_repository import ProductListingRepository
from app.schemas.product_listing_schema import ProductListingCreate, ProductListingUpdate, ProductListingResponse
from app.services.product_listing_service import ProductListingService

router = APIRouter(prefix="/product-listings", tags=["ProductListing"])

def _service(db: AsyncSession) -> ProductListingService:
    return ProductListingService(ProductListingRepository(db))

@router.post("", response_model=ProductListingResponse, status_code=status.HTTP_201_CREATED)
async def create(payload: ProductListingCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> ProductListingResponse:
    # Ownership/authorization rules beyond the direct actor field belong in the domain service.
    entity = await _service(db).create(payload.model_dump(exclude_unset=True))
    return ProductListingResponse.model_validate(entity)

@router.get("", response_model=list[ProductListingResponse])
async def list_all(offset: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[ProductListingResponse]:
    entities, _ = await _service(db).list(offset, limit)
    return [ProductListingResponse.model_validate(x) for x in entities]

@router.get("/{public_id}", response_model=ProductListingResponse)
async def get_one(public_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> ProductListingResponse:
    entity = await _service(db).get(public_id)
    return ProductListingResponse.model_validate(entity)

@router.patch("/{public_id}", response_model=ProductListingResponse)
async def update(public_id: UUID, payload: ProductListingUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> ProductListingResponse:
    entity = await _service(db).update(public_id, payload.model_dump(exclude_unset=True))
    return ProductListingResponse.model_validate(entity)

@router.delete("/{public_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(public_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> None:
    await _service(db).delete(public_id)
