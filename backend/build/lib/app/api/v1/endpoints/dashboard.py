from fastapi import APIRouter
from app.core.responses import ok
router=APIRouter()
@router.get("/farmer")
async def farmer(): return ok({"active_listings":12,"active_bids":5,"pending_orders":3,"estimated_revenue":125000,"rescue_crops":2,"waste_listings":4})
@router.get("/buyer")
async def buyer(): return ok({"active_bids":8,"orders_in_progress":4,"monthly_spend":385000,"saved_crops":14})
@router.get("/customer")
async def customer(): return ok({"orders":6,"active_orders":1,"saved_items":9,"total_spend":12400})
@router.get("/fpo")
async def fpo(): return ok({"members":128,"active_crops":43,"total_quantity_kg":38500,"active_bids":17,"estimated_revenue":920000})
