from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import TIMESTAMP
from datetime import datetime
from typing import Optional, Any, TYPE_CHECKING
from enum import Enum
from ..db import Base

if TYPE_CHECKING:
    from .client import Client


class AccountType(str, Enum):
    """Bank account type enumeration"""
    SAVINGS = "SAVINGS"
    CURRENT = "CURRENT"
    FIXED_DEPOSIT = "FIXED_DEPOSIT"
    SALARY = "SALARY"


class BankAccountStatus(str, Enum):
    """Bank account status enumeration"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    CLOSED = "CLOSED"


class CustomerBankAccount(Base):
    """Customer bank account information"""
    __tablename__ = "customer_bank_accounts"

    id: Mapped[str] = mapped_column(String, primary_key=True)

    # Link to customer
    customer_id: Mapped[str] = mapped_column(
        String, ForeignKey("clients.id"), nullable=False, index=True
    )

    # Bank details
    bank_name: Mapped[str] = mapped_column(String(100), nullable=False)
    bank_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # Swift code or bank code
    branch_name: Mapped[str] = mapped_column(String(100), nullable=False)
    branch_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Account details
    account_number: Mapped[str] = mapped_column(String(50), nullable=False)
    account_name: Mapped[str] = mapped_column(String(200), nullable=False)
    account_type: Mapped[str] = mapped_column(String(30), nullable=False)

    # Account status
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="ACTIVE", server_default="'ACTIVE'"
    )

    # Primary account flag
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    # Salary account flag
    is_salary_account: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    # Verification
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    verified_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    verified_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    verification_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # BANK_STATEMENT, LETTER

    # Document references
    bank_statement_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    bank_letter_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

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
    created_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Relationships
    customer: Mapped["Client"] = relationship("Client", backref="bank_accounts")

    def to_dict(self) -> dict[str, Any]:
        """Convert bank account to dictionary"""
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "bank_name": self.bank_name,
            "bank_code": self.bank_code,
            "branch_name": self.branch_name,
            "branch_code": self.branch_code,
            "account_number": self.account_number,
            "account_name": self.account_name,
            "account_type": self.account_type,
            "status": self.status,
            "is_primary": self.is_primary,
            "is_salary_account": self.is_salary_account,
            "is_verified": self.is_verified,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "verified_by": self.verified_by,
            "verification_method": self.verification_method,
            "bank_statement_url": self.bank_statement_url,
            "bank_letter_url": self.bank_letter_url,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def verify(self, verified_by: str, method: str) -> None:
        """Mark bank account as verified"""
        self.is_verified = True
        self.verified_at = datetime.utcnow()
        self.verified_by = verified_by
        self.verification_method = method

    def mask_account_number(self) -> str:
        """Return masked account number for display"""
        if len(self.account_number) <= 4:
            return self.account_number
        return "*" * (len(self.account_number) - 4) + self.account_number[-4:]
