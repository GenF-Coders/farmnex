from fastapi import APIRouter
from app.api.v2.endpoints import role_controller, user_controller

router = APIRouter()

modules = [
    (role_controller, "role"),
    (user_controller, "user"),
]

for module, tag in modules:
    router.include_router(module.router, tags=[tag])
