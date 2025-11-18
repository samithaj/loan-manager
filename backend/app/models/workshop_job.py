from __future__ import annotations

from sqlalchemy import String, Numeric, Integer, Text, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from enum import Enum
from typing import Optional

from .base import Base


class RepairJobType(str, Enum):
    SERVICE = "SERVICE"
    ACCIDENT_REPAIR = "ACCIDENT_REPAIR"
    FULL_OVERHAUL_BEFORE_SALE = "FULL_OVERHAUL_BEFORE_SALE"
    MAINTENANCE = "MAINTENANCE"
    CUSTOM_WORK = "CUSTOM_WORK"
    WARRANTY_REPAIR = "WARRANTY_REPAIR"


class RepairJobStatus(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    INVOICED = "INVOICED"
    CANCELLED = "CANCELLED"


class RepairJob(Base):
    """Work orders for bicycle repairs and overhauls"""
    __tablename__ = "repair_jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    job_number: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    bicycle_id: Mapped[str] = mapped_column(String, nullable=False)
    branch_id: Mapped[str] = mapped_column(String, nullable=False)
    job_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, server_default="OPEN")
    opened_at: Mapped[datetime] = mapped_column(nullable=False, server_default="NOW()")
    started_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    odometer: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    customer_complaint: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    diagnosis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    work_performed: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mechanic_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Costing summary (calculated)
    total_parts_cost: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, server_default="0")
    total_labour_cost: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, server_default="0")
    total_overhead_cost: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, server_default="0")
    total_cost: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, server_default="0")

    # Customer pricing (with markup)
    total_parts_price: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, server_default="0")
    total_labour_price: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, server_default="0")
    total_overhead_price: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, server_default="0")
    total_price: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, server_default="0")

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default="NOW()")
    updated_at: Mapped[datetime] = mapped_column(nullable=False, server_default="NOW()")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "job_number": self.job_number,
            "bicycle_id": self.bicycle_id,
            "branch_id": self.branch_id,
            "job_type": self.job_type,
            "status": self.status,
            "opened_at": self.opened_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "odometer": self.odometer,
            "customer_complaint": self.customer_complaint,
            "diagnosis": self.diagnosis,
            "work_performed": self.work_performed,
            "mechanic_id": self.mechanic_id,
            "created_by": self.created_by,
            "total_parts_cost": float(self.total_parts_cost),
            "total_labour_cost": float(self.total_labour_cost),
            "total_overhead_cost": float(self.total_overhead_cost),
            "total_cost": float(self.total_cost),
            "total_parts_price": float(self.total_parts_price),
            "total_labour_price": float(self.total_labour_price),
            "total_overhead_price": float(self.total_overhead_price),
            "total_price": float(self.total_price),
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    def can_edit(self) -> bool:
        """Check if job can be edited"""
        return self.status in [RepairJobStatus.OPEN.value, RepairJobStatus.IN_PROGRESS.value]

    def can_complete(self) -> bool:
        """Check if job can be marked as completed"""
        return self.status == RepairJobStatus.IN_PROGRESS.value

    def calculate_totals(self) -> dict:
        """Calculate summary totals - to be used after parts/labour/overhead are added"""
        return {
            "total_cost": float(self.total_parts_cost) + float(self.total_labour_cost) + float(self.total_overhead_cost),
            "total_price": float(self.total_parts_price) + float(self.total_labour_price) + float(self.total_overhead_price)
        }


class RepairJobPart(Base):
    """Parts used in repair jobs with batch-level costing"""
    __tablename__ = "repair_job_parts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    job_id: Mapped[str] = mapped_column(String, nullable=False)
    part_id: Mapped[str] = mapped_column(String, nullable=False)
    batch_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    quantity_used: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    unit_cost: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    total_cost: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    unit_price_to_customer: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)
    total_price_to_customer: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default="NOW()")

    __table_args__ = (
        CheckConstraint("quantity_used > 0", name="positive_quantity"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "job_id": self.job_id,
            "part_id": self.part_id,
            "batch_id": self.batch_id,
            "quantity_used": float(self.quantity_used),
            "unit_cost": float(self.unit_cost),
            "total_cost": float(self.total_cost),
            "unit_price_to_customer": float(self.unit_price_to_customer) if self.unit_price_to_customer else None,
            "total_price_to_customer": float(self.total_price_to_customer) if self.total_price_to_customer else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat()
        }


class RepairJobLabour(Base):
    """Labour charges for repair jobs"""
    __tablename__ = "repair_job_labour"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    job_id: Mapped[str] = mapped_column(String, nullable=False)
    labour_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    mechanic_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    hours: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    hourly_rate_cost: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    labour_cost: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    hourly_rate_customer: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)
    labour_price_to_customer: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default="NOW()")

    __table_args__ = (
        CheckConstraint("hours > 0", name="positive_hours"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "job_id": self.job_id,
            "labour_code": self.labour_code,
            "description": self.description,
            "mechanic_id": self.mechanic_id,
            "hours": float(self.hours),
            "hourly_rate_cost": float(self.hourly_rate_cost),
            "labour_cost": float(self.labour_cost),
            "hourly_rate_customer": float(self.hourly_rate_customer) if self.hourly_rate_customer else None,
            "labour_price_to_customer": float(self.labour_price_to_customer) if self.labour_price_to_customer else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat()
        }


class RepairJobOverhead(Base):
    """Overhead and miscellaneous charges for repair jobs"""
    __tablename__ = "repair_job_overheads"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    job_id: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    cost: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    price_to_customer: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default="NOW()")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "job_id": self.job_id,
            "description": self.description,
            "cost": float(self.cost),
            "price_to_customer": float(self.price_to_customer) if self.price_to_customer else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat()
        }
