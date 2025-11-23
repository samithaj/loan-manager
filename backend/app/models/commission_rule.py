from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Numeric, Text, ForeignKey, Boolean, Integer
from sqlalchemy.dialects.postgresql import TIMESTAMP, JSONB
from datetime import datetime
from typing import Optional, Any, TYPE_CHECKING
from enum import Enum
from decimal import Decimal
from ..db import Base

if TYPE_CHECKING:
    from .reference import Staff


class CommissionType(str, Enum):
    """Commission type enumeration"""
    BIKE_SALE = "BIKE_SALE"
    LOAN_APPROVAL = "LOAN_APPROVAL"
    LOAN_DISBURSEMENT = "LOAN_DISBURSEMENT"
    REFERRAL = "REFERRAL"


class FormulaType(str, Enum):
    """Commission formula type"""
    FLAT_RATE = "FLAT_RATE"  # Fixed amount per transaction
    PERCENTAGE_OF_SALE = "PERCENTAGE_OF_SALE"  # % of sale price
    PERCENTAGE_OF_PROFIT = "PERCENTAGE_OF_PROFIT"  # % of profit (sale price - cost)
    TIERED = "TIERED"  # Different rates for different tiers
    CUSTOM = "CUSTOM"  # Custom formula (future)


class TierBasis(str, Enum):
    """Basis for tiered commission"""
    SALE_AMOUNT = "SALE_AMOUNT"
    PROFIT_AMOUNT = "PROFIT_AMOUNT"
    UNIT_COUNT = "UNIT_COUNT"


