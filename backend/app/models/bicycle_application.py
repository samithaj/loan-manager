from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Numeric, Text, Index, CheckConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from datetime import datetime
from enum import Enum
from typing import Optional, Any
import uuid
from ..db import Base


class ApplicationStatus(str, Enum):
    """Application status enumeration"""
    PENDING = "PENDING"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CONVERTED_TO_LOAN = "CONVERTED_TO_LOAN"


class BicycleApplication(Base):
    __tablename__ = "bicycle_applications"

    # Primary identification
    id: Mapped[str] = mapped_column(String, primary_key=True)

    # Customer information
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    nip_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Address information
    address_line1: Mapped[str] = mapped_column(String, nullable=False)
    address_line2: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    city: Mapped[str] = mapped_column(String, nullable=False)

    # Employment information
    employer_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    monthly_income: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)

    # Application details
    bicycle_id: Mapped[str] = mapped_column(String, ForeignKey("bicycles.id"), nullable=False)
    branch_id: Mapped[str] = mapped_column(String, ForeignKey("offices.id"), nullable=False)
    tenure_months: Mapped[int] = mapped_column(Integer, nullable=False)
    down_payment: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0, server_default="0")

    # Status tracking
    status: Mapped[str] = mapped_column(String, nullable=False, default="PENDING")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    loan_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("loans.id"), nullable=True)

    # Audit fields
    submitted_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, server_default="NOW()")
    reviewed_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    # bicycle = relationship("Bicycle", back_populates="applications")
    # branch = relationship("Office", foreign_keys=[branch_id])
    # loan = relationship("Loan", foreign_keys=[loan_id])
    # reviewer = relationship("User", foreign_keys=[reviewed_by])

    __table_args__ = (
        CheckConstraint("status IN ('PENDING', 'UNDER_REVIEW', 'APPROVED', 'REJECTED', 'CONVERTED_TO_LOAN')", name="check_application_status"),
        CheckConstraint("tenure_months IN (12, 24, 36, 48)", name="check_tenure_months"),
        Index("idx_bicycle_applications_status", "status"),
        Index("idx_bicycle_applications_branch", "branch_id"),
        Index("idx_bicycle_applications_submitted_at", "submitted_at"),
        Index("idx_bicycle_applications_bicycle", "bicycle_id"),
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert application to dictionary with all fields"""
        return {
            "id": self.id,
            "full_name": self.full_name,
            "phone": self.phone,
            "email": self.email,
            "nip_number": self.nip_number,
            "address_line1": self.address_line1,
            "address_line2": self.address_line2,
            "city": self.city,
            "employer_name": self.employer_name,
            "monthly_income": float(self.monthly_income) if self.monthly_income else None,
            "bicycle_id": self.bicycle_id,
            "branch_id": self.branch_id,
            "tenure_months": self.tenure_months,
            "down_payment": float(self.down_payment) if self.down_payment else 0,
            "status": self.status,
            "notes": self.notes,
            "loan_id": self.loan_id,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "reviewed_by": str(self.reviewed_by) if self.reviewed_by else None,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
        }

    def can_approve(self) -> bool:
        """
        Check if the application can be approved

        Returns:
            True if application can be approved, False otherwise
        """
        return self.status in [ApplicationStatus.PENDING.value, ApplicationStatus.UNDER_REVIEW.value]

    def can_reject(self) -> bool:
        """
        Check if the application can be rejected

        Returns:
            True if application can be rejected, False otherwise
        """
        return self.status in [ApplicationStatus.PENDING.value, ApplicationStatus.UNDER_REVIEW.value]

    def can_convert_to_loan(self) -> bool:
        """
        Check if the application can be converted to a loan

        Returns:
            True if application can be converted, False otherwise
        """
        return self.status == ApplicationStatus.APPROVED.value
