from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Numeric, Integer, Date, DateTime, ForeignKey
from datetime import datetime, date
from ..db import Base


class Loan(Base):
    __tablename__ = "loans"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    client_id: Mapped[str] = mapped_column(String, ForeignKey("clients.id"), nullable=False)
    product_id: Mapped[str] = mapped_column(String, ForeignKey("loan_products.id"), nullable=False)
    principal: Mapped[float] = mapped_column(Numeric, nullable=False)
    interest_rate: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    term_months: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)  # PENDING, APPROVED, DISBURSED, CLOSED
    disbursed_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_on: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    client = relationship("Client")
    product = relationship("LoanProduct")


class LoanTransaction(Base):
    __tablename__ = "loan_transactions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    loan_id: Mapped[str] = mapped_column(String, ForeignKey("loans.id"), nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)  # DISBURSEMENT, REPAYMENT, PREPAYMENT, etc.
    amount: Mapped[float] = mapped_column(Numeric, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    receipt_number: Mapped[str] = mapped_column(String, nullable=False)
    posted_by: Mapped[str | None] = mapped_column(String, nullable=True)

    # Relationship
    loan = relationship("Loan")


class LoanCharge(Base):
    __tablename__ = "loan_charges"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    loan_id: Mapped[str] = mapped_column(String, ForeignKey("loans.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)  # PENDING, PAID, WAIVED

    # Relationship
    loan = relationship("Loan")


class Collateral(Base):
    __tablename__ = "collaterals"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    loan_id: Mapped[str | None] = mapped_column(String, ForeignKey("loans.id"), nullable=True)
    type: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[float] = mapped_column(Numeric, nullable=False)
    details: Mapped[dict | None] = mapped_column(String, nullable=True)  # JSON stored as text

    # Relationship
    loan = relationship("Loan")


class VehicleInventory(Base):
    __tablename__ = "vehicle_inventory"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    vin_or_frame_number: Mapped[str | None] = mapped_column(String, nullable=True)
    brand: Mapped[str] = mapped_column(String, nullable=False)
    model: Mapped[str] = mapped_column(String, nullable=False)
    plate: Mapped[str | None] = mapped_column(String, nullable=True)
    color: Mapped[str | None] = mapped_column(String, nullable=True)
    purchase_price: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    msrp: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)  # IN_STOCK, SOLD, ALLOCATED
    linked_loan_id: Mapped[str | None] = mapped_column(String, ForeignKey("loans.id"), nullable=True)

    # Relationship
    linked_loan = relationship("Loan")


class DelinquencyBucket(Base):
    __tablename__ = "delinquency_buckets"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    min_days: Mapped[int] = mapped_column(Integer, nullable=False)
    max_days: Mapped[int] = mapped_column(Integer, nullable=False)


class DelinquencyStatus(Base):
    __tablename__ = "delinquency_status"

    loan_id: Mapped[str] = mapped_column(String, ForeignKey("loans.id"), primary_key=True)
    current_bucket_id: Mapped[str] = mapped_column(String, ForeignKey("delinquency_buckets.id"), nullable=False)
    days_past_due: Mapped[int] = mapped_column(Integer, nullable=False)
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Relationships
    loan = relationship("Loan")
    bucket = relationship("DelinquencyBucket")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    owner_type: Mapped[str] = mapped_column(String, nullable=False)  # CLIENT, LOAN
    owner_id: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    mime_type: Mapped[str] = mapped_column(String, nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    uploaded_on: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)