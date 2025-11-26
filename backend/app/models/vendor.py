"""Vendor/Supplier models for parts purchasing"""
from __future__ import annotations

from sqlalchemy import String, Boolean, Numeric, Date, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import date, datetime
from typing import Optional, Dict, Any
from decimal import Decimal

from ..db import Base


class Vendor(Base):
    """Vendors/Suppliers for parts and services"""
    __tablename__ = "vendors"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    company_id: Mapped[str] = mapped_column(String, ForeignKey("companies.id"), nullable=False)
    vendor_code: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)

    # Contact Information
    contact_person: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Address
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    province: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    country: Mapped[str] = mapped_column(String, nullable=False, server_default="Sri Lanka")

    # Business Details
    tax_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    business_registration_no: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Payment Terms
    payment_terms: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    credit_limit: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, server_default="0")
    currency: Mapped[str] = mapped_column(String, nullable=False, server_default="LKR")

    # Banking
    bank_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    bank_account_no: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    bank_branch: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    # Performance Metrics (computed/cached)
    total_purchases: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, server_default="0")
    total_orders: Mapped[int] = mapped_column(nullable=False, server_default="0")
    last_purchase_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Category
    category_id: Mapped[Optional[str]] = mapped_column(
        String,
        ForeignKey("vendor_categories.id"),
        nullable=True
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Audit
    created_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default="NOW()")
    updated_at: Mapped[datetime] = mapped_column(nullable=False, server_default="NOW()")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "company_id": self.company_id,
            "vendor_code": self.vendor_code,
            "name": self.name,
            "contact_person": self.contact_person,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
            "city": self.city,
            "province": self.province,
            "postal_code": self.postal_code,
            "country": self.country,
            "tax_id": self.tax_id,
            "business_registration_no": self.business_registration_no,
            "payment_terms": self.payment_terms,
            "credit_limit": float(self.credit_limit) if self.credit_limit else 0.0,
            "currency": self.currency,
            "bank_name": self.bank_name,
            "bank_account_no": self.bank_account_no,
            "bank_branch": self.bank_branch,
            "is_active": self.is_active,
            "total_purchases": float(self.total_purchases) if self.total_purchases else 0.0,
            "total_orders": self.total_orders,
            "last_purchase_date": self.last_purchase_date.isoformat() if self.last_purchase_date else None,
            "category_id": self.category_id,
            "notes": self.notes,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class VendorCategory(Base):
    """Categories for organizing vendors"""
    __tablename__ = "vendor_categories"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default="NOW()")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class VendorContact(Base):
    """Contact persons at vendor companies"""
    __tablename__ = "vendor_contacts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    vendor_id: Mapped[str] = mapped_column(String, ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False)

    name: Mapped[str] = mapped_column(String, nullable=False)
    position: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    mobile: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default="NOW()")
    updated_at: Mapped[datetime] = mapped_column(nullable=False, server_default="NOW()")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "vendor_id": self.vendor_id,
            "name": self.name,
            "position": self.position,
            "phone": self.phone,
            "mobile": self.mobile,
            "email": self.email,
            "is_primary": self.is_primary,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
