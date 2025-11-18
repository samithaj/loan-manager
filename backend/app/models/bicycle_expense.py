from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Date, ForeignKey, Text, Numeric
from sqlalchemy.dialects.postgresql import TIMESTAMP
from datetime import datetime, date
from enum import Enum
from typing import Optional, Any, TYPE_CHECKING
from ..db import Base

if TYPE_CHECKING:
    from .bicycle import Bicycle
    from .reference import Office


class ExpenseCategory(str, Enum):
    TRANSPORT = "TRANSPORT"
    MINOR_REPAIR = "MINOR_REPAIR"
    LICENSE_RENEWAL = "LICENSE_RENEWAL"
    INSURANCE = "INSURANCE"
    CLEANING = "CLEANING"
    DOCUMENTATION = "DOCUMENTATION"
    STORAGE = "STORAGE"
    OTHER = "OTHER"


class BicycleBranchExpense(Base):
    __tablename__ = "bicycle_branch_expenses"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    bicycle_id: Mapped[str] = mapped_column(
        String, ForeignKey("bicycles.id", ondelete="CASCADE"), nullable=False
    )
    branch_id: Mapped[str] = mapped_column(
        String, ForeignKey("offices.id"), nullable=False
    )
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    invoice_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    vendor_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    recorded_by: Mapped[str] = mapped_column(String, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, server_default="NOW()"
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, server_default="NOW()", onupdate=datetime.utcnow
    )

    # Relationships
    bicycle: Mapped["Bicycle"] = relationship("Bicycle", back_populates="branch_expenses")
    branch: Mapped["Office"] = relationship("Office")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "bicycle_id": self.bicycle_id,
            "branch_id": self.branch_id,
            "expense_date": self.expense_date.isoformat() if self.expense_date else None,
            "description": self.description,
            "category": self.category,
            "amount": float(self.amount) if self.amount else 0,
            "invoice_number": self.invoice_number,
            "vendor_name": self.vendor_name,
            "recorded_by": self.recorded_by,
            "notes": self.notes,
        }
