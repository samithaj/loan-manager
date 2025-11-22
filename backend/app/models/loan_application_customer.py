from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, text, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from typing import TYPE_CHECKING, Optional
from datetime import date
import uuid
from ..db import Base

if TYPE_CHECKING:
    from .loan_application import LoanApplication


class LoanApplicationCustomer(Base):
    __tablename__ = "loan_application_customers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # Foreign key
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("loan_applications.id"), unique=True, index=True
    )

    # Customer details
    nic: Mapped[str] = mapped_column(String(20), index=True)
    full_name: Mapped[str] = mapped_column(String(200))
    dob: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    address: Mapped[str] = mapped_column(String(500))
    phone: Mapped[str] = mapped_column(String(20))
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationship
    application: Mapped["LoanApplication"] = relationship(
        "LoanApplication", back_populates="customer"
    )
