from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, text, Numeric, DateTime, ForeignKey, Enum as SQLEnum, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from typing import TYPE_CHECKING, Optional, Any
from datetime import datetime
from enum import Enum
import uuid
from ..db import Base

if TYPE_CHECKING:
    from .bicycle import Bicycle
    from .branch import Branch
    from .fund_source import FundSource
    from .user import User


class CostEventType(str, Enum):
    """Types of cost events that can be recorded"""
    PURCHASE = "PURCHASE"
    BRANCH_TRANSFER = "BRANCH_TRANSFER"
    REPAIR_JOB = "REPAIR_JOB"
    SPARE_PARTS = "SPARE_PARTS"
    ADMIN_FEES = "ADMIN_FEES"
    REGISTRATION = "REGISTRATION"
    INSURANCE = "INSURANCE"
    TRANSPORT = "TRANSPORT"
    FUEL = "FUEL"
    INSPECTION = "INSPECTION"
    DOCUMENTATION = "DOCUMENTATION"
    OTHER_EXPENSE = "OTHER_EXPENSE"
    SALE = "SALE"


class VehicleCostLedger(Base):
    """
    Central ledger for all vehicle-related costs
    Each entry represents a cost transaction with full traceability
    """
    __tablename__ = "vehicle_cost_ledger"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # Vehicle reference (using bicycle_id from existing system)
    vehicle_id: Mapped[str] = mapped_column(String, ForeignKey("bicycles.id"), index=True)

    # Branch where cost was incurred
    branch_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("branches.id"))

    # Cost details
    event_type: Mapped[CostEventType] = mapped_column(
        SQLEnum(CostEventType, name="cost_event_type"), index=True
    )

    # Bill number format: <BRANCH_CODE>-<FUND_CODE>-<YYYYMMDD>-<SEQ>
    # Example: BD-PC-20251122-0041
    bill_no: Mapped[str] = mapped_column(String(50), unique=True, index=True)

    # Fund source (petty cash, bank, etc.)
    fund_source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fund_sources.id")
    )

    # Amount and currency
    amount: Mapped[float] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), default="LKR")

    # Description and notes
    description: Mapped[str] = mapped_column(String(500))
    notes: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)

    # Reference to source document/table
    reference_table: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    reference_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Receipt/bill attachments
    receipt_urls: Mapped[Optional[list[str]]] = mapped_column(
        JSONB, nullable=True, default=list, server_default="'[]'::jsonb"
    )

    # Metadata (tax details, quantities, unit costs, etc.)
    meta_json: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, nullable=True, default=dict, server_default="'{}'::jsonb"
    )

    # Audit fields
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), index=True
    )

    # Lock after sale (prevent edits)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    locked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    locked_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    # Approval workflow (optional)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=True)
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    vehicle: Mapped["Bicycle"] = relationship("Bicycle", foreign_keys=[vehicle_id])
    branch: Mapped["Branch"] = relationship("Branch", foreign_keys=[branch_id])
    fund_source: Mapped["FundSource"] = relationship("FundSource")
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])
