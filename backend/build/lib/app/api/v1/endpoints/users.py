from fastapi import APIRouter
from app.core.responses import ok
router = APIRouter()
@router.get("")
async def list_users(): return ok([{ "id": 1001, "name": "Demo Farmer", "role": "FARMER" }, {"id": 2001, "name": "Demo Buyer", "role": "BUYER"}], count=2)
@router.get("/{user_id}")
async def get_user(user_id: int): return ok({"id": user_id, "name": "Demo User", "role": "FARMER", "verified": True})
@router.patch("/{user_id}")
async def update_user(user_id: int): return ok({"id": user_id, "updated": True})
@router.post("/{user_id}/avatar")
async def avatar(user_id: int): return ok({"user_id": user_id, "url": "https://cdn.example.com/farmnex/avatar/demo.jpg"})
@router.delete("/{user_id}/avatar")
async def delete_avatar(user_id: int): return ok({"user_id": user_id, "deleted": True})
