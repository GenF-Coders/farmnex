from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.listing_media import ListingMedia, ListingVerification
from app.models.product_listing import ProductListing


class ListingMediaRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # --- listings -------------------------------------------------------------------

    async def get_listing_owned_by_user(self, listing_public_id: UUID, user_id: int) -> ProductListing | None:
        """The seller's own listing, locked until the request ends, so two uploads at once can't beat the limits."""
        result = await self.db.execute(
            select(ProductListing)
            .where(ProductListing.public_id == listing_public_id, ProductListing.seller_id == user_id)
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def get_listing_visible_to(self, listing_public_id: UUID, user_id: int) -> ProductListing | None:
        """Same rule as the listing: ACTIVE listings are public to a logged-in user; a seller sees all their own."""
        result = await self.db.execute(
            select(ProductListing).where(
                ProductListing.public_id == listing_public_id,
                or_(ProductListing.status == "ACTIVE", ProductListing.seller_id == user_id),
            )
        )
        return result.scalar_one_or_none()

    async def get_listing(self, listing_public_id: UUID, *, lock: bool = False) -> ProductListing | None:
        query = select(ProductListing).where(ProductListing.public_id == listing_public_id)
        result = await self.db.execute(query.with_for_update() if lock else query)
        return result.scalar_one_or_none()

    # --- media ----------------------------------------------------------------------

    async def list_media(self, listing_id: int) -> list[ListingMedia]:
        result = await self.db.execute(
            select(ListingMedia).where(ListingMedia.listing_id == listing_id).order_by(ListingMedia.id)
        )
        return list(result.scalars().all())

    async def count_media(self, listing_id: int, kind: str) -> int:
        result = await self.db.execute(
            select(func.count(ListingMedia.id)).where(ListingMedia.listing_id == listing_id, ListingMedia.kind == kind)
        )
        return int(result.scalar_one())

    async def get_media(self, listing_id: int, media_public_id: UUID) -> ListingMedia | None:
        result = await self.db.execute(
            select(ListingMedia).where(ListingMedia.listing_id == listing_id, ListingMedia.public_id == media_public_id)
        )
        return result.scalar_one_or_none()

    async def add_media(self, **values) -> ListingMedia:
        entity = ListingMedia(**values)
        self.db.add(entity)
        await self.db.flush()
        await self.db.refresh(entity)
        return entity

    async def delete_media(self, entity: ListingMedia) -> None:
        await self.db.delete(entity)
        await self.db.flush()

    async def media_counts(self, listing_ids: list[int]) -> dict[int, int]:
        if not listing_ids:
            return {}
        result = await self.db.execute(
            select(ListingMedia.listing_id, func.count(ListingMedia.id))
            .where(ListingMedia.listing_id.in_(listing_ids))
            .group_by(ListingMedia.listing_id)
        )
        return {listing_id: int(count) for listing_id, count in result.all()}

    # --- verification ---------------------------------------------------------------

    async def get_verification(self, listing_id: int) -> ListingVerification | None:
        result = await self.db.execute(
            select(ListingVerification).where(ListingVerification.listing_id == listing_id)
        )
        return result.scalar_one_or_none()

    async def statuses(self, listing_ids: list[int]) -> dict[int, str]:
        if not listing_ids:
            return {}
        result = await self.db.execute(
            select(ListingVerification.listing_id, ListingVerification.status).where(
                ListingVerification.listing_id.in_(listing_ids)
            )
        )
        return {listing_id: status for listing_id, status in result.all()}

    async def set_verification(
        self,
        listing_id: int,
        *,
        status: str,
        reason: str | None = None,
        reviewed_by_id: int | None = None,
        reviewed_at: datetime | None = None,
    ) -> ListingVerification:
        entity = await self.get_verification(listing_id)
        if entity is None:
            entity = ListingVerification(listing_id=listing_id)
            self.db.add(entity)
        entity.status = status
        entity.reason = reason
        entity.reviewed_by_id = reviewed_by_id
        entity.reviewed_at = reviewed_at
        await self.db.flush()
        await self.db.refresh(entity)
        return entity

    async def clear_verification(self, listing_id: int) -> None:
        entity = await self.get_verification(listing_id)
        if entity is not None:
            await self.db.delete(entity)
            await self.db.flush()

    async def list_by_status(self, status: str, *, offset: int, limit: int) -> list[tuple[ListingVerification, ProductListing]]:
        result = await self.db.execute(
            select(ListingVerification, ProductListing)
            .join(ProductListing, ProductListing.id == ListingVerification.listing_id)
            .where(ListingVerification.status == status)
            .order_by(ListingVerification.updated_at, ListingVerification.id)
            .offset(offset)
            .limit(limit)
        )
        return [(verification, listing) for verification, listing in result.all()]
