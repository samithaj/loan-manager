from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Numeric
from ..db import Base


class LoanProduct(Base):
    __tablename__ = "loan_products"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    interest_rate: Mapped[float] = mapped_column(Numeric, nullable=False)
    term_months: Mapped[int] = mapped_column(Integer, nullable=False)
    repayment_frequency: Mapped[str] = mapped_column(String, nullable=False)