class CommissionRule(Base):
    """Commission rules for different roles and transaction types"""
    __tablename__ = "commission_rules"

    id: Mapped[str] = mapped_column(String, primary_key=True)

    # Rule identification
    rule_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Commission type
    commission_type: Mapped[str] = mapped_column(String(30), nullable=False)

    # Applicable roles
    applicable_roles: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default="'[]'::jsonb"
    )  # ["salesperson", "lmo", "branch_manager"]

    # Formula configuration
    formula_type: Mapped[str] = mapped_column(String(30), nullable=False)

    # For FLAT_RATE
    flat_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)

    # For PERCENTAGE_OF_SALE and PERCENTAGE_OF_PROFIT
    percentage_rate: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)

    # For TIERED
    tier_basis: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    tier_configuration: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    # Example tier_configuration:
    # {
    #   "tiers": [
    #     {"min": 0, "max": 100000, "rate": 2.0},
    #     {"min": 100001, "max": 500000, "rate": 3.0},
    #     {"min": 500001, "max": null, "rate": 5.0}
    #   ]
    # }

    # Minimum and maximum commission
    min_commission: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    max_commission: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)

    # Conditions
    min_sale_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    min_profit_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)

    # Branch restriction (null = applies to all branches)
    branch_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Vehicle condition filter (null = applies to all)
    vehicle_condition: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # NEW, USED

    # Priority (higher priority rules are applied first)
    priority: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    # Active status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    # Effective dates
    effective_from: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    effective_until: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    # Audit
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, server_default="NOW()"
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow,
        server_default="NOW()", onupdate=datetime.utcnow
    )
    created_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    def to_dict(self) -> dict[str, Any]:
        """Convert commission rule to dictionary"""
        return {
            "id": self.id,
            "rule_name": self.rule_name,
            "description": self.description,
            "commission_type": self.commission_type,
            "applicable_roles": self.applicable_roles,
            "formula_type": self.formula_type,
            "flat_amount": float(self.flat_amount) if self.flat_amount else None,
            "percentage_rate": float(self.percentage_rate) if self.percentage_rate else None,
            "tier_basis": self.tier_basis,
            "tier_configuration": self.tier_configuration,
            "min_commission": float(self.min_commission) if self.min_commission else None,
            "max_commission": float(self.max_commission) if self.max_commission else None,
            "min_sale_amount": float(self.min_sale_amount) if self.min_sale_amount else None,
            "min_profit_amount": float(self.min_profit_amount) if self.min_profit_amount else None,
            "branch_id": self.branch_id,
            "vehicle_condition": self.vehicle_condition,
            "priority": self.priority,
            "is_active": self.is_active,
            "effective_from": self.effective_from.isoformat() if self.effective_from else None,
            "effective_until": self.effective_until.isoformat() if self.effective_until else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def calculate_commission(
        self,
        sale_amount: float,
        cost_amount: float,
        unit_count: int = 1
    ) -> float:
        """
        Calculate commission based on rule configuration

        Args:
            sale_amount: Sale price
            cost_amount: Total cost
            unit_count: Number of units (for unit-based tiering)

        Returns:
            Commission amount
        """
        profit_amount = sale_amount - cost_amount

        # Check minimum thresholds
        if self.min_sale_amount and sale_amount < float(self.min_sale_amount):
            return 0.0
        if self.min_profit_amount and profit_amount < float(self.min_profit_amount):
            return 0.0

        commission = 0.0

        if self.formula_type == FormulaType.FLAT_RATE.value:
            commission = float(self.flat_amount or 0)

        elif self.formula_type == FormulaType.PERCENTAGE_OF_SALE.value:
            commission = sale_amount * (float(self.percentage_rate or 0) / 100)

        elif self.formula_type == FormulaType.PERCENTAGE_OF_PROFIT.value:
            commission = profit_amount * (float(self.percentage_rate or 0) / 100)

        elif self.formula_type == FormulaType.TIERED.value:
            commission = self._calculate_tiered_commission(
                sale_amount, profit_amount, unit_count
            )

        # Apply min/max constraints
        if self.min_commission:
            commission = max(commission, float(self.min_commission))
        if self.max_commission:
            commission = min(commission, float(self.max_commission))

        return round(commission, 2)

    def _calculate_tiered_commission(
        self, sale_amount: float, profit_amount: float, unit_count: int
    ) -> float:
        """Calculate tiered commission based on tier configuration"""
        if not self.tier_configuration or "tiers" not in self.tier_configuration:
            return 0.0

        # Determine the value to use for tiering
        if self.tier_basis == TierBasis.SALE_AMOUNT.value:
            tier_value = sale_amount
        elif self.tier_basis == TierBasis.PROFIT_AMOUNT.value:
            tier_value = profit_amount
        elif self.tier_basis == TierBasis.UNIT_COUNT.value:
            tier_value = unit_count
        else:
            tier_value = sale_amount

        # Find applicable tier
        tiers = self.tier_configuration.get("tiers", [])
        for tier in sorted(tiers, key=lambda t: t.get("min", 0)):
            min_val = tier.get("min", 0)
            max_val = tier.get("max")

            if max_val is None:
                # Last tier (no max)
                if tier_value >= min_val:
                    rate = tier.get("rate", 0)
                    # Apply rate to profit or sale based on tier basis
                    if self.tier_basis == TierBasis.UNIT_COUNT.value:
                        return unit_count * rate
                    elif self.tier_basis == TierBasis.PROFIT_AMOUNT.value:
                        return profit_amount * (rate / 100)
                    else:
                        return sale_amount * (rate / 100)
            else:
                if min_val <= tier_value <= max_val:
                    rate = tier.get("rate", 0)
                    if self.tier_basis == TierBasis.UNIT_COUNT.value:
                        return unit_count * rate
                    elif self.tier_basis == TierBasis.PROFIT_AMOUNT.value:
                        return profit_amount * (rate / 100)
                    else:
                        return sale_amount * (rate / 100)

        return 0.0

    def is_effective(self, check_date: Optional[datetime] = None) -> bool:
        """Check if rule is effective on a given date"""
        if not self.is_active:
            return False

        check_date = check_date or datetime.utcnow()

        if self.effective_from and check_date < self.effective_from:
            return False
        if self.effective_until and check_date > self.effective_until:
            return False

        return True
