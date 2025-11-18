from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Date, Boolean, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional, Any, TYPE_CHECKING
from ..db import Base

if TYPE_CHECKING:
    from .company import Company


class Office(Base):
    __tablename__ = "offices"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)

    # Bicycle-specific fields
    allows_bicycle_sales: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    bicycle_display_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    map_coordinates: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    operating_hours: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    public_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Company relationship fields
    company_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("companies.id"), nullable=True)
    is_repair_center: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default="false")

    # Relationships
    company: Mapped[Optional["Company"]] = relationship("Company", back_populates="offices")

    def to_public_dict(self) -> dict[str, Any]:
        """Convert office to public-facing dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "allows_bicycle_sales": self.allows_bicycle_sales,
            "bicycle_display_order": self.bicycle_display_order,
            "map_coordinates": self.map_coordinates,
            "operating_hours": self.operating_hours,
            "public_description": self.public_description,
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert office to dictionary with all fields"""
        return {
            "id": self.id,
            "name": self.name,
            "company_id": self.company_id,
            "is_repair_center": self.is_repair_center,
            "allows_bicycle_sales": self.allows_bicycle_sales,
            "bicycle_display_order": self.bicycle_display_order,
            "map_coordinates": self.map_coordinates,
            "operating_hours": self.operating_hours,
            "public_description": self.public_description,
        }


class Staff(Base):
    __tablename__ = "staff"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)


class Holiday(Base):
    __tablename__ = "holidays"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[str] = mapped_column(Date, nullable=False)



