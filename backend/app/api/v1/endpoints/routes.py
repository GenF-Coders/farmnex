from fastapi import APIRouter
from app.core.responses import ok
router=APIRouter()
@router.post("/optimize")
async def optimize(): return ok({"route_id":"R-1001","distance_km":47.8,"duration_minutes":126,"fuel_estimate_liters":6.2,"stops":[{"farm_id":501,"sequence":1},{"farm_id":502,"sequence":2},{"destination":"Pune Market","sequence":3}],"optimization":"mock_or_tools"})
@router.get("/{route_id}")
async def get_route(route_id:str): return ok({"route_id":route_id,"status":"planned","distance_km":47.8,"duration_minutes":126})
@router.post("/{route_id}/start")
async def start(route_id:str): return ok({"route_id":route_id,"status":"in_progress"})
@router.post("/{route_id}/complete")
async def complete(route_id:str): return ok({"route_id":route_id,"status":"completed"})
