from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, text
from sqlalchemy.dialects.postgresql import UUID
import uuid
from ..db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String)
    roles_csv: Mapped[str] = mapped_column(String, default="user")

    @property
    def roles(self) -> list[str]:
        return [r for r in self.roles_csv.split(",") if r]




