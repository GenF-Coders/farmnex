from fastapi import APIRouter
from app.core.responses import ok
router=APIRouter()
DATA=[{"id":1,"crop_name":"Tomato","price_per_kg":25,"quantity":500,"location":"Pune","farmer":"Ramesh Patil","rating":4.7},{"id":2,"crop_name":"Onion","price_per_kg":30,"quantity":1000,"location":"Nashik","farmer":"Suresh Jadhav","rating":4.6}]
@router.get("")
async def marketplace(): return ok(DATA,count=len(DATA),page=1,page_size=20)
@router.get("/search")
async def search(): return ok(DATA,count=len(DATA))
@router.get("/categories")
async def categories(): return ok(["Vegetables","Fruits","Grains","Pulses","Spices","Waste"])
@router.get("/trending")
async def trending(): return ok([{"crop":"Tomato","demand_score":92},{"crop":"Onion","demand_score":88}])
@router.get("/nearby")
async def nearby(): return ok(DATA)
