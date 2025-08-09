from __future__ import annotations

import uuid
import hashlib
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.user import User


def _hash_password(password: str) -> str:
    # Simple SHA256 for demo; replace with bcrypt/argon2 in production
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


async def create_user(session: AsyncSession, username: str, password: str, roles: list[str] | None = None) -> User:
    # Preflight check to return a clean 409 for existing username
    existing = await session.execute(select(User).where(User.username == username))
    if existing.scalar_one_or_none() is not None:
        raise ValueError("USERNAME_EXISTS")

    roles_csv = ",".join(roles or ["user"])
    user = User(id=uuid.uuid4(), username=username, password_hash=_hash_password(password), roles_csv=roles_csv)
    session.add(user)
    try:
        await session.commit()
    except IntegrityError as exc:
        # Some other integrity issue (e.g., DB constraints). Surface as generic error.
        await session.rollback()
        raise
    await session.refresh(user)
    return user


async def verify_credentials(session: AsyncSession, username: str, password: str) -> User | None:
    result = await session.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user:
        return None
    if user.password_hash != _hash_password(password):
        return None
    return user


