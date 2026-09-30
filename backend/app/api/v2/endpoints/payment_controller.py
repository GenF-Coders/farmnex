from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.current_user import get_current_user
from app.core.database import get_db
from app.models.payment import Payment
from app.models.user import User
from app.repositories.payment_repository import PaymentRepository
from app.repositories.wallet_repository import WalletRepository
from app.schemas.payment_schema import PaymentResponse
from app.schemas.wallet_schema import WalletResponse
from app.services.payment_service import PaymentService
from app.services.wallet_service import WalletService

# No POST/PATCH/DELETE on payments themselves: they are created and updated only by the server -
# Pay (demo) and bid accept (F12 / S20).
router = APIRouter(prefix="/payments", tags=["Payment"])

def _service(db: AsyncSession) -> PaymentService:
    return PaymentService(PaymentRepository(db))

def _wallet(db: AsyncSession) -> WalletService:
    return WalletService(WalletRepository(db))

def _to_response(entity: Payment, order_public_id: UUID) -> PaymentResponse:
    # entity.order_id is the internal int; the response uses the order's public id instead.
    fields = {name: getattr(entity, name) for name in PaymentResponse.model_fields if name != "order_id"}
    return PaymentResponse(**fields, order_id=order_public_id)

@router.get("", response_model=list[PaymentResponse])
async def list_all(offset: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[PaymentResponse]:
    rows = await _service(db).list(current_user=current_user, offset=offset, limit=limit)
    return [_to_response(payment, order_public_id) for payment, order_public_id in rows]

@router.get("/wallet", response_model=WalletResponse)
async def my_wallet(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> WalletResponse:
    """My demo wallet: money held from me, money held for my sales, received and refunded."""
    return WalletResponse(**await _wallet(db).summary(current_user))

@router.post("/orders/{order_id}/pay-demo", response_model=PaymentResponse)
async def pay_demo(
    order_id: UUID,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key", max_length=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PaymentResponse:
    """Pay (demo) - no real money moves. The order's buyer pays what is still due; the server works
    out the amount and holds it until delivery. Paying again returns the same payment."""
    return _to_response(*await _wallet(db).pay_demo(order_id, current_user, request_key=idempotency_key))

@router.get("/{public_id}", response_model=PaymentResponse)
async def get_one(public_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> PaymentResponse:
    return _to_response(*await _service(db).get(public_id, current_user))
