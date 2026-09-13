from fastapi import APIRouter
from app.core.responses import ok
router=APIRouter()
@router.get("")
async def prices(): return ok([{ "crop":"Tomato","market":"Pune","price":24,"unit":"kg","date":"2026-09-13","source":"demo-market-data"}])
@router.get("/current")
async def current(): return ok([{ "crop":"Tomato","market":"Pune","price":24,"unit":"kg"},{"crop":"Onion","market":"Nashik","price":30,"unit":"kg"}])
@router.get("/history")
async def history(): return ok([{ "date":"2026-09-11","price":22},{"date":"2026-09-12","price":23},{"date":"2026-09-13","price":24}])
@router.get("/{crop_type_id}")
async def crop_price(crop_type_id:int): return ok({"crop_type_id":crop_type_id,"current_price":24,"unit":"kg"})
