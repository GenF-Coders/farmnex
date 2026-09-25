from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies.current_user import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.repositories.bid_repository import BidRepository
from app.repositories.crop_batch_repository import CropBatchRepository
from app.repositories.farm_crop_activity_repository import FarmCropActivityRepository
from app.repositories.farm_repository import FarmRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.product_listing_repository import ProductListingRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.repositories.waste_record_repository import WasteRecordRepository
from app.services.bid_service import BidService
from app.services.crop_batch_service import CropBatchService
from app.services.farm_crop_activity_service import FarmCropActivityService
from app.services.farm_service import FarmService
from app.services.me_service import MeService
from app.services.notification_service import NotificationService
from app.services.order_service import OrderService
from app.services.product_listing_service import ProductListingService
from app.services.storage_service import StorageService
from app.services.user_service import UserService
from app.services.waste_record_service import WasteRecordService
router = APIRouter(prefix='/me', tags=['My Dashboard'])
def get_me_service(db: AsyncSession = Depends(get_db)) -> MeService:
    return MeService(user_service=UserService(UserRepository(db), RoleRepository(db), StorageService()), farm_service=FarmService(FarmRepository(db)), product_listing_service=ProductListingService(ProductListingRepository(db)), bid_service=BidService(BidRepository(db)), order_service=OrderService(OrderRepository(db)), crop_batch_service=CropBatchService(CropBatchRepository(db)), activity_service=FarmCropActivityService(FarmCropActivityRepository(db)), waste_record_service=WasteRecordService(WasteRecordRepository(db)), notification_service=NotificationService(NotificationRepository(db)))
@router.get('/dashboard')
async def get_my_dashboard(limit: int = Query(20, ge=1, le=50), current_user: User = Depends(get_current_user), service: MeService = Depends(get_me_service)) -> dict:
    return await service.get_dashboard(current_user=current_user, limit=limit)
