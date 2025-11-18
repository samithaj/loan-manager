from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Date, ForeignKey, Text, Numeric, Integer
from sqlalchemy.dialects.postgresql import TIMESTAMP
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional, Any, TYPE_CHECKING
from ..db import Base

if TYPE_CHECKING:
    from .bicycle import Bicycle
    from .company import Company
    from .reference import Office
    from .hr_bonus import BonusPayment


class SalePaymentMethod(str, Enum):
    CASH = "CASH"
    FINANCE = "FINANCE"
    TRADE_IN = "TRADE_IN"
    BANK_TRANSFER = "BANK_TRANSFER"
    MIXED = "MIXED"


class BicycleSale(Base):
    __tablename__ = "bicycle_sales"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    bicycle_id: Mapped[str] = mapped_column(
        String, ForeignKey("bicycles.id", ondelete="RESTRICT"), nullable=False, unique=True
    )
    selling_branch_id: Mapped[str] = mapped_column(
        String, ForeignKey("offices.id"), nullable=False
    )
    selling_company_id: Mapped[str] = mapped_column(
        String, ForeignKey("companies.id"), nullable=False
    )
    stock_number_at_sale: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    sale_date: Mapped[date] = mapped_column(Date, nullable=False)
    selling_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    payment_method: Mapped[str] = mapped_column(String, nullable=False)

    # Customer details
    customer_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    customer_phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    customer_email: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    customer_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    customer_nic: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Trade-in details
    trade_in_bicycle_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("bicycles.id"), nullable=True
    )
    trade_in_value: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)

    # Finance details
    finance_institution: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    down_payment: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    financed_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)

    # Sale details
    sold_by: Mapped[str] = mapped_column(String, nullable=False)
    sale_invoice_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    delivery_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    warranty_months: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Computed fields (updated via trigger or app logic)
    total_cost: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    profit_or_loss: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, server_default="NOW()"
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, server_default="NOW()", onupdate=datetime.utcnow
    )

    # Relationships
    bicycle: Mapped["Bicycle"] = relationship(
        "Bicycle", back_populates="sale", foreign_keys=[bicycle_id]
    )
    selling_branch: Mapped["Office"] = relationship("Office", foreign_keys=[selling_branch_id])
    selling_company: Mapped["Company"] = relationship("Company")
    trade_in_bicycle: Mapped[Optional["Bicycle"]] = relationship(
        "Bicycle", foreign_keys=[trade_in_bicycle_id]
    )
    commissions: Mapped[list["BonusPayment"]] = relationship(
        "BonusPayment", back_populates="bicycle_sale"
    )

    def calculate_profit(self) -> float:
        """Calculate profit or loss for this sale"""
        if not self.total_cost or not self.selling_price:
            return 0
        return float(self.selling_price) - float(self.total_cost)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "bicycle_id": self.bicycle_id,
            "selling_branch_id": self.selling_branch_id,
            "selling_company_id": self.selling_company_id,
            "stock_number_at_sale": self.stock_number_at_sale,
            "sale_date": self.sale_date.isoformat() if self.sale_date else None,
            "selling_price": float(self.selling_price) if self.selling_price else 0,
            "payment_method": self.payment_method,
            "customer_name": self.customer_name,
            "customer_phone": self.customer_phone,
            "customer_email": self.customer_email,
            "customer_address": self.customer_address,
            "customer_nic": self.customer_nic,
            "trade_in_bicycle_id": self.trade_in_bicycle_id,
            "trade_in_value": float(self.trade_in_value) if self.trade_in_value else None,
            "finance_institution": self.finance_institution,
            "down_payment": float(self.down_payment) if self.down_payment else None,
            "financed_amount": float(self.financed_amount) if self.financed_amount else None,
            "sold_by": self.sold_by,
            "sale_invoice_number": self.sale_invoice_number,
            "delivery_date": self.delivery_date.isoformat() if self.delivery_date else None,
            "warranty_months": self.warranty_months,
            "total_cost": float(self.total_cost) if self.total_cost else None,
            "profit_or_loss": float(self.profit_or_loss) if self.profit_or_loss else None,
            "notes": self.notes,
        }
