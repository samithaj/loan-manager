from __future__ import annotations

from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: F401
from app.db import SessionLocal, engine, Base
from app.services.users import create_user
from loguru import logger


router = APIRouter(prefix="/v1")


class UserCreate(BaseModel):
    username: str
    password: str
    roles: list[str] | None = None


class UserOut(BaseModel):
    id: str
    username: str
    roles: list[str]


@router.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@router.post("/users", response_model=UserOut, status_code=201)
async def post_user(request: Request, payload: UserCreate):
    async with SessionLocal() as session:  # type: AsyncSession
        try:
            user = await create_user(session, payload.username, payload.password, payload.roles)
        except ValueError as e:
            if str(e) == "USERNAME_EXISTS":
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "USERNAME_EXISTS", "message": "Username already exists"})
            raise
        logger.bind(route="/users", method="POST", username=user.username, roles=user.roles, correlationId=getattr(request.state, "correlation_id", None)).info("created user")
        return UserOut(id=str(user.id), username=user.username, roles=user.roles)





