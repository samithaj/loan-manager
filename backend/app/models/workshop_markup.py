from __future__ import annotations

from sqlalchemy import String, Boolean, Numeric, Date, Integer, ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from datetime import date, datetime
from enum import Enum
from typing import Optional, List

from ..db import Base


class MarkupTargetType(str, Enum):
    PART_CATEGORY = "PART_CATEGORY"
    LABOUR = "LABOUR"
    OVERHEAD = "OVERHEAD"
    BIKE_SALE = "BIKE_SALE"
    DEFAULT = "DEFAULT"


class MarkupType(str, Enum):
    PERCENTAGE = "PERCENTAGE"
    FIXED_AMOUNT = "FIXED_AMOUNT"


class MarkupRule(Base):
    """Pricing markup rules for parts, labour, and bike sales"""
    __tablename__ = "markup_rules"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    target_type: Mapped[str] = mapped_column(String, nullable=False)
    target_value: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    markup_type: Mapped[str] = mapped_column(String, nullable=False)
    markup_value: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    applies_to_branches: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    priority: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default="NOW()")
    updated_at: Mapped[datetime] = mapped_column(nullable=False, server_default="NOW()")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "target_type": self.target_type,
            "target_value": self.target_value,
            "markup_type": self.markup_type,
            "markup_value": float(self.markup_value),
            "applies_to_branches": self.applies_to_branches,
            "effective_from": self.effective_from.isoformat(),
            "effective_to": self.effective_to.isoformat() if self.effective_to else None,
            "is_active": self.is_active,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    def is_effective(self, check_date: Optional[date] = None) -> bool:
        """Check if this rule is effective on a given date (default: today)"""
        if not self.is_active:
            return False

        if check_date is None:
            check_date = date.today()

        if check_date < self.effective_from:
            return False

        if self.effective_to and check_date > self.effective_to:
            return False

        return True

    def applies_to_branch(self, branch_id: str) -> bool:
        """Check if this rule applies to a specific branch"""
        if not self.applies_to_branches:
            return True  # Applies to all branches
        return branch_id in self.applies_to_branches

    def calculate_markup(self, base_amount: float) -> float:
        """Calculate marked-up amount based on rule"""
        if self.markup_type == MarkupType.PERCENTAGE.value:
            return base_amount * (1 + float(self.markup_value) / 100)
        elif self.markup_type == MarkupType.FIXED_AMOUNT.value:
            return base_amount + float(self.markup_value)
        return base_amount

    def calculate_markup_amount(self, base_amount: float) -> float:
        """Calculate just the markup amount (not the total)"""
        if self.markup_type == MarkupType.PERCENTAGE.value:
            return base_amount * (float(self.markup_value) / 100)
        elif self.markup_type == MarkupType.FIXED_AMOUNT.value:
            return float(self.markup_value)
        return 0.0
