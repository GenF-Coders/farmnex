from fastapi import APIRouter
from app.core.responses import ok
router=APIRouter()
@router.get("/buyers")
async def buyers(): return ok([{ "buyer_id":201,"business_name":"FreshMart Foods","match_score":0.94,"offered_price":28,"distance_km":18,"required_quantity":500,"reliability_score":0.96 }])
@router.post("/buyers")
async def match_buyers(): return ok({"match_id":"M-1001","matches":[{"buyer_id":201,"match_score":0.94},{"buyer_id":202,"match_score":0.88}]})
@router.get("/crops/{crop_id}")
async def crop_matches(crop_id:int): return ok([{ "buyer_id":201,"crop_id":crop_id,"match_score":0.94,"offered_price":28 }])
