from fastapi import APIRouter
from app.core.responses import ok
router=APIRouter()
@router.get("")
async def reviews(): return ok([{ "id":1,"order_id":9001,"reviewer_id":2001,"reviewee_id":101,"rating":5,"comment":"Fresh produce and reliable delivery"}])
@router.post("")
async def create_review(): return ok({"id":2,"rating":5,"created":True})
@router.get("/{review_id}")
async def review(review_id:int): return ok({"id":review_id,"rating":5,"comment":"Good transaction"})
@router.patch("/{review_id}")
async def update(review_id:int): return ok({"id":review_id,"updated":True})
@router.delete("/{review_id}")
async def delete(review_id:int): return ok({"id":review_id,"deleted":True})
