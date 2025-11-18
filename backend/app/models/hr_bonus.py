from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Numeric, Date, DateTime, Boolean, Text, UUID, ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from enum import Enum
from ..db import Base


class TargetType(str, Enum):
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    YEARLY = "YEARLY"


class BonusRuleType(str, Enum):
    FIXED = "FIXED"
    PERCENTAGE = "PERCENTAGE"
    TIERED = "TIERED"
    COMMISSION = "COMMISSION"


class BonusPaymentStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    PAID = "PAID"
    REJECTED = "REJECTED"


class SalesTarget(Base):
    __tablename__ = "sales_targets"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(UUID, nullable=False)  # References users.id
    target_type: Mapped[str] = mapped_column(String, nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    target_loans: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    target_loan_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    target_bicycles: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    target_bicycle_revenue: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    created_by: Mapped[Optional[str]] = mapped_column(UUID, nullable=True)  # References users.id
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": str(self.user_id),
            "target_type": self.target_type,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "target_loans": self.target_loans,
            "target_loan_amount": float(self.target_loan_amount),
            "target_bicycles": self.target_bicycles,
            "target_bicycle_revenue": float(self.target_bicycle_revenue),
            "created_by": str(self.created_by) if self.created_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class PerformanceMetric(Base):
    __tablename__ = "performance_metrics"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(UUID, nullable=False)  # References users.id
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    actual_loans: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    actual_loan_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    actual_bicycles: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    actual_bicycle_revenue: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    achievement_percentage: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    calculated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": str(self.user_id),
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "actual_loans": self.actual_loans,
            "actual_loan_amount": float(self.actual_loan_amount),
            "actual_bicycles": self.actual_bicycles,
            "actual_bicycle_revenue": float(self.actual_bicycle_revenue),
            "achievement_percentage": float(self.achievement_percentage),
            "calculated_at": self.calculated_at.isoformat() if self.calculated_at else None,
        }


class BonusRule(Base):
    __tablename__ = "bonus_rules"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rule_type: Mapped[str] = mapped_column(String, nullable=False)
    applies_to_roles: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    min_achievement_percentage: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    base_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    percentage_rate: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    commission_rate: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "rule_type": self.rule_type,
            "applies_to_roles": self.applies_to_roles,
            "min_achievement_percentage": float(self.min_achievement_percentage),
            "base_amount": float(self.base_amount) if self.base_amount else None,
            "percentage_rate": float(self.percentage_rate) if self.percentage_rate else None,
            "commission_rate": float(self.commission_rate) if self.commission_rate else None,
            "is_active": self.is_active,
            "effective_from": self.effective_from.isoformat() if self.effective_from else None,
            "effective_to": self.effective_to.isoformat() if self.effective_to else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class BonusTier(Base):
    __tablename__ = "bonus_tiers"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    bonus_rule_id: Mapped[str] = mapped_column(String, nullable=False)  # References bonus_rules.id
    tier_order: Mapped[int] = mapped_column(Integer, nullable=False)
    achievement_from: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    achievement_to: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    bonus_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    bonus_percentage: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "bonus_rule_id": self.bonus_rule_id,
            "tier_order": self.tier_order,
            "achievement_from": float(self.achievement_from),
            "achievement_to": float(self.achievement_to),
            "bonus_amount": float(self.bonus_amount) if self.bonus_amount else None,
            "bonus_percentage": float(self.bonus_percentage) if self.bonus_percentage else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class BonusPayment(Base):
    __tablename__ = "bonus_payments"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(UUID, nullable=False)  # References users.id
    bonus_rule_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # References bonus_rules.id
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    target_amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)
    actual_amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)
    achievement_percentage: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    bonus_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    calculation_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default=BonusPaymentStatus.PENDING.value)
    approved_by: Mapped[Optional[str]] = mapped_column(UUID, nullable=True)  # References users.id
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    payment_reference: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def can_approve(self) -> bool:
        """Check if bonus payment can be approved"""
        return self.status == BonusPaymentStatus.PENDING.value

    def can_pay(self) -> bool:
        """Check if bonus payment can be paid"""
        return self.status == BonusPaymentStatus.APPROVED.value

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": str(self.user_id),
            "bonus_rule_id": self.bonus_rule_id,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "target_amount": float(self.target_amount) if self.target_amount else None,
            "actual_amount": float(self.actual_amount) if self.actual_amount else None,
            "achievement_percentage": float(self.achievement_percentage) if self.achievement_percentage else None,
            "bonus_amount": float(self.bonus_amount),
            "calculation_details": self.calculation_details,
            "status": self.status,
            "approved_by": str(self.approved_by) if self.approved_by else None,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "payment_reference": self.payment_reference,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
