from __future__ import annotations

from sqlalchemy import String, Boolean, Numeric, Date, Text, ARRAY, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from datetime import date, datetime
from enum import Enum
from typing import Optional, Dict, Any
import json

from ..db import Base


class PartCategory(str, Enum):
    ENGINE = "ENGINE"
    BRAKE = "BRAKE"
    TYRE = "TYRE"
    ELECTRICAL = "ELECTRICAL"
    SUSPENSION = "SUSPENSION"
    TRANSMISSION = "TRANSMISSION"
    EXHAUST = "EXHAUST"
    BODY = "BODY"
    ACCESSORIES = "ACCESSORIES"
    FLUIDS = "FLUIDS"
    CONSUMABLES = "CONSUMABLES"
    OTHER = "OTHER"


class StockMovementType(str, Enum):
    PURCHASE = "PURCHASE"
    ADJUSTMENT = "ADJUSTMENT"
    TRANSFER_IN = "TRANSFER_IN"
    TRANSFER_OUT = "TRANSFER_OUT"
    REPAIR_USAGE = "REPAIR_USAGE"
    RETURN = "RETURN"
    WRITE_OFF = "WRITE_OFF"


class Part(Base):
    """Spare parts master data"""
    __tablename__ = "parts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    part_code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String, nullable=False)
    brand: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    unit: Mapped[str] = mapped_column(String, nullable=False, server_default="pcs")
    is_universal: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    bike_model_compatibility: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )
    minimum_stock_level: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, server_default="0")
    reorder_point: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default="NOW()")
    updated_at: Mapped[datetime] = mapped_column(nullable=False, server_default="NOW()")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "part_code": self.part_code,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "brand": self.brand,
            "unit": self.unit,
            "is_universal": self.is_universal,
            "bike_model_compatibility": self.bike_model_compatibility,
            "minimum_stock_level": float(self.minimum_stock_level) if self.minimum_stock_level else 0,
            "reorder_point": float(self.reorder_point) if self.reorder_point else 0,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class PartStockBatch(Base):
    """Stock batches with individual purchase prices (FIFO costing)"""
    __tablename__ = "part_stock_batches"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    part_id: Mapped[str] = mapped_column(String, nullable=False)
    supplier_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    branch_id: Mapped[str] = mapped_column(String, nullable=False)
    purchase_date: Mapped[date] = mapped_column(Date, nullable=False)
    purchase_price_per_unit: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    quantity_received: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    quantity_available: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    invoice_no: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    grn_no: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default="NOW()")
    updated_at: Mapped[datetime] = mapped_column(nullable=False, server_default="NOW()")

    __table_args__ = (
        CheckConstraint("quantity_received >= 0 AND quantity_available >= 0", name="positive_quantities"),
        CheckConstraint("quantity_available <= quantity_received", name="available_lte_received"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "part_id": self.part_id,
            "supplier_id": self.supplier_id,
            "branch_id": self.branch_id,
            "purchase_date": self.purchase_date.isoformat(),
            "purchase_price_per_unit": float(self.purchase_price_per_unit),
            "quantity_received": float(self.quantity_received),
            "quantity_available": float(self.quantity_available),
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "invoice_no": self.invoice_no,
            "grn_no": self.grn_no,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    def is_expired(self) -> bool:
        """Check if this batch has expired"""
        if not self.expiry_date:
            return False
        return date.today() > self.expiry_date

    def is_available(self) -> bool:
        """Check if this batch has available stock"""
        return float(self.quantity_available) > 0 and not self.is_expired()


class PartStockMovement(Base):
    """Audit log of all stock movements"""
    __tablename__ = "part_stock_movements"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    part_id: Mapped[str] = mapped_column(String, nullable=False)
    batch_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    branch_id: Mapped[str] = mapped_column(String, nullable=False)
    movement_type: Mapped[str] = mapped_column(String, nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    unit_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)
    total_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)
    related_doc_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    related_doc_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default="NOW()")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "part_id": self.part_id,
            "batch_id": self.batch_id,
            "branch_id": self.branch_id,
            "movement_type": self.movement_type,
            "quantity": float(self.quantity),
            "unit_cost": float(self.unit_cost) if self.unit_cost else None,
            "total_cost": float(self.total_cost) if self.total_cost else None,
            "related_doc_type": self.related_doc_type,
            "related_doc_id": self.related_doc_id,
            "notes": self.notes,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat()
        }
