from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from typing import TYPE_CHECKING, Optional, Any
from datetime import datetime
import uuid
from ..db import Base

if TYPE_CHECKING:
    from .loan_application import LoanApplication
    from .user import User
    from .loan_application import ApplicationStatus


class LoanApplicationAudit(Base):
    __tablename__ = "loan_application_audits"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # Foreign keys
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("loan_applications.id"), index=True
    )
    actor_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    # Audit details
    action: Mapped[str] = mapped_column(String(100), index=True)
    from_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    to_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Additional payload (e.g., changed fields, decision details, etc.)
    payload_json: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, nullable=True, default=dict, server_default="'{}'::jsonb"
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), index=True
    )

    # Relationships
    application: Mapped["LoanApplication"] = relationship(
        "LoanApplication", back_populates="audit_logs"
    )
    actor: Mapped[Optional["User"]] = relationship("User", foreign_keys=[actor_user_id])
