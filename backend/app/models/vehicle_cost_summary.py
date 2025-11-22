from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, text, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from typing import TYPE_CHECKING, Optional
from datetime import datetime
import uuid
from ..db import Base

if TYPE_CHECKING:
    from .bicycle import Bicycle


class VehicleCostSummary(Base):
    """
    Cached summary of all costs for a vehicle
    Updated whenever a cost ledger entry is added/modified
    """
    __tablename__ = "vehicle_cost_summary"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # Vehicle reference
    vehicle_id: Mapped[str] = mapped_column(
        String, ForeignKey("bicycles.id"), unique=True, index=True
    )

    # Cost breakdown
    purchase_cost: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    transfer_cost: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    repair_cost: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    parts_cost: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    admin_cost: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    registration_cost: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    insurance_cost: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    transport_cost: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    other_cost: Mapped[float] = mapped_column(Numeric(12, 2), default=0)

    # Totals
    total_cost: Mapped[float] = mapped_column(Numeric(12, 2), default=0)

    # Sale information
    sale_price: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    profit: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    profit_margin_pct: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)

    # Entry counts (for auditing)
    total_entries: Mapped[int] = mapped_column(default=0)
    locked_entries: Mapped[int] = mapped_column(default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=datetime.utcnow
    )

    # Relationship
    vehicle: Mapped["Bicycle"] = relationship("Bicycle", foreign_keys=[vehicle_id])
