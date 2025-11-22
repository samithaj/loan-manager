from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from typing import TYPE_CHECKING, Optional
import uuid
from ..db import Base

if TYPE_CHECKING:
    from .loan_application import LoanApplication


class LoanApplicationVehicle(Base):
    __tablename__ = "loan_application_vehicles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # Foreign key
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("loan_applications.id"), unique=True, index=True
    )

    # Vehicle details
    chassis_no: Mapped[str] = mapped_column(String(50), index=True)
    engine_no: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    make: Mapped[str] = mapped_column(String(100))
    model: Mapped[str] = mapped_column(String(100))
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    registration_no: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)

    # Relationship
    application: Mapped["LoanApplication"] = relationship(
        "LoanApplication", back_populates="vehicle"
    )
