from fastapi import APIRouter
from app.core.responses import ok
router = APIRouter()
@router.get("/states")
async def states(): return ok([{ "code": "MH", "name": "Maharashtra" }])
@router.get("/districts")
async def districts(): return ok([{ "code": "PUN", "name": "Pune", "state_code": "MH" }, {"code":"NAS","name":"Nashik","state_code":"MH"}])
@router.get("/talukas")
async def talukas(): return ok([{ "name": "Baramati", "district": "Pune" }])
@router.get("/villages")
async def villages(): return ok([{ "name": "Demo Village", "taluka": "Baramati" }])
@router.get("/search")
async def search(): return ok([{ "label": "Pune, Maharashtra", "lat": 18.5204, "lng": 73.8567 }])
