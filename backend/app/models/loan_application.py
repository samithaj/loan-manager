from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, text, Integer, Numeric, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from typing import TYPE_CHECKING, Optional
from datetime import datetime
from enum import Enum
import uuid
from ..db import Base

if TYPE_CHECKING:
    from .branch import Branch
    from .user import User
    from .loan_application_customer import LoanApplicationCustomer
    from .loan_application_vehicle import LoanApplicationVehicle
    from .loan_application_document import LoanApplicationDocument
    from .loan_application_decision import LoanApplicationDecision
    from .loan_application_audit import LoanApplicationAudit


class ApplicationStatus(str, Enum):
    """Loan application status state machine"""
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    NEEDS_MORE_INFO = "NEEDS_MORE_INFO"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class LoanApplication(Base):
    __tablename__ = "loan_applications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # Human-readable application number (e.g., "LA-2025-0001")
    application_no: Mapped[str] = mapped_column(String(50), unique=True, index=True)

    # Foreign keys
    lmo_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    branch_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("branches.id"))

    # Loan details
    requested_amount: Mapped[int] = mapped_column(Numeric(12, 2))
    tenure_months: Mapped[int] = mapped_column(Integer)

    # Status tracking
    status: Mapped[ApplicationStatus] = mapped_column(
        SQLEnum(ApplicationStatus, name="application_status"),
        default=ApplicationStatus.DRAFT,
        index=True
    )

    # LMO notes
    lmo_notes: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=datetime.utcnow
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    lmo: Mapped["User"] = relationship("User", foreign_keys=[lmo_user_id])
    branch: Mapped["Branch"] = relationship("Branch", back_populates="loan_applications")
    customer: Mapped[Optional["LoanApplicationCustomer"]] = relationship(
        "LoanApplicationCustomer", back_populates="application", uselist=False, cascade="all, delete-orphan"
    )
    vehicle: Mapped[Optional["LoanApplicationVehicle"]] = relationship(
        "LoanApplicationVehicle", back_populates="application", uselist=False, cascade="all, delete-orphan"
    )
    documents: Mapped[list["LoanApplicationDocument"]] = relationship(
        "LoanApplicationDocument", back_populates="application", cascade="all, delete-orphan"
    )
    decisions: Mapped[list["LoanApplicationDecision"]] = relationship(
        "LoanApplicationDecision", back_populates="application", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["LoanApplicationAudit"]] = relationship(
        "LoanApplicationAudit", back_populates="application", cascade="all, delete-orphan"
    )
