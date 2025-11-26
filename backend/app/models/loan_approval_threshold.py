"""Loan Approval Threshold model for multi-level approval system"""
from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, text, Boolean, Integer, Numeric, DateTime
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional
from datetime import datetime
from decimal import Decimal
import uuid
from ..db import Base


class LoanApprovalThreshold(Base):
    """
    Defines loan amount thresholds and required approval levels.

    Example Configuration:
    - Level 0 (0-∞): Loan Manager initial review
    - Level 1 (100K-500K): Credit Officer L1
    - Level 2 (500K-1M): Credit Officer L2
    - Level 3 (1M+): Senior Management
    """
    __tablename__ = "loan_approval_thresholds"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # Company scoping
    company_id: Mapped[str] = mapped_column(String, index=True, nullable=False)

    # Threshold range
    min_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    max_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)  # NULL = unlimited

    # Approval level configuration
    approval_level: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    approver_role: Mapped[str] = mapped_column(String, nullable=False)
    approver_permission: Mapped[str] = mapped_column(String, nullable=False)

    # Sequential enforcement
    requires_previous_levels: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    # Metadata
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=datetime.utcnow
    )
    created_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "company_id": self.company_id,
            "min_amount": float(self.min_amount) if self.min_amount else 0,
            "max_amount": float(self.max_amount) if self.max_amount else None,
            "approval_level": self.approval_level,
            "approver_role": self.approver_role,
            "approver_permission": self.approver_permission,
            "requires_previous_levels": self.requires_previous_levels,
            "description": self.description,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
        }

    def covers_amount(self, amount: Decimal) -> bool:
        """Check if this threshold covers the given loan amount"""
        if amount < self.min_amount:
            return False
        if self.max_amount is not None and amount >= self.max_amount:
            return False
        return True

    def __repr__(self) -> str:
        max_amt = f"{self.max_amount}" if self.max_amount else "∞"
        return (
            f"<LoanApprovalThreshold(level={self.approval_level}, "
            f"range={self.min_amount}-{max_amt}, role={self.approver_role})>"
        )
