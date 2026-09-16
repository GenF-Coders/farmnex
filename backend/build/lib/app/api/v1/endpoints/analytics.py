from fastapi import APIRouter
from app.core.responses import ok
router=APIRouter()
@router.get("/farmer")
async def farmer(): return ok({"revenue":325000,"orders_completed":28,"average_crop_price":26.4,"waste_recovered_kg":820})
@router.get("/buyer")
async def buyer(): return ok({"spend":1250000,"orders_completed":74,"average_saving_percent":8.6})
@router.get("/fpo")
async def fpo(): return ok({"member_count":128,"sales_value":9200000,"quantity_sold_kg":38500})
