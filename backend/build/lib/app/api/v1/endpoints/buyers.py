from fastapi import APIRouter
from app.core.responses import ok
router = APIRouter()
@router.get("")
async def buyers(): return ok([{ "id": 201, "business_name": "FreshMart Foods", "location": "Pune", "verified": True, "rating": 4.6 }], count=1)
@router.get("/{buyer_id}")
async def buyer(buyer_id: int): return ok({"id": buyer_id, "business_name": "FreshMart Foods", "verified": True, "rating": 4.6})
@router.patch("/{buyer_id}")
async def update_buyer(buyer_id: int): return ok({"id": buyer_id, "updated": True})
@router.get("/{buyer_id}/reviews")
async def buyer_reviews(buyer_id: int): return ok([{ "id": 1, "rating": 5, "comment": "Reliable buyer" }])
