from fastapi import APIRouter, Request
from app.core.responses import ok
router=APIRouter()
@router.post("/payment")
async def payment(request: Request): return ok({"received":True,"event":"payment.updated"})
@router.post("/notification")
async def notification(request: Request): return ok({"received":True,"event":"notification.updated"})
