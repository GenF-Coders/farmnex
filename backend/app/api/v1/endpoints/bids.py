from fastapi import APIRouter, status
from pydantic import BaseModel
from app.core.responses import ok
router=APIRouter()
class BidCreate(BaseModel): crop_id:int; bid_price:float; quantity:float; valid_until:str|None=None; note:str|None=None
@router.get("")
async def bids(): return ok([{ "id":7001,"crop_id":1,"buyer_id":201,"bid_price":28,"quantity":500,"status":"active","created_at":"2026-09-13T09:00:00Z"}],count=1)
@router.post("",status_code=status.HTTP_201_CREATED)
async def create_bid(payload:BidCreate): return ok({"id":7002,"buyer_id":201,**payload.model_dump(),"status":"active"},"Bid submitted")
@router.get("/{bid_id}")
async def get_bid(bid_id:int): return ok({"id":bid_id,"crop_id":1,"buyer_id":201,"bid_price":28,"quantity":500,"status":"active"})
@router.patch("/{bid_id}")
async def update_bid(bid_id:int): return ok({"id":bid_id,"updated":True})
@router.delete("/{bid_id}")
async def delete_bid(bid_id:int): return ok({"id":bid_id,"deleted":True})
@router.post("/{bid_id}/accept")
async def accept(bid_id:int): return ok({"id":bid_id,"status":"accepted","order_id":9001})
@router.post("/{bid_id}/reject")
async def reject(bid_id:int): return ok({"id":bid_id,"status":"rejected"})
@router.post("/{bid_id}/withdraw")
async def withdraw(bid_id:int): return ok({"id":bid_id,"status":"withdrawn"})
