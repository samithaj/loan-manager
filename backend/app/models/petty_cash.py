from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Numeric, Text, Date, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import TIMESTAMP
from datetime import datetime, date
from typing import Optional, Any, TYPE_CHECKING
from enum import Enum
from ..db import Base

if TYPE_CHECKING:
    from .branch import Branch
    from .user import User
    from .fund_source import FundSource


class VoucherType(str, Enum):
    """Petty cash voucher type"""
    RECEIPT = "RECEIPT"  # Money in
    DISBURSEMENT = "DISBURSEMENT"  # Money out


class VoucherStatus(str, Enum):
    """Voucher status"""
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    POSTED = "POSTED"
    VOID = "VOID"


class PettyCashFloat(Base):
    """Petty cash float management per branch/fund source"""
    __tablename__ = "petty_cash_floats"

    id: Mapped[str] = mapped_column(String, primary_key=True)

    # Branch and fund source
    branch_id: Mapped[str] = mapped_column(String, ForeignKey("branches.id"), nullable=False, index=True)
    fund_source_id: Mapped[str] = mapped_column(String, ForeignKey("fund_sources.id"), nullable=False)

    # Float details
    opening_balance: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    current_balance: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    # Last reconciliation
    last_reconciled_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    last_reconciled_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    reconciled_balance: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)

    # Custodian
    custodian_user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    # Audit
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, server_default="NOW()"
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow,
        server_default="NOW()", onupdate=datetime.utcnow
    )
    created_by: Mapped[str] = mapped_column(String, nullable=False)

    # Relationships
    branch: Mapped["Branch"] = relationship("Branch", foreign_keys=[branch_id])
    fund_source: Mapped["FundSource"] = relationship("FundSource")
    custodian: Mapped["User"] = relationship("User", foreign_keys=[custodian_user_id])
    vouchers: Mapped[list["PettyCashVoucher"]] = relationship(
        "PettyCashVoucher", back_populates="petty_cash_float", cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert petty cash float to dictionary"""
        return {
            "id": self.id,
            "branch_id": self.branch_id,
            "fund_source_id": self.fund_source_id,
            "opening_balance": float(self.opening_balance) if self.opening_balance else 0,
            "current_balance": float(self.current_balance) if self.current_balance else 0,
            "last_reconciled_at": self.last_reconciled_at.isoformat() if self.last_reconciled_at else None,
            "last_reconciled_by": self.last_reconciled_by,
            "reconciled_balance": float(self.reconciled_balance) if self.reconciled_balance else None,
            "custodian_user_id": self.custodian_user_id,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "variance": self.calculate_variance(),
        }

    def calculate_variance(self) -> Optional[float]:
        """Calculate variance between current balance and reconciled balance"""
        if self.reconciled_balance is None:
            return None
        return float(self.current_balance) - float(self.reconciled_balance)

    def update_balance(self, amount: float, is_receipt: bool) -> None:
        """Update current balance"""
        if is_receipt:
            self.current_balance = float(self.current_balance) + amount
        else:
            self.current_balance = float(self.current_balance) - amount

    def reconcile(self, reconciled_by: str, actual_balance: float) -> None:
        """Reconcile petty cash"""
        self.last_reconciled_at = datetime.utcnow()
        self.last_reconciled_by = reconciled_by
        self.reconciled_balance = actual_balance


class PettyCashVoucher(Base):
    """Petty cash vouchers (receipts and disbursements)"""
    __tablename__ = "petty_cash_vouchers"

    id: Mapped[str] = mapped_column(String, primary_key=True)

    # Link to petty cash float
    petty_cash_float_id: Mapped[str] = mapped_column(
        String, ForeignKey("petty_cash_floats.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Voucher details
    voucher_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    voucher_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    voucher_type: Mapped[str] = mapped_column(String(20), nullable=False)  # RECEIPT or DISBURSEMENT

    # Amount
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    # Payee/Payer
    payee_payer: Mapped[str] = mapped_column(String(200), nullable=False)

    # Description
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Category/Expense type
    expense_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # GL account (for posting to journal)
    gl_account_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("chart_of_accounts.id"), nullable=True
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="DRAFT", server_default="'DRAFT'", index=True
    )

    # Approval
    approved_by: Mapped[Optional[str]] = mapped_column(String, ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    # Rejection
    rejected_by: Mapped[Optional[str]] = mapped_column(String, ForeignKey("users.id"), nullable=True)
    rejected_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Posted to journal
    posted_to_journal: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    journal_entry_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("journal_entries.id"), nullable=True
    )

    # Receipt attachment
    receipt_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

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
    petty_cash_float: Mapped["PettyCashFloat"] = relationship("PettyCashFloat", back_populates="vouchers")
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])
    approver: Mapped[Optional["User"]] = relationship("User", foreign_keys=[approved_by])
    rejecter: Mapped[Optional["User"]] = relationship("User", foreign_keys=[rejected_by])

    def to_dict(self) -> dict[str, Any]:
        """Convert petty cash voucher to dictionary"""
        return {
            "id": self.id,
            "petty_cash_float_id": self.petty_cash_float_id,
            "voucher_number": self.voucher_number,
            "voucher_date": self.voucher_date.isoformat() if self.voucher_date else None,
            "voucher_type": self.voucher_type,
            "amount": float(self.amount) if self.amount else 0,
            "payee_payer": self.payee_payer,
            "description": self.description,
            "expense_category": self.expense_category,
            "gl_account_id": self.gl_account_id,
            "status": self.status,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "rejected_by": self.rejected_by,
            "rejected_at": self.rejected_at.isoformat() if self.rejected_at else None,
            "rejection_reason": self.rejection_reason,
            "posted_to_journal": self.posted_to_journal,
            "journal_entry_id": self.journal_entry_id,
            "receipt_url": self.receipt_url,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
        }

    def approve(self, approved_by: str) -> None:
        """Approve the voucher"""
        if self.status != VoucherStatus.DRAFT.value:
            raise ValueError(f"Cannot approve voucher in status {self.status}")

        self.status = VoucherStatus.APPROVED.value
        self.approved_by = approved_by
        self.approved_at = datetime.utcnow()

    def reject(self, rejected_by: str, reason: str) -> None:
        """Reject the voucher"""
        if self.status != VoucherStatus.DRAFT.value:
            raise ValueError(f"Cannot reject voucher in status {self.status}")

        self.status = VoucherStatus.REJECTED.value
        self.rejected_by = rejected_by
        self.rejected_at = datetime.utcnow()
        self.rejection_reason = reason

    def post_to_journal(self, journal_entry_id: str) -> None:
        """Mark voucher as posted to journal"""
        if self.status != VoucherStatus.APPROVED.value:
            raise ValueError(f"Cannot post voucher in status {self.status}")

        self.posted_to_journal = True
        self.journal_entry_id = journal_entry_id
        self.status = VoucherStatus.POSTED.value
