from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime
from ..db import Base


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    mobile: Mapped[str | None] = mapped_column(String, nullable=True)
    national_id: Mapped[str | None] = mapped_column(String, nullable=True)
    address: Mapped[str | None] = mapped_column(String, nullable=True)
    # created_on exists in DB; not required for responses now
    # created_on: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


