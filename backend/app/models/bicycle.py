from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Numeric, Text, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from datetime import datetime
from enum import Enum
from typing import Optional, Any
from ..db import Base


class BicycleCondition(str, Enum):
    """Bicycle condition enumeration"""
    NEW = "NEW"
    USED = "USED"


class BicycleStatus(str, Enum):
    """Bicycle status enumeration"""
    AVAILABLE = "AVAILABLE"
    RESERVED = "RESERVED"
    SOLD = "SOLD"
    MAINTENANCE = "MAINTENANCE"


class Bicycle(Base):
    __tablename__ = "bicycles"

    # Primary identification
    id: Mapped[str] = mapped_column(String, primary_key=True)

    # Basic information
    title: Mapped[str] = mapped_column(String, nullable=False)
    brand: Mapped[str] = mapped_column(String, nullable=False)
    model: Mapped[str] = mapped_column(String, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    condition: Mapped[str] = mapped_column(String, nullable=False)

    # Vehicle identification
    license_plate: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)
    frame_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    engine_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Pricing
    purchase_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    cash_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    hire_purchase_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    duty_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0, server_default="0")
    registration_fee: Mapped[float] = mapped_column(Numeric(12, 2), default=0, server_default="0")

    # Additional details
    mileage_km: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Branch assignment
    branch_id: Mapped[str] = mapped_column(String, nullable=False)

    # Status
    status: Mapped[str] = mapped_column(String, nullable=False, default="AVAILABLE")

    # Images
    image_urls: Mapped[Optional[list[str]]] = mapped_column(JSONB, default=list, server_default="'[]'::jsonb")
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, server_default="NOW()")
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, server_default="NOW()", onupdate=datetime.utcnow)

    # Relationships
    # branch = relationship("Office", foreign_keys=[branch_id], backref="bicycles")
    # applications = relationship("BicycleApplication", back_populates="bicycle")

    __table_args__ = (
        CheckConstraint("condition IN ('NEW', 'USED')", name="check_bicycle_condition"),
        CheckConstraint("status IN ('AVAILABLE', 'RESERVED', 'SOLD', 'MAINTENANCE')", name="check_bicycle_status"),
        Index("idx_bicycles_branch", "branch_id"),
        Index("idx_bicycles_status", "status"),
        Index("idx_bicycles_condition", "condition"),
        Index("idx_bicycles_license_plate", "license_plate"),
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert bicycle to dictionary with all fields"""
        return {
            "id": self.id,
            "title": self.title,
            "brand": self.brand,
            "model": self.model,
            "year": self.year,
            "condition": self.condition,
            "license_plate": self.license_plate,
            "frame_number": self.frame_number,
            "engine_number": self.engine_number,
            "purchase_price": float(self.purchase_price) if self.purchase_price else 0,
            "cash_price": float(self.cash_price) if self.cash_price else 0,
            "hire_purchase_price": float(self.hire_purchase_price) if self.hire_purchase_price else 0,
            "duty_amount": float(self.duty_amount) if self.duty_amount else 0,
            "registration_fee": float(self.registration_fee) if self.registration_fee else 0,
            "mileage_km": self.mileage_km,
            "description": self.description,
            "branch_id": self.branch_id,
            "status": self.status,
            "image_urls": self.image_urls or [],
            "thumbnail_url": self.thumbnail_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_public_dict(self) -> dict[str, Any]:
        """Convert bicycle to public-facing dictionary (excludes internal fields)"""
        return {
            "id": self.id,
            "title": self.title,
            "brand": self.brand,
            "model": self.model,
            "year": self.year,
            "condition": self.condition,
            "license_plate": self.license_plate,
            "mileage_km": self.mileage_km,
            "description": self.description,
            "branch_id": self.branch_id,
            "cash_price": float(self.cash_price) if self.cash_price else 0,
            "hire_purchase_price": float(self.hire_purchase_price) if self.hire_purchase_price else 0,
            "image_urls": self.image_urls or [],
            "thumbnail_url": self.thumbnail_url,
            "monthly_payment_estimate": self.calculate_monthly_payment(),
        }

    def calculate_monthly_payment(self, tenure_months: int = 36, down_payment: float = 0) -> float:
        """
        Calculate estimated monthly payment for hire purchase

        Args:
            tenure_months: Loan tenure in months (default 36)
            down_payment: Down payment amount (default 0)

        Returns:
            Estimated monthly payment amount
        """
        if not self.hire_purchase_price:
            return 0

        financed_amount = float(self.hire_purchase_price) - down_payment
        if financed_amount <= 0:
            return 0

        # Simple calculation: financed amount / tenure
        # In production, you'd apply the actual interest rate from loan product
        return financed_amount / tenure_months
