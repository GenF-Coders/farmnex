from fastapi import APIRouter, status
from pydantic import BaseModel
from app.core.responses import ok
router = APIRouter()

CROPS = [
    {"id":1,"farmer_id":101,"crop_name":"Tomato","variety":"Hybrid","quantity":500,"unit":"kg","expected_price":25,"location":"Pune","harvest_date":"2026-10-15","quality":"A","organic":False,"status":"available"},
    {"id":2,"farmer_id":102,"crop_name":"Onion","variety":"N-53","quantity":1000,"unit":"kg","expected_price":30,"location":"Nashik","harvest_date":"2026-10-20","quality":"A","organic":True,"status":"available"},
]
class CropCreate(BaseModel):
    crop_name: str
    quantity: float
    unit: str = "kg"
    expected_price: float
    location: str
    harvest_date: str | None = None
    quality: str = "A"
    organic: bool = False

@router.get("")
async def list_crops(): return ok(CROPS, count=len(CROPS), page=1, page_size=20)
@router.post("", status_code=status.HTTP_201_CREATED)
async def create_crop(payload: CropCreate):
    item={"id":3,"farmer_id":101,**payload.model_dump(),"status":"available"}
    return ok(item,"Crop listing created")
@router.get("/{crop_id}")
async def get_crop(crop_id: int): return ok(next((x for x in CROPS if x["id"]==crop_id), {"id":crop_id,"crop_name":"Tomato","status":"available"}))
@router.patch("/{crop_id}")
async def update_crop(crop_id: int): return ok({"id":crop_id,"updated":True})
@router.delete("/{crop_id}")
async def delete_crop(crop_id: int): return ok({"id":crop_id,"deleted":True})
@router.post("/{crop_id}/publish")
async def publish(crop_id:int): return ok({"id":crop_id,"status":"available"})
@router.post("/{crop_id}/pause")
async def pause(crop_id:int): return ok({"id":crop_id,"status":"paused"})
@router.post("/{crop_id}/sold")
async def sold(crop_id:int): return ok({"id":crop_id,"status":"sold"})
@router.post("/{crop_id}/cancel")
async def cancel(crop_id:int): return ok({"id":crop_id,"status":"cancelled"})
@router.get("/{crop_id}/bids")
async def crop_bids(crop_id:int): return ok([{ "id":7001,"crop_id":crop_id,"buyer_id":201,"bid_price":28,"quantity":500,"status":"active" }])
@router.get("/{crop_id}/bidding-status")
async def bidding_status(crop_id:int): return ok({"crop_id":crop_id,"active":True,"bid_count":3,"highest_bid":31})
@router.post("/{crop_id}/disease-scan")
async def disease_scan(crop_id:int): return ok({"scan_id":"DS-1001","crop_id":crop_id,"status":"completed","disease":"No significant disease detected","confidence":0.91})
