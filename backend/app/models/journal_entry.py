from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Numeric, Text, Date, ForeignKey, Boolean, CheckConstraint
from sqlalchemy.dialects.postgresql import TIMESTAMP
from datetime import datetime, date
from typing import Optional, Any, TYPE_CHECKING, List
from enum import Enum
from ..db import Base

if TYPE_CHECKING:
    from .chart_of_accounts import ChartOfAccounts
    from .branch import Branch
    from .user import User


class JournalEntryStatus(str, Enum):
    """Journal entry status"""
    DRAFT = "DRAFT"
    POSTED = "POSTED"
    VOID = "VOID"


class JournalEntryType(str, Enum):
    """Journal entry type"""
    GENERAL = "GENERAL"
    VEHICLE_PURCHASE = "VEHICLE_PURCHASE"
    VEHICLE_SALE = "VEHICLE_SALE"
    REPAIR_EXPENSE = "REPAIR_EXPENSE"
    PETTY_CASH = "PETTY_CASH"
    SALARY = "SALARY"
    COMMISSION = "COMMISSION"
    LOAN_DISBURSEMENT = "LOAN_DISBURSEMENT"
    LOAN_REPAYMENT = "LOAN_REPAYMENT"
    DEPRECIATION = "DEPRECIATION"
    ADJUSTMENT = "ADJUSTMENT"


class JournalEntry(Base):
    """Journal entries for double-entry bookkeeping"""
    __tablename__ = "journal_entries"

    id: Mapped[str] = mapped_column(String, primary_key=True)

    # Entry number (e.g., "JE-2025-0001")
    entry_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)

    # Entry date (accounting date)
    entry_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Entry type
    entry_type: Mapped[str] = mapped_column(String(30), nullable=False, default="GENERAL")

    # Description
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Status
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="DRAFT", server_default="'DRAFT'", index=True
    )

    # Branch
    branch_id: Mapped[str] = mapped_column(String, ForeignKey("branches.id"), nullable=False)

    # Reference to source document
    reference_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # SALE, PURCHASE, INVOICE
    reference_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    reference_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Totals (calculated from lines)
    total_debit: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0, server_default="0")
    total_credit: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0, server_default="0")

    # Posted status
    posted_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    posted_by: Mapped[Optional[str]] = mapped_column(String, ForeignKey("users.id"), nullable=True)

    # Void status
    voided_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    voided_by: Mapped[Optional[str]] = mapped_column(String, ForeignKey("users.id"), nullable=True)
    void_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Audit
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, server_default="NOW()"
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow,
        server_default="NOW()", onupdate=datetime.utcnow
    )
    created_by: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)

    # Relationships
    branch: Mapped["Branch"] = relationship("Branch", foreign_keys=[branch_id])
    lines: Mapped[List["JournalEntryLine"]] = relationship(
        "JournalEntryLine", back_populates="journal_entry", cascade="all, delete-orphan"
    )
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])
    poster: Mapped[Optional["User"]] = relationship("User", foreign_keys=[posted_by])
    voider: Mapped[Optional["User"]] = relationship("User", foreign_keys=[voided_by])

    __table_args__ = (
        CheckConstraint("total_debit = total_credit", name="check_balanced_entry"),
    )

    def to_dict(self, include_lines: bool = False) -> dict[str, Any]:
        """Convert journal entry to dictionary"""
        result = {
            "id": self.id,
            "entry_number": self.entry_number,
            "entry_date": self.entry_date.isoformat() if self.entry_date else None,
            "entry_type": self.entry_type,
            "description": self.description,
            "status": self.status,
            "branch_id": self.branch_id,
            "reference_type": self.reference_type,
            "reference_id": self.reference_id,
            "reference_number": self.reference_number,
            "total_debit": float(self.total_debit) if self.total_debit else 0,
            "total_credit": float(self.total_credit) if self.total_credit else 0,
            "posted_at": self.posted_at.isoformat() if self.posted_at else None,
            "posted_by": self.posted_by,
            "voided_at": self.voided_at.isoformat() if self.voided_at else None,
            "voided_by": self.voided_by,
            "void_reason": self.void_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
        }

        if include_lines and self.lines:
            result["lines"] = [line.to_dict() for line in self.lines]

        return result

    def post(self, posted_by: str) -> None:
        """Post the journal entry"""
        if self.status != JournalEntryStatus.DRAFT.value:
            raise ValueError(f"Cannot post entry in status {self.status}")
        if not self.is_balanced():
            raise ValueError("Cannot post unbalanced entry")

        self.status = JournalEntryStatus.POSTED.value
        self.posted_at = datetime.utcnow()
        self.posted_by = posted_by

    def void(self, voided_by: str, reason: str) -> None:
        """Void the journal entry"""
        if self.status != JournalEntryStatus.POSTED.value:
            raise ValueError(f"Cannot void entry in status {self.status}")

        self.status = JournalEntryStatus.VOID.value
        self.voided_at = datetime.utcnow()
        self.voided_by = voided_by
        self.void_reason = reason

    def is_balanced(self) -> bool:
        """Check if debits equal credits"""
        return abs(float(self.total_debit) - float(self.total_credit)) < 0.01

    def recalculate_totals(self) -> None:
        """Recalculate total debit and credit from lines"""
        self.total_debit = sum(float(line.debit_amount or 0) for line in self.lines)
        self.total_credit = sum(float(line.credit_amount or 0) for line in self.lines)


class JournalEntryLine(Base):
    """Journal entry lines (individual debits and credits)"""
    __tablename__ = "journal_entry_lines"

    id: Mapped[str] = mapped_column(String, primary_key=True)

    # Link to journal entry
    journal_entry_id: Mapped[str] = mapped_column(
        String, ForeignKey("journal_entries.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Line number (for ordering)
    line_number: Mapped[int] = mapped_column(nullable=False)

    # Account
    account_id: Mapped[str] = mapped_column(
        String, ForeignKey("chart_of_accounts.id"), nullable=False, index=True
    )

    # Description (can override entry description)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Debit amount (null means credit line)
    debit_amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)

    # Credit amount (null means debit line)
    credit_amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)

    # Cost center / department (optional)
    cost_center: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Audit
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, server_default="NOW()"
    )

    # Relationships
    journal_entry: Mapped["JournalEntry"] = relationship("JournalEntry", back_populates="lines")
    account: Mapped["ChartOfAccounts"] = relationship("ChartOfAccounts", back_populates="journal_entry_lines")

    __table_args__ = (
        CheckConstraint(
            "(debit_amount IS NOT NULL AND credit_amount IS NULL) OR (debit_amount IS NULL AND credit_amount IS NOT NULL)",
            name="check_debit_or_credit"
        ),
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert journal entry line to dictionary"""
        return {
            "id": self.id,
            "journal_entry_id": self.journal_entry_id,
            "line_number": self.line_number,
            "account_id": self.account_id,
            "account_code": self.account.account_code if self.account else None,
            "account_name": self.account.account_name if self.account else None,
            "description": self.description,
            "debit_amount": float(self.debit_amount) if self.debit_amount else None,
            "credit_amount": float(self.credit_amount) if self.credit_amount else None,
            "cost_center": self.cost_center,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @property
    def amount(self) -> float:
        """Get the line amount (debit or credit)"""
        return float(self.debit_amount or self.credit_amount or 0)

    @property
    def is_debit(self) -> bool:
        """Check if this is a debit line"""
        return self.debit_amount is not None
