from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Numeric, Text, ForeignKey, Boolean, Date
from sqlalchemy.dialects.postgresql import TIMESTAMP
from datetime import datetime, date
from typing import Optional, Any, TYPE_CHECKING
from enum import Enum
from ..db import Base

if TYPE_CHECKING:
    from .client import Client


class EmploymentType(str, Enum):
    """Employment type enumeration"""
    PERMANENT = "PERMANENT"
    CONTRACT = "CONTRACT"
    TEMPORARY = "TEMPORARY"
    SELF_EMPLOYED = "SELF_EMPLOYED"
    BUSINESS_OWNER = "BUSINESS_OWNER"
    RETIRED = "RETIRED"
    UNEMPLOYED = "UNEMPLOYED"


class IncomeFrequency(str, Enum):
    """Income frequency enumeration"""
    MONTHLY = "MONTHLY"
    WEEKLY = "WEEKLY"
    DAILY = "DAILY"
    ANNUAL = "ANNUAL"


class CustomerEmployment(Base):
    """Customer employment and income information"""
    __tablename__ = "customer_employment"

    id: Mapped[str] = mapped_column(String, primary_key=True)

    # Link to customer
    customer_id: Mapped[str] = mapped_column(
        String, ForeignKey("clients.id"), nullable=False, index=True
    )

    # Employment details
    employment_type: Mapped[str] = mapped_column(String(50), nullable=False)
    employer_name: Mapped[str] = mapped_column(String(200), nullable=False)
    job_title: Mapped[str] = mapped_column(String(100), nullable=False)
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Employment period
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    # Income details
    gross_income: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    income_frequency: Mapped[str] = mapped_column(
        String(20), nullable=False, default="MONTHLY", server_default="'MONTHLY'"
    )

    # Calculated monthly income (normalized)
    monthly_income: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    # Additional income sources
    other_income: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    other_income_source: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Employer contact
    employer_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    employer_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    employer_email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # HR contact
    hr_contact_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    hr_contact_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Verification
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    verified_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    verified_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    verification_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # PHONE_CALL, LETTER, EMAIL

    # Document references
    salary_slip_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    employment_letter_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    bank_statement_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

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

    # Relationships
    customer: Mapped["Client"] = relationship("Client", backref="employment_history")

    def to_dict(self) -> dict[str, Any]:
        """Convert employment to dictionary"""
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "employment_type": self.employment_type,
            "employer_name": self.employer_name,
            "job_title": self.job_title,
            "industry": self.industry,
            "department": self.department,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "is_current": self.is_current,
            "gross_income": float(self.gross_income) if self.gross_income else 0,
            "income_frequency": self.income_frequency,
            "monthly_income": float(self.monthly_income) if self.monthly_income else 0,
            "other_income": float(self.other_income) if self.other_income else None,
            "other_income_source": self.other_income_source,
            "employer_address": self.employer_address,
            "employer_phone": self.employer_phone,
            "employer_email": self.employer_email,
            "hr_contact_name": self.hr_contact_name,
            "hr_contact_phone": self.hr_contact_phone,
            "is_verified": self.is_verified,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "verified_by": self.verified_by,
            "verification_method": self.verification_method,
            "salary_slip_url": self.salary_slip_url,
            "employment_letter_url": self.employment_letter_url,
            "bank_statement_url": self.bank_statement_url,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "years_employed": self.calculate_years_employed(),
        }

    def calculate_years_employed(self) -> float:
        """Calculate years employed at current employer"""
        end = self.end_date if self.end_date else date.today()
        years = (end - self.start_date).days / 365.25
        return round(years, 1)

    def verify(self, verified_by: str, method: str) -> None:
        """Mark employment as verified"""
        self.is_verified = True
        self.verified_at = datetime.utcnow()
        self.verified_by = verified_by
        self.verification_method = method

    @staticmethod
    def normalize_to_monthly(amount: float, frequency: str) -> float:
        """Normalize income to monthly amount"""
        multipliers = {
            "DAILY": 30,
            "WEEKLY": 4.33,
            "MONTHLY": 1,
            "ANNUAL": 1 / 12,
        }
        return amount * multipliers.get(frequency, 1)
