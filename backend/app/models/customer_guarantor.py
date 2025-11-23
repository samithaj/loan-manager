from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Numeric, Text, ForeignKey, Boolean, Date
from sqlalchemy.dialects.postgresql import TIMESTAMP
from datetime import datetime, date
from typing import Optional, Any, TYPE_CHECKING
from ..db import Base

if TYPE_CHECKING:
    from .client import Client


class CustomerGuarantor(Base):
    """Guarantor information for loan applications"""
    __tablename__ = "customer_guarantors"

    id: Mapped[str] = mapped_column(String, primary_key=True)

    # Link to customer
    customer_id: Mapped[str] = mapped_column(
        String, ForeignKey("clients.id"), nullable=False, index=True
    )

    # Personal details
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    nic: Mapped[str] = mapped_column(String(20), nullable=False)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    mobile: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Address
    address_line1: Mapped[str] = mapped_column(String(200), nullable=False)
    address_line2: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    province: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # Relationship to customer
    relationship_to_customer: Mapped[str] = mapped_column(String(50), nullable=False)

    # Employment details
    employer_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    job_title: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    employment_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # PERMANENT, CONTRACT, SELF_EMPLOYED
    monthly_income: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    years_employed: Mapped[Optional[float]] = mapped_column(Numeric(4, 1), nullable=True)

    # Employment address
    employer_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    employer_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Verification
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    verified_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    verified_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Document references
    nic_document_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    salary_slip_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

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

    # Primary guarantor flag (first guarantor is usually primary)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    # Relationships
    customer: Mapped["Client"] = relationship("Client", backref="guarantors")

    def to_dict(self) -> dict[str, Any]:
        """Convert guarantor to dictionary"""
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "full_name": self.full_name,
            "nic": self.nic,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "mobile": self.mobile,
            "email": self.email,
            "address_line1": self.address_line1,
            "address_line2": self.address_line2,
            "city": self.city,
            "province": self.province,
            "postal_code": self.postal_code,
            "relationship_to_customer": self.relationship_to_customer,
            "employer_name": self.employer_name,
            "job_title": self.job_title,
            "employment_type": self.employment_type,
            "monthly_income": float(self.monthly_income) if self.monthly_income else None,
            "years_employed": float(self.years_employed) if self.years_employed else None,
            "employer_address": self.employer_address,
            "employer_phone": self.employer_phone,
            "is_verified": self.is_verified,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "verified_by": self.verified_by,
            "nic_document_url": self.nic_document_url,
            "salary_slip_url": self.salary_slip_url,
            "notes": self.notes,
            "is_primary": self.is_primary,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def verify(self, verified_by: str) -> None:
        """Mark guarantor as verified"""
        self.is_verified = True
        self.verified_at = datetime.utcnow()
        self.verified_by = verified_by
