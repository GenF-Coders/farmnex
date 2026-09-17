from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Integer, String, Text, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base



class AIRecommendation(Base):

    __tablename__ = "ai_recommendations"



    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    public_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), unique=True, nullable=False, index=True, default=uuid4)

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    farm_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("farms.id", ondelete="CASCADE"), nullable=True, index=True)

    farm_crop_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("farm_crops.id", ondelete="CASCADE"), nullable=True, index=True)

    prediction_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("ai_predictions.id", ondelete="CASCADE"), nullable=True, index=True)

    recommendation_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)

    title: Mapped[str] = mapped_column(String(200), nullable=False)

    description: Mapped[str] = mapped_column(Text, nullable=False)

    priority: Mapped[str] = mapped_column(String(30), nullable=False, index=True, default="ACTIVE", server_default="ACTIVE")

    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True, default="ACTIVE", server_default="ACTIVE")

    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    farm: Mapped["Farm"] = relationship("Farm", foreign_keys=[AIRecommendation.farm_id])

    farm_crop: Mapped["FarmCrop"] = relationship("FarmCrop", foreign_keys=[AIRecommendation.farm_crop_id])

    prediction: Mapped["AIPrediction"] = relationship("AIPrediction", foreign_keys=[AIRecommendation.prediction_id])
