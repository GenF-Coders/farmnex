from fastapi import APIRouter
from app.core.responses import ok
router=APIRouter()
@router.get("")
async def search(): return ok({"query":"tomato","results":[{"type":"crop","id":1,"title":"Tomato","location":"Pune"},{"type":"buyer","id":201,"title":"FreshMart Foods","location":"Pune"}]})
@router.get("/recommendations")
async def recommendations(): return ok([{ "type":"crop","id":1,"reason":"High demand in your market","score":0.92 }])
@router.get("/recommendations/crops")
async def crop_recommendations(): return ok([{ "crop":"Tomato","score":0.92},{"crop":"Onion","score":0.86}])
@router.get("/recommendations/buyers")
async def buyer_recommendations(): return ok([{ "buyer_id":201,"business_name":"FreshMart Foods","score":0.94 }])
