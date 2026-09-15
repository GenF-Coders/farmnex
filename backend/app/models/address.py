from __future__ import annotations

from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.core.base import Base


class Address(Base):
    __tablename__ = "addresses"

    __table_args__ = (
        Index(
            "uq_addresses_user_default_active",
            "user_id",
            unique=True,
            postgresql_where=text(
                "is_default = true AND is_active = true"
            ),
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
    )

    public_id = Column(
        PG_UUID(as_uuid=True),
        unique=True,
        nullable=False,
        index=True,
        default=uuid4,
    )

    user_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    address_line_1 = Column(
        String(255),
        nullable=False,
    )

    address_line_2 = Column(
        String(255),
        nullable=True,
    )

    landmark = Column(
        String(255),
        nullable=True,
    )

    village = Column(
        String(150),
        nullable=True,
    )

    city = Column(
        String(150),
        nullable=False,
    )

    district = Column(
        String(150),
        nullable=True,
    )

    state = Column(
        String(150),
        nullable=False,
    )

    postal_code = Column(
        String(20),
        nullable=False,
    )

    country = Column(
        String(100),
        nullable=False,
        default="India",
        server_default="India",
    )

    latitude = Column(
        Numeric(10, 7),
        nullable=True,
    )

    longitude = Column(
        Numeric(10, 7),
        nullable=True,
    )

    is_default = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    user = relationship(
        "User",
        back_populates="addresses",
    )

    farms = relationship(
        "Farm",
        back_populates="address",
    )