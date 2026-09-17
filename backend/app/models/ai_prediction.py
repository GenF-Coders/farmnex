from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Integer, Numeric, String, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base



class AIPrediction(Base):

    __tablename__ = "ai_predictions"



    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    public_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), unique=True, nullable=False, index=True, default=uuid4)

    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)

    farm_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("farms.id", ondelete="CASCADE"), nullable=True, index=True)

    farm_crop_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("farm_crops.id", ondelete="CASCADE"), nullable=True, index=True)

    model_name: Mapped[str] = mapped_column(String(150), nullable=False)

    model_version: Mapped[str | None] = mapped_column(String(80), nullable=True)

    prediction_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)

    prediction: Mapped[dict] = mapped_column(JSONB, nullable=False)

    confidence: Mapped[Decimal | None] = mapped_column(Numeric(6,5), nullable=True)

    predicted_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    farm: Mapped["Farm"] = relationship("Farm", foreign_keys=[AIPrediction.farm_id])

    farm_crop: Mapped["FarmCrop"] = relationship("FarmCrop", foreign_keys=[AIPrediction.farm_crop_id])
