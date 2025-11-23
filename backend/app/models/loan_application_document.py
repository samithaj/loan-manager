from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, text, DateTime, ForeignKey, Enum as SQLEnum, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from typing import TYPE_CHECKING, Optional, Any
from datetime import datetime
from enum import Enum
import uuid
from ..db import Base

if TYPE_CHECKING:
    from .loan_application import LoanApplication
    from .user import User


class DocumentType(str, Enum):
    """Types of documents that can be uploaded"""
    # Customer documents
    NIC_FRONT = "NIC_FRONT"
    NIC_BACK = "NIC_BACK"
    CUSTOMER_PHOTO = "CUSTOMER_PHOTO"
    CUSTOMER_SELFIE = "CUSTOMER_SELFIE"
    PROOF_OF_ADDRESS = "PROOF_OF_ADDRESS"

    # Vehicle documents
    CERTIFICATE_OF_REGISTRATION = "CERTIFICATE_OF_REGISTRATION"
    VEHICLE_PHOTO_FRONT = "VEHICLE_PHOTO_FRONT"
    VEHICLE_PHOTO_BACK = "VEHICLE_PHOTO_BACK"
    VEHICLE_PHOTO_SIDE = "VEHICLE_PHOTO_SIDE"
    VEHICLE_PHOTO_DASHBOARD = "VEHICLE_PHOTO_DASHBOARD"
    VEHICLE_PHOTO_ENGINE = "VEHICLE_PHOTO_ENGINE"

    # Other documents
    BANK_STATEMENT = "BANK_STATEMENT"
    SALARY_SLIP = "SALARY_SLIP"
    OTHER = "OTHER"


class LoanApplicationDocument(Base):
    __tablename__ = "loan_application_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # Foreign keys
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("loan_applications.id"), index=True
    )
    uploaded_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Document details
    doc_type: Mapped[DocumentType] = mapped_column(
        SQLEnum(DocumentType, name="loan_document_type"), index=True
    )
    file_url: Mapped[str] = mapped_column(String(1000))
    file_name: Mapped[str] = mapped_column(String(255))
    file_size: Mapped[int] = mapped_column(Integer)  # Size in bytes
    file_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # SHA-256 hash
    mime_type: Mapped[str] = mapped_column(String(100))

    # Metadata (e.g., image dimensions, OCR status, etc.)
    meta_json: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, nullable=True, default=dict, server_default="'{}'::jsonb"
    )

    # Timestamps
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )

    # Relationships
    application: Mapped["LoanApplication"] = relationship(
        "LoanApplication", back_populates="documents"
    )
    uploader: Mapped["User"] = relationship("User", foreign_keys=[uploaded_by])
