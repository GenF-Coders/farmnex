from fastapi import APIRouter
from app.core.responses import ok
router = APIRouter()
@router.get("")
async def farmers(): return ok([{ "id": 101, "name": "Ramesh Patil", "village": "Baramati", "district": "Pune", "verified": True, "rating": 4.7 }], count=1)
@router.get("/{farmer_id}")
async def farmer(farmer_id: int): return ok({"id": farmer_id, "name": "Ramesh Patil", "farm_count": 2, "rating": 4.7, "verified": True})
@router.patch("/{farmer_id}")
async def update_farmer(farmer_id: int): return ok({"id": farmer_id, "updated": True})
@router.get("/{farmer_id}/reviews")
async def farmer_reviews(farmer_id: int): return ok([{ "id": 1, "rating": 5, "comment": "Good quality and timely delivery" }])
