from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, text, Date, Integer, UniqueConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import date
import uuid
from ..db import Base


class BillNumberSequence(Base):
    """
    Tracks bill number sequences per branch + fund source + date
    Used to generate unique bill numbers like: BD-PC-20251122-0041
    """
    __tablename__ = "bill_number_sequences"
    __table_args__ = (
        UniqueConstraint("branch_id", "fund_source_id", "sequence_date", name="uq_bill_sequence"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    branch_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("branches.id"))
    fund_source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fund_sources.id"))
    sequence_date: Mapped[date] = mapped_column(Date)

    # Current sequence number for this combination
    current_sequence: Mapped[int] = mapped_column(Integer, default=0)

    # Last updated (for tracking)
    last_generated_at: Mapped[date] = mapped_column(
        Date, server_default=text("CURRENT_DATE")
    )
