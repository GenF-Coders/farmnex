from fastapi import APIRouter, status
from pydantic import BaseModel, EmailStr
from app.core.responses import ok

router = APIRouter()

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "FARMER"
    phone: str | None = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest):
    return ok({"user_id": 1001, "name": payload.name, "email": payload.email, "role": payload.role, "verification_required": True}, "Registration successful")

@router.post("/login")
async def login(payload: LoginRequest):
    return ok({"access_token": "demo-access-token", "refresh_token": "demo-refresh-token", "token_type": "bearer", "expires_in": 3600, "user": {"id": 1001, "name": "Demo Farmer", "role": "FARMER"}}, "Login successful")

@router.post("/logout")
async def logout(): return ok(None, "Logged out successfully")

@router.post("/refresh")
async def refresh(): return ok({"access_token": "demo-access-token-refreshed", "token_type": "bearer", "expires_in": 3600})

@router.post("/forgot-password")
async def forgot_password(): return ok({"request_id": "PWD-10001"}, "Password reset request created")

@router.post("/reset-password")
async def reset_password(): return ok(None, "Password reset successfully")

@router.post("/verify-email")
async def verify_email(): return ok({"verified": True})

@router.post("/verify-phone")
async def verify_phone(): return ok({"verified": True})

@router.post("/resend-verification")
async def resend_verification(): return ok({"sent": True})

@router.get("/me")
async def me(): return ok({"id": 1001, "name": "Demo Farmer", "email": "farmer@farmnex.demo", "role": "FARMER", "verified": True})

@router.patch("/me")
async def update_me(): return ok({"id": 1001, "updated": True})

@router.delete("/me")
async def delete_me(): return ok(None, "Account deletion request accepted")

@router.get("/sessions")
async def sessions(): return ok([{ "id": "sess-1", "device": "Android", "current": True }])

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str): return ok({"session_id": session_id, "revoked": True})

@router.delete("/sessions/all")
async def delete_all_sessions(): return ok({"revoked": 3})
