from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from typing import TYPE_CHECKING
import uuid
from ..db import Base

if TYPE_CHECKING:
    from .loan_application import LoanApplication


class Branch(Base):
    __tablename__ = "branches"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    region: Mapped[str] = mapped_column(String(100), nullable=True)
    address: Mapped[str] = mapped_column(String(500), nullable=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    email: Mapped[str] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    loan_applications: Mapped[list["LoanApplication"]] = relationship(
        "LoanApplication", back_populates="branch"
    )
