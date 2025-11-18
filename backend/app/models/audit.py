from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, JSON, text
from ..db import Base


class LoanAudit(Base):
    __tablename__ = "loan_audit"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    loan_id: Mapped[str] = mapped_column(String, nullable=False)
    actor: Mapped[str] = mapped_column(String, nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False)
    at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    correlation_id: Mapped[str | None] = mapped_column(String, nullable=True)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)



