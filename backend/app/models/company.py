from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from datetime import datetime
from typing import Optional, Any, TYPE_CHECKING
from ..db import Base

if TYPE_CHECKING:
    from .reference import Office
    from .bicycle import Bicycle


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    district: Mapped[str] = mapped_column(String, nullable=False)
    contact_person: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    address: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    tax_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, server_default="NOW()"
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, server_default="NOW()", onupdate=datetime.utcnow
    )

    # Relationships
    offices: Mapped[list["Office"]] = relationship("Office", back_populates="company")
    bicycles: Mapped[list["Bicycle"]] = relationship("Bicycle", back_populates="company")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "district": self.district,
            "contact_person": self.contact_person,
            "contact_phone": self.contact_phone,
            "contact_email": self.contact_email,
            "address": self.address,
            "tax_id": self.tax_id,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
