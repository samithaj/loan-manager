from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Numeric, Text, Index, CheckConstraint, Boolean, Date, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional, Any, TYPE_CHECKING
from ..db import Base

if TYPE_CHECKING:
    from .company import Company
    from .stock_number import StockNumberAssignment
    from .bicycle_transfer import BicycleTransfer
    from .bicycle_expense import BicycleBranchExpense
    from .bicycle_sale import BicycleSale
    from .reference import Staff, Office
else:
    # Import bicycle_sale at runtime for foreign_keys reference
    from . import bicycle_sale


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
    IN_STOCK = "IN_STOCK"
    ALLOCATED = "ALLOCATED"
    IN_TRANSIT = "IN_TRANSIT"
    WRITTEN_OFF = "WRITTEN_OFF"


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

    # NEW FIELDS - Company and business model
    company_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("companies.id"), nullable=True
    )
    business_model: Mapped[str] = mapped_column(
        String, default="HIRE_PURCHASE", nullable=False, server_default="'HIRE_PURCHASE'"
    )
    current_stock_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    current_branch_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("offices.id"), nullable=True
    )

    # NEW FIELDS - Procurement details
    procurement_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    procurement_source: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    bought_method: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    hand_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    settlement_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    payment_branch_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("offices.id"), nullable=True
    )
    cr_location: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    buyer_employee_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("staff.id"), nullable=True
    )

    # NEW FIELDS - Control flags
    first_od: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    ldate: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    sk_flag: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    ls_flag: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    caller: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    house_use: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    # NEW FIELDS - Cost tracking
    total_branch_expenses: Mapped[float] = mapped_column(
        Numeric(12, 2), default=0, server_default="0"
    )
    # total_expenses is a GENERATED column in DB
    # base_purchase_price field (added by workshop module for cost tracking)
    base_purchase_price: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)
    total_repair_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)

    # NEW FIELDS - Sale tracking
    sold_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    selling_price: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    # profit_or_loss is a GENERATED column in DB

    # Relationships
    # branch = relationship("Office", foreign_keys=[branch_id], backref="bicycles")
    # applications = relationship("BicycleApplication", back_populates="bicycle")

    # NEW RELATIONSHIPS
    company: Mapped[Optional["Company"]] = relationship(
        "Company", back_populates="bicycles"
    )
    stock_assignments: Mapped[list["StockNumberAssignment"]] = relationship(
        "StockNumberAssignment", back_populates="bicycle", cascade="all, delete-orphan"
    )
    transfers: Mapped[list["BicycleTransfer"]] = relationship(
        "BicycleTransfer", back_populates="bicycle", cascade="all, delete-orphan"
    )
    branch_expenses: Mapped[list["BicycleBranchExpense"]] = relationship(
        "BicycleBranchExpense", back_populates="bicycle", cascade="all, delete-orphan"
    )
    sale: Mapped[Optional["BicycleSale"]] = relationship(
        "BicycleSale",
        back_populates="bicycle",
        foreign_keys="BicycleSale.bicycle_id",
        uselist=False
    )
    buyer_employee: Mapped[Optional["Staff"]] = relationship(
        "Staff", foreign_keys=[buyer_employee_id]
    )

    # NEW PROPERTIES
    @property
    def get_current_stock_number(self) -> Optional[str]:
        """Get the current active stock number"""
        if self.stock_assignments:
            for assignment in self.stock_assignments:
                if assignment.is_current:
                    return assignment.full_stock_number
        return None

    @property
    def get_total_branch_expenses(self) -> float:
        """Calculate total branch expenses"""
        if self.branch_expenses:
            return sum(float(exp.amount) for exp in self.branch_expenses)
        return 0.0

    @property
    def get_total_expenses(self) -> float:
        """Calculate total expenses (purchase + repair + branch)"""
        purchase = float(self.base_purchase_price) if self.base_purchase_price else 0.0
        repair = float(self.total_repair_cost) if self.total_repair_cost else 0.0
        branch = self.get_total_branch_expenses
        return purchase + repair + branch

    @property
    def get_profit_or_loss(self) -> Optional[float]:
        """Calculate profit or loss if sold"""
        if not self.selling_price:
            return None
        return float(self.selling_price) - self.get_total_expenses

    __table_args__ = (
        CheckConstraint("condition IN ('NEW', 'USED')", name="check_bicycle_condition"),
        CheckConstraint("status IN ('AVAILABLE', 'RESERVED', 'SOLD', 'MAINTENANCE', 'IN_STOCK', 'ALLOCATED', 'IN_TRANSIT', 'WRITTEN_OFF')", name="check_bicycle_status"),
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
            # New lifecycle fields
            "company_id": self.company_id,
            "business_model": self.business_model,
            "current_stock_number": self.current_stock_number or self.get_current_stock_number,
            "current_branch_id": self.current_branch_id,
            "procurement_date": self.procurement_date.isoformat() if self.procurement_date else None,
            "procurement_source": self.procurement_source,
            "bought_method": self.bought_method,
            "hand_amount": float(self.hand_amount) if self.hand_amount else None,
            "settlement_amount": float(self.settlement_amount) if self.settlement_amount else None,
            "payment_branch_id": self.payment_branch_id,
            "cr_location": self.cr_location,
            "buyer_employee_id": self.buyer_employee_id,
            "first_od": self.first_od,
            "ldate": self.ldate.isoformat() if self.ldate else None,
            "sk_flag": self.sk_flag,
            "ls_flag": self.ls_flag,
            "caller": self.caller,
            "house_use": self.house_use,
            "base_purchase_price": float(self.base_purchase_price) if self.base_purchase_price else None,
            "total_repair_cost": float(self.total_repair_cost) if self.total_repair_cost else None,
            "total_branch_expenses": float(self.total_branch_expenses) if self.total_branch_expenses else 0,
            "total_expenses": self.get_total_expenses,
            "sold_date": self.sold_date.isoformat() if self.sold_date else None,
            "selling_price": float(self.selling_price) if self.selling_price else None,
            "profit_or_loss": self.get_profit_or_loss,
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
