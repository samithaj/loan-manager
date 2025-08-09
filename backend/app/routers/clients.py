from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import SessionLocal
from ..models.client import Client


router = APIRouter(prefix="/v1")


class ClientOut(BaseModel):
    id: str
    displayName: str
    mobile: str | None = None
    nationalId: str | None = None
    address: str | None = None


class ClientIn(BaseModel):
    id: str
    displayName: str
    mobile: str | None = None
    nationalId: str | None = None
    address: str | None = None


@router.get("/clients", response_model=list[ClientOut])
async def list_clients(q: str | None = Query(default=None, description="Search by name/mobile/nationalId")):
    async with SessionLocal() as session:  # type: AsyncSession
        stmt = select(Client).order_by(Client.display_name)
        if q:
            like = f"%{q}%"
            stmt = stmt.where(
                (Client.display_name.ilike(like))
                | (Client.mobile.ilike(like))
                | (Client.national_id.ilike(like))
            )
        rows = (await session.execute(stmt)).scalars().all()
        return [
            ClientOut(
                id=c.id,
                displayName=c.display_name,
                mobile=c.mobile,
                nationalId=c.national_id,
                address=c.address,
            )
            for c in rows
        ]


@router.post("/clients", response_model=ClientOut, status_code=201)
async def create_client(payload: ClientIn):
    async with SessionLocal() as session:  # type: AsyncSession
        exists = await session.get(Client, payload.id)
        if exists:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "CLIENT_EXISTS"})
        c = Client(
            id=payload.id,
            display_name=payload.displayName,
            mobile=payload.mobile,
            national_id=payload.nationalId,
            address=payload.address,
        )
        session.add(c)
        await session.commit()
        await session.refresh(c)
        return ClientOut(
            id=c.id,
            displayName=c.display_name,
            mobile=c.mobile,
            nationalId=c.national_id,
            address=c.address,
        )


@router.get("/clients/{clientId}", response_model=ClientOut)
async def get_client(clientId: str):
    async with SessionLocal() as session:  # type: AsyncSession
        c = await session.get(Client, clientId)
        if not c:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND"})
        return ClientOut(
            id=c.id,
            displayName=c.display_name,
            mobile=c.mobile,
            nationalId=c.national_id,
            address=c.address,
        )


@router.put("/clients/{clientId}", response_model=ClientOut)
async def update_client(clientId: str, payload: ClientIn):
    async with SessionLocal() as session:  # type: AsyncSession
        c = await session.get(Client, clientId)
        if not c:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND"})
        c.display_name = payload.displayName
        c.mobile = payload.mobile
        c.national_id = payload.nationalId
        c.address = payload.address
        await session.commit()
        await session.refresh(c)
        return ClientOut(
            id=c.id,
            displayName=c.display_name,
            mobile=c.mobile,
            nationalId=c.national_id,
            address=c.address,
        )


@router.delete("/clients/{clientId}", status_code=204)
async def delete_client(clientId: str):
    async with SessionLocal() as session:  # type: AsyncSession
        c = await session.get(Client, clientId)
        if not c:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND"})
        await session.delete(c)
        await session.commit()
        return None


