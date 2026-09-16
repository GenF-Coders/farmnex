from fastapi import APIRouter
from app.api.v2.endpoints import auth_controller, role_controller, user_controller, storage_controller, address_controller, farm_controller,  otp_controller

router = APIRouter()

modules = [
    auth_controller,
    user_controller,
    #role_controller,
    address_controller,
    farm_controller,
    #storage_controller,
    #otp_controller,

]

for module in modules:
    router.include_router(module.router)
