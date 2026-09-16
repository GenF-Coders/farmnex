from fastapi import APIRouter
from app.core.responses import ok
router = APIRouter()
@router.get("")
async def farms(): return ok([{ "id": 501, "farmer_id": 101, "name": "Main Farm", "area_acres": 4.5, "location": {"lat":18.52,"lng":73.86}, "soil_type":"loamy" }])
@router.post("")
async def create_farm(): return ok({"id": 502, "created": True}, "Farm created")
@router.get("/{farm_id}")
async def farm(farm_id: int): return ok({"id": farm_id, "farmer_id": 101, "area_acres": 4.5, "soil_type":"loamy"})
@router.patch("/{farm_id}")
async def update_farm(farm_id: int): return ok({"id": farm_id, "updated": True})
@router.delete("/{farm_id}")
async def delete_farm(farm_id: int): return ok({"id": farm_id, "deleted": True})
