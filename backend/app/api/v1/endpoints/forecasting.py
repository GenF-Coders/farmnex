from fastapi import APIRouter
from app.core.responses import ok
router=APIRouter()
@router.get("/demand")
async def demand(): return ok([{ "crop":"Tomato","market":"Pune","forecast_week":"2026-W39","expected_quantity_kg":4200,"demand_score":91,"confidence":0.84 }])
@router.post("/demand")
async def demand_predict(): return ok({"forecast_id":"DF-1001","crop":"Tomato","market":"Pune","expected_quantity_kg":4200,"demand_score":91,"confidence":0.84,"model_version":"demand-demo-v1"})
@router.get("/demand/{forecast_id}")
async def demand_by_id(forecast_id:str): return ok({"forecast_id":forecast_id,"status":"completed","expected_quantity_kg":4200,"confidence":0.84})
@router.get("/price")
async def price(): return ok([{ "crop":"Tomato","market":"Pune","current_price":24,"predicted_price":28,"horizon_days":7,"confidence":0.82 }])
@router.post("/price")
async def price_predict(): return ok({"forecast_id":"PF-1001","current_price":24,"predicted_price":28,"confidence":0.82,"model_version":"price-demo-v1"})
