from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Numeric, Date, DateTime, Boolean, Text, UUID
from datetime import datetime, date
from typing import Optional
from enum import Enum
from ..db import Base


class LeaveStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class LeaveType(Base):
    __tablename__ = "leave_types"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    default_days_per_year: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    requires_approval: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    requires_documentation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    max_consecutive_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_paid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "default_days_per_year": self.default_days_per_year,
            "requires_approval": self.requires_approval,
            "requires_documentation": self.requires_documentation,
            "max_consecutive_days": self.max_consecutive_days,
            "is_paid": self.is_paid,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class LeaveBalance(Base):
    __tablename__ = "leave_balances"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(UUID, nullable=False)  # References users.id
    leave_type_id: Mapped[str] = mapped_column(String, nullable=False)  # References leave_types.id
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    entitled_days: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    used_days: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    pending_days: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    # remaining_days is computed column in DB
    carried_forward_days: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def remaining_days(self) -> float:
        """Calculate remaining days"""
        return float(self.entitled_days) - float(self.used_days) - float(self.pending_days)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": str(self.user_id),
            "leave_type_id": self.leave_type_id,
            "year": self.year,
            "entitled_days": float(self.entitled_days),
            "used_days": float(self.used_days),
            "pending_days": float(self.pending_days),
            "remaining_days": self.remaining_days,
            "carried_forward_days": float(self.carried_forward_days),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class LeaveApplication(Base):
    __tablename__ = "leave_applications"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(UUID, nullable=False)  # References users.id
    leave_type_id: Mapped[str] = mapped_column(String, nullable=False)  # References leave_types.id
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_days: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default=LeaveStatus.PENDING.value)
    approver_id: Mapped[Optional[str]] = mapped_column(UUID, nullable=True)  # References users.id
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    approver_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    document_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def can_approve(self) -> bool:
        """Check if application can be approved"""
        return self.status == LeaveStatus.PENDING.value

    def can_reject(self) -> bool:
        """Check if application can be rejected"""
        return self.status == LeaveStatus.PENDING.value

    def can_cancel(self) -> bool:
        """Check if application can be cancelled"""
        return self.status in [LeaveStatus.PENDING.value, LeaveStatus.APPROVED.value]

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": str(self.user_id),
            "leave_type_id": self.leave_type_id,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "total_days": float(self.total_days),
            "reason": self.reason,
            "status": self.status,
            "approver_id": str(self.approver_id) if self.approver_id else None,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "approver_notes": self.approver_notes,
            "document_url": self.document_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
