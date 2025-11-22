from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, text, DateTime, ForeignKey, Enum as SQLEnum, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from typing import TYPE_CHECKING, Optional, Any
from datetime import datetime
from enum import Enum
import uuid
from ..db import Base

if TYPE_CHECKING:
    from .user import User


class ApprovalDecision(str, Enum):
    """Decision types for leave approval"""
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    NEEDS_INFO = "NEEDS_INFO"


class ApproverRole(str, Enum):
    """Role of the approver"""
    BRANCH_MANAGER = "BRANCH_MANAGER"
    HEAD_MANAGER = "HEAD_MANAGER"
    ADMIN = "ADMIN"


class LeaveApproval(Base):
    """
    Tracks individual approval decisions in multi-level workflow
    Each leave request can have multiple approvals (Branch → HO)
    """
    __tablename__ = "leave_approvals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # Leave request reference (using string ID from existing leave_applications)
    leave_request_id: Mapped[str] = mapped_column(String, index=True)

    # Approver details
    approver_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    approver_role: Mapped[ApproverRole] = mapped_column(
        SQLEnum(ApproverRole, name="approver_role"), index=True
    )

    # Decision
    decision: Mapped[ApprovalDecision] = mapped_column(
        SQLEnum(ApprovalDecision, name="approval_decision")
    )
    notes: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)

    # Metadata
    decided_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )

    # Additional context
    meta_json: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, nullable=True, default=dict, server_default="'{}'::jsonb"
    )

    # Relationship
    approver: Mapped["User"] = relationship("User", foreign_keys=[approver_id])


class LeaveAuditLog(Base):
    """
    Complete audit trail for leave requests
    Tracks all state changes and actions
    """
    __tablename__ = "leave_audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # Leave request reference
    leave_request_id: Mapped[str] = mapped_column(String, index=True)

    # Actor (who performed the action)
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    # Action details
    action: Mapped[str] = mapped_column(String(100), index=True)
    old_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    new_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Additional payload
    payload_json: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, nullable=True, default=dict, server_default="'{}'::jsonb"
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), index=True
    )

    # Relationship
    actor: Mapped[Optional["User"]] = relationship("User", foreign_keys=[actor_id])


class LeavePolicy(Base):
    """
    Leave policies per branch/company
    Defines approval rules and workflows
    """
    __tablename__ = "leave_policies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # Policy scope
    branch_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("branches.id"), nullable=True
    )  # NULL = global/default policy

    # Leave type
    leave_type_id: Mapped[str] = mapped_column(String)  # FK to leave_types

    # Approval workflow rules
    requires_branch_approval: Mapped[bool] = mapped_column(Boolean, default=True)
    requires_ho_approval: Mapped[bool] = mapped_column(Boolean, default=False)

    # Auto-approval thresholds
    auto_approve_days_threshold: Mapped[Optional[int]] = mapped_column(nullable=True)

    # SLA (in hours)
    branch_approval_sla_hours: Mapped[Optional[int]] = mapped_column(nullable=True)
    ho_approval_sla_hours: Mapped[Optional[int]] = mapped_column(nullable=True)

    # Restrictions
    min_notice_days: Mapped[int] = mapped_column(default=0)  # How many days ahead must apply
    max_days_per_request: Mapped[Optional[int]] = mapped_column(nullable=True)
    allow_half_day: Mapped[bool] = mapped_column(Boolean, default=False)

    # Active flag
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=datetime.utcnow
    )
