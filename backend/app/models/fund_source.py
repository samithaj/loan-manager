from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional
import uuid
from ..db import Base


class FundSource(Base):
    """
    Fund sources for vehicle cost transactions
    Tracks different sources of money: Petty Cash, Bank, Head Office, Supplier Credit, etc.
    """
    __tablename__ = "fund_sources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    code: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Metadata
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    approval_threshold: Mapped[Optional[float]] = mapped_column(String, nullable=True)  # Amount threshold
