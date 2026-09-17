from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Integer, String, Text, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base

from app.models.user import User



class AuditLog(Base):

    __tablename__ = "audit_logs"



    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    public_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), unique=True, nullable=False, index=True, default=uuid4)

    actor_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)

    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    request_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)

    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    before_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    after_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at_override: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    actor: Mapped["User"] = relationship("User", foreign_keys=[actor_id])
