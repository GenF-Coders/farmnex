from fastapi import APIRouter
from app.core.responses import ok
router = APIRouter()
@router.post("/kyc")
async def submit_kyc(): return ok({"kyc_id":"KYC-1001","status":"pending"}, "KYC submitted")
@router.get("/kyc")
async def get_kyc(): return ok({"kyc_id":"KYC-1001","status":"verified","verified_at":"2026-09-13T10:00:00Z"})
@router.patch("/kyc")
async def update_kyc(): return ok({"kyc_id":"KYC-1001","status":"pending_review"})
@router.get("/status")
async def status(): return ok({"identity":"verified","kyc":"verified","phone":"verified","email":"verified"})
