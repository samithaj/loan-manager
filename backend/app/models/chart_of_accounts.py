from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, ForeignKey, Boolean, Integer
from sqlalchemy.dialects.postgresql import TIMESTAMP
from datetime import datetime
from typing import Optional, Any, TYPE_CHECKING, List
from enum import Enum
from ..db import Base

if TYPE_CHECKING:
    from .journal_entry import JournalEntryLine


class AccountCategory(str, Enum):
    """Account category enumeration (first level of chart of accounts)"""
    ASSET = "ASSET"
    LIABILITY = "LIABILITY"
    EQUITY = "EQUITY"
    REVENUE = "REVENUE"
    EXPENSE = "EXPENSE"


class AccountType(str, Enum):
    """Account type enumeration (subcategory)"""
    # Assets
    CURRENT_ASSET = "CURRENT_ASSET"
    FIXED_ASSET = "FIXED_ASSET"
    INVENTORY = "INVENTORY"
    ACCOUNTS_RECEIVABLE = "ACCOUNTS_RECEIVABLE"
    CASH_AND_BANK = "CASH_AND_BANK"

    # Liabilities
    CURRENT_LIABILITY = "CURRENT_LIABILITY"
    LONG_TERM_LIABILITY = "LONG_TERM_LIABILITY"
    ACCOUNTS_PAYABLE = "ACCOUNTS_PAYABLE"

    # Equity
    OWNER_EQUITY = "OWNER_EQUITY"
    RETAINED_EARNINGS = "RETAINED_EARNINGS"

    # Revenue
    SALES_REVENUE = "SALES_REVENUE"
    SERVICE_REVENUE = "SERVICE_REVENUE"
    OTHER_INCOME = "OTHER_INCOME"

    # Expenses
    COST_OF_GOODS_SOLD = "COST_OF_GOODS_SOLD"
    OPERATING_EXPENSE = "OPERATING_EXPENSE"
    ADMINISTRATIVE_EXPENSE = "ADMINISTRATIVE_EXPENSE"
    DEPRECIATION = "DEPRECIATION"
    INTEREST_EXPENSE = "INTEREST_EXPENSE"


class ChartOfAccounts(Base):
    """Chart of accounts for double-entry bookkeeping"""
    __tablename__ = "chart_of_accounts"

    id: Mapped[str] = mapped_column(String, primary_key=True)

    # Account code (e.g., "1000", "1100", "4010")
    account_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)

    # Account name
    account_name: Mapped[str] = mapped_column(String(200), nullable=False)

    # Description
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Account category (ASSET, LIABILITY, EQUITY, REVENUE, EXPENSE)
    category: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    # Account type (more specific classification)
    account_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Parent account (for hierarchical structure)
    parent_account_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("chart_of_accounts.id"), nullable=True
    )

    # Level in hierarchy (0 = top level, 1 = sub-account, etc.)
    level: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    # Is this a header account (summary) or detail account (transactional)
    is_header: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    # Normal balance (DEBIT or CREDIT)
    normal_balance: Mapped[str] = mapped_column(String(6), nullable=False)  # DEBIT or CREDIT

    # Branch-specific account (null = company-wide)
    branch_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Active status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    # System account (cannot be deleted by users)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

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
    parent_account: Mapped[Optional["ChartOfAccounts"]] = relationship(
        "ChartOfAccounts", remote_side=[id], back_populates="sub_accounts"
    )
    sub_accounts: Mapped[List["ChartOfAccounts"]] = relationship(
        "ChartOfAccounts", back_populates="parent_account"
    )
    journal_entry_lines: Mapped[List["JournalEntryLine"]] = relationship(
        "JournalEntryLine", back_populates="account"
    )

    def to_dict(self, include_children: bool = False) -> dict[str, Any]:
        """Convert account to dictionary"""
        result = {
            "id": self.id,
            "account_code": self.account_code,
            "account_name": self.account_name,
            "description": self.description,
            "category": self.category,
            "account_type": self.account_type,
            "parent_account_id": self.parent_account_id,
            "level": self.level,
            "is_header": self.is_header,
            "normal_balance": self.normal_balance,
            "branch_id": self.branch_id,
            "is_active": self.is_active,
            "is_system": self.is_system,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_children and self.sub_accounts:
            result["sub_accounts"] = [acc.to_dict(include_children=True) for acc in self.sub_accounts]

        return result

    def get_full_name(self) -> str:
        """Get full hierarchical account name"""
        if self.parent_account:
            return f"{self.parent_account.get_full_name()} > {self.account_name}"
        return self.account_name

    @classmethod
    def determine_normal_balance(cls, category: str) -> str:
        """Determine normal balance based on account category"""
        debit_categories = [AccountCategory.ASSET.value, AccountCategory.EXPENSE.value]
        if category in debit_categories:
            return "DEBIT"
        return "CREDIT"
