from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Text, Numeric
from sqlalchemy.dialects.postgresql import TIMESTAMP, JSONB
from datetime import datetime
from enum import Enum
from typing import Optional, Any, Dict, TYPE_CHECKING
from decimal import Decimal
from ..db import Base

if TYPE_CHECKING:
    from .bicycle import Bicycle
    from .reference import Office


class TransferStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    IN_TRANSIT = "IN_TRANSIT"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class BicycleTransfer(Base):
    __tablename__ = "bicycle_transfers"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    bicycle_id: Mapped[str] = mapped_column(
        String, ForeignKey("bicycles.id", ondelete="CASCADE"), nullable=False
    )
    from_branch_id: Mapped[str] = mapped_column(
        String, ForeignKey("offices.id"), nullable=False
    )
    to_branch_id: Mapped[str] = mapped_column(
        String, ForeignKey("offices.id"), nullable=False
    )
    from_stock_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    to_stock_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(
        String, default="PENDING", nullable=False, server_default="'PENDING'"
    )

    # Request details
    requested_by: Mapped[str] = mapped_column(String, nullable=False)
    requested_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, server_default="NOW()"
    )

    # Approval details
    approved_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    # Completion details
    completed_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    # Rejection details
    rejected_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    rejected_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Additional info
    transfer_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reference_doc_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Transfer costs
    transfer_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=0, server_default="0"
    )
    cost_breakdown: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True, default=dict, server_default="'{}'::jsonb"
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, server_default="NOW()"
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, server_default="NOW()", onupdate=datetime.utcnow
    )

    # Relationships
    bicycle: Mapped["Bicycle"] = relationship("Bicycle", back_populates="transfers")
    from_branch: Mapped["Office"] = relationship("Office", foreign_keys=[from_branch_id])
    to_branch: Mapped["Office"] = relationship("Office", foreign_keys=[to_branch_id])

    def approve(self, approved_by: str) -> None:
        """Approve the transfer"""
        if self.status != TransferStatus.PENDING.value:
            raise ValueError(f"Cannot approve transfer in status {self.status}")
        self.status = TransferStatus.APPROVED.value
        self.approved_by = approved_by
        self.approved_at = datetime.utcnow()

    def complete(self, completed_by: str) -> None:
        """Mark transfer as completed"""
        if self.status != TransferStatus.APPROVED.value:
            raise ValueError(f"Cannot complete transfer in status {self.status}")
        self.status = TransferStatus.COMPLETED.value
        self.completed_by = completed_by
        self.completed_at = datetime.utcnow()

    def reject(self, rejected_by: str, reason: str) -> None:
        """Reject the transfer"""
        if self.status not in [TransferStatus.PENDING.value, TransferStatus.APPROVED.value]:
            raise ValueError(f"Cannot reject transfer in status {self.status}")
        self.status = TransferStatus.REJECTED.value
        self.rejected_by = rejected_by
        self.rejected_at = datetime.utcnow()
        self.rejection_reason = reason

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "bicycle_id": self.bicycle_id,
            "from_branch_id": self.from_branch_id,
            "to_branch_id": self.to_branch_id,
            "from_stock_number": self.from_stock_number,
            "to_stock_number": self.to_stock_number,
            "status": self.status,
            "requested_by": self.requested_by,
            "requested_at": self.requested_at.isoformat() if self.requested_at else None,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "completed_by": self.completed_by,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "rejected_by": self.rejected_by,
            "rejected_at": self.rejected_at.isoformat() if self.rejected_at else None,
            "rejection_reason": self.rejection_reason,
            "transfer_reason": self.transfer_reason,
            "reference_doc_number": self.reference_doc_number,
            "notes": self.notes,
            "transfer_cost": float(self.transfer_cost) if self.transfer_cost else 0.0,
            "cost_breakdown": self.cost_breakdown or {},
        }
