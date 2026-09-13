from fastapi import APIRouter
from app.core.responses import ok
router=APIRouter()
@router.post("/create")
async def create(): return ok({"payment_id":"PAY-1001","order_id":9001,"amount":14000,"currency":"INR","status":"created","provider":"demo"})
@router.get("/detail/{payment_id}")
async def get_payment(payment_id:str): return ok({"payment_id":payment_id,"amount":14000,"currency":"INR","status":"success"})
@router.post("/detail/{payment_id}/verify")
async def verify(payment_id:str): return ok({"payment_id":payment_id,"verified":True,"status":"success"})
@router.post("/detail/{payment_id}/refund")
async def refund(payment_id:str): return ok({"payment_id":payment_id,"refund_id":"REF-1001","status":"initiated"})
@router.get("/history")
async def history(): return ok([{ "payment_id":"PAY-1001","amount":14000,"status":"success","date":"2026-09-13" }])
