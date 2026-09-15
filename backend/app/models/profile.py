from __future__ import annotations

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from uuid import uuid4

from app.core.base import Base


class Profile(Base):
    __tablename__ = "profiles"

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
        unique=True,
        index=True,
    )

    first_name = Column(
        String(100),
        nullable=False,
    )

    middle_name = Column(
        String(100),
        nullable=True,
    )

    surname = Column(
        String(100),
        nullable=False,
    )

    alternate_phone_number = Column(
        String(20),
        nullable=True,
        unique=True,
    )

    alternate_phone_verified_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    date_of_birth = Column(
        Date,
        nullable=True,
    )

    gender = Column(
        String(30),
        nullable=True,
    )

    profile_image_path = Column(
        String(1024),
        nullable=True,
    )

    preferred_language = Column(
        String(20),
        nullable=True,
    )

    timezone = Column(
        String(50),
        nullable=True,
    )

    occupation = Column(
        String(150),
        nullable=True,
    )

    bio = Column(
        Text,
        nullable=True,
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

    user = relationship(
        "User",
        back_populates="profile",
    )