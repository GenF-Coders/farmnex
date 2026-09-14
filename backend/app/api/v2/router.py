from fastapi import APIRouter
from app.api.v2.endpoints import role_controller, user_controller

router = APIRouter()

modules = [
    role_controller,
    user_controller,
]

for module in modules:
    router.include_router(module.router)
