from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import TIMESTAMP
from datetime import datetime
from typing import Optional, Any, TYPE_CHECKING
from ..db import Base

if TYPE_CHECKING:
    from .bicycle import Bicycle
    from .company import Company
    from .reference import Office


class StockNumberSequence(Base):
    __tablename__ = "stock_number_sequences"

    company_id: Mapped[str] = mapped_column(
        String, ForeignKey("companies.id"), primary_key=True
    )
    branch_id: Mapped[str] = mapped_column(
        String, ForeignKey("offices.id"), primary_key=True
    )
    current_number: Mapped[int] = mapped_column(Integer, default=0, nullable=False, server_default="0")
    last_assigned_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, server_default="NOW()"
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, server_default="NOW()", onupdate=datetime.utcnow
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "company_id": self.company_id,
            "branch_id": self.branch_id,
            "current_number": self.current_number,
            "last_assigned_at": self.last_assigned_at.isoformat() if self.last_assigned_at else None,
        }


class StockNumberAssignment(Base):
    __tablename__ = "stock_number_assignments"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    bicycle_id: Mapped[str] = mapped_column(
        String, ForeignKey("bicycles.id", ondelete="CASCADE"), nullable=False
    )
    company_id: Mapped[str] = mapped_column(
        String, ForeignKey("companies.id"), nullable=False
    )
    branch_id: Mapped[str] = mapped_column(
        String, ForeignKey("offices.id"), nullable=False
    )
    running_number: Mapped[int] = mapped_column(Integer, nullable=False)
    full_stock_number: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    assigned_date: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, server_default="NOW()"
    )
    released_date: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    assignment_reason: Mapped[str] = mapped_column(String, nullable=False)
    previous_assignment_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("stock_number_assignments.id"), nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, server_default="NOW()"
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, server_default="NOW()", onupdate=datetime.utcnow
    )

    # Relationships
    bicycle: Mapped["Bicycle"] = relationship("Bicycle", back_populates="stock_assignments")
    company: Mapped["Company"] = relationship("Company")
    branch: Mapped["Office"] = relationship("Office")
    previous_assignment: Mapped[Optional["StockNumberAssignment"]] = relationship(
        "StockNumberAssignment", remote_side=[id], foreign_keys=[previous_assignment_id]
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "bicycle_id": self.bicycle_id,
            "company_id": self.company_id,
            "branch_id": self.branch_id,
            "running_number": self.running_number,
            "full_stock_number": self.full_stock_number,
            "assigned_date": self.assigned_date.isoformat() if self.assigned_date else None,
            "released_date": self.released_date.isoformat() if self.released_date else None,
            "assignment_reason": self.assignment_reason,
            "previous_assignment_id": self.previous_assignment_id,
            "notes": self.notes,
        }

    @property
    def is_current(self) -> bool:
        """Check if this is the current assignment (not released)"""
        return self.released_date is None
