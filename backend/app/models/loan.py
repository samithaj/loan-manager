from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Numeric, Date, DateTime, text
from ..db import Base


class Loan(Base):
    __tablename__ = "loans"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    client_id: Mapped[str] = mapped_column(String, nullable=False)
    product_id: Mapped[str] = mapped_column(String, nullable=False)
    principal: Mapped[float] = mapped_column(Numeric, nullable=False)
    interest_rate: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    term_months: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    disbursed_on: Mapped[str | None] = mapped_column(Date, nullable=True)
    created_on: Mapped[str | None] = mapped_column(DateTime(timezone=True), server_default=text("now()"))


