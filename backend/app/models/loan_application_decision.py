from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from typing import TYPE_CHECKING
from datetime import datetime
from enum import Enum
import uuid
from ..db import Base

if TYPE_CHECKING:
    from .loan_application import LoanApplication
    from .user import User


class DecisionType(str, Enum):
    """Types of decisions that can be made on an application"""
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    NEEDS_MORE_INFO = "NEEDS_MORE_INFO"


class LoanApplicationDecision(Base):
    __tablename__ = "loan_application_decisions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # Foreign keys
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("loan_applications.id"), index=True
    )
    officer_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Decision details
    decision: Mapped[DecisionType] = mapped_column(
        SQLEnum(DecisionType, name="loan_decision_type"), index=True
    )
    notes: Mapped[str] = mapped_column(String(2000))

    # Timestamp
    decided_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )

    # Relationships
    application: Mapped["LoanApplication"] = relationship(
        "LoanApplication", back_populates="decisions"
    )
    officer: Mapped["User"] = relationship("User", foreign_keys=[officer_user_id])
