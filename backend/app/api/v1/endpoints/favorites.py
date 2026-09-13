from fastapi import APIRouter
from app.core.responses import ok
router=APIRouter()
@router.get("")
async def favorites(): return ok([{ "id":1,"crop_id":1,"crop_name":"Tomato","saved_at":"2026-09-13T10:00:00Z"}])
@router.post("")
async def add(): return ok({"id":2,"crop_id":2,"saved":True})
@router.delete("/{favorite_id}")
async def remove(favorite_id:int): return ok({"id":favorite_id,"removed":True})
