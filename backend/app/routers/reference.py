from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import SessionLocal
from datetime import date as DateType
from ..models.reference import Office, Staff, Holiday


router = APIRouter(prefix="/v1")


class OfficeOut(BaseModel):
    id: str
    name: str
    allows_bicycle_sales: bool = True
    bicycle_display_order: int = 0
    map_coordinates: dict | None = None
    operating_hours: str | None = None
    public_description: str | None = None


class StaffOut(BaseModel):
    id: str
    name: str
    role: str


class HolidayOut(BaseModel):
    id: str
    name: str
    date: str


class OfficeIn(BaseModel):
    id: str
    name: str
    allows_bicycle_sales: bool = True
    bicycle_display_order: int = 0
    map_coordinates: dict | None = None
    operating_hours: str | None = None
    public_description: str | None = None


class StaffIn(BaseModel):
    id: str
    name: str
    role: str


class HolidayIn(BaseModel):
    id: str
    name: str
    date: str  # ISO date


@router.get("/offices", response_model=list[OfficeOut])
async def get_offices():
    async with SessionLocal() as session:  # type: AsyncSession
        result = await session.execute(select(Office).order_by(Office.id))
        rows = result.scalars().all()
        return [OfficeOut(
            id=o.id,
            name=o.name,
            allows_bicycle_sales=o.allows_bicycle_sales,
            bicycle_display_order=o.bicycle_display_order,
            map_coordinates=o.map_coordinates,
            operating_hours=o.operating_hours,
            public_description=o.public_description
        ) for o in rows]


@router.post("/offices", response_model=OfficeOut, status_code=201)
async def create_office(payload: OfficeIn):
    async with SessionLocal() as session:  # type: AsyncSession
        exists = await session.get(Office, payload.id)
        if exists:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "OFFICE_EXISTS"})
        office = Office(
            id=payload.id,
            name=payload.name,
            allows_bicycle_sales=payload.allows_bicycle_sales,
            bicycle_display_order=payload.bicycle_display_order,
            map_coordinates=payload.map_coordinates,
            operating_hours=payload.operating_hours,
            public_description=payload.public_description
        )
        session.add(office)
        await session.commit()
        await session.refresh(office)
        return OfficeOut(
            id=office.id,
            name=office.name,
            allows_bicycle_sales=office.allows_bicycle_sales,
            bicycle_display_order=office.bicycle_display_order,
            map_coordinates=office.map_coordinates,
            operating_hours=office.operating_hours,
            public_description=office.public_description
        )


@router.put("/offices/{officeId}", response_model=OfficeOut)
async def update_office(officeId: str, payload: OfficeIn):
    async with SessionLocal() as session:  # type: AsyncSession
        office = await session.get(Office, officeId)
        if not office:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND"})
        office.name = payload.name
        office.allows_bicycle_sales = payload.allows_bicycle_sales
        office.bicycle_display_order = payload.bicycle_display_order
        office.map_coordinates = payload.map_coordinates
        office.operating_hours = payload.operating_hours
        office.public_description = payload.public_description
        await session.commit()
        await session.refresh(office)
        return OfficeOut(
            id=office.id,
            name=office.name,
            allows_bicycle_sales=office.allows_bicycle_sales,
            bicycle_display_order=office.bicycle_display_order,
            map_coordinates=office.map_coordinates,
            operating_hours=office.operating_hours,
            public_description=office.public_description
        )


@router.delete("/offices/{officeId}", status_code=204)
async def delete_office(officeId: str):
    async with SessionLocal() as session:  # type: AsyncSession
        office = await session.get(Office, officeId)
        if not office:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND"})
        await session.delete(office)
        await session.commit()
        return None


@router.get("/staff", response_model=list[StaffOut])
async def get_staff():
    async with SessionLocal() as session:  # type: AsyncSession
        result = await session.execute(select(Staff).order_by(Staff.id))
        rows = result.scalars().all()
        return [StaffOut(id=s.id, name=s.name, role=s.role) for s in rows]


@router.post("/staff", response_model=StaffOut, status_code=201)
async def create_staff(payload: StaffIn):
    async with SessionLocal() as session:  # type: AsyncSession
        exists = await session.get(Staff, payload.id)
        if exists:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "STAFF_EXISTS"})
        staff = Staff(id=payload.id, name=payload.name, role=payload.role)
        session.add(staff)
        await session.commit()
        await session.refresh(staff)
        return StaffOut(id=staff.id, name=staff.name, role=staff.role)


@router.put("/staff/{staffId}", response_model=StaffOut)
async def update_staff(staffId: str, payload: StaffIn):
    async with SessionLocal() as session:  # type: AsyncSession
        staff = await session.get(Staff, staffId)
        if not staff:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND"})
        staff.name = payload.name
        staff.role = payload.role
        await session.commit()
        await session.refresh(staff)
        return StaffOut(id=staff.id, name=staff.name, role=staff.role)


@router.delete("/staff/{staffId}", status_code=204)
async def delete_staff(staffId: str):
    async with SessionLocal() as session:  # type: AsyncSession
        staff = await session.get(Staff, staffId)
        if not staff:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND"})
        await session.delete(staff)
        await session.commit()
        return None


@router.get("/holidays", response_model=list[HolidayOut])
async def get_holidays():
    async with SessionLocal() as session:  # type: AsyncSession
        result = await session.execute(select(Holiday).order_by(Holiday.date))
        rows = result.scalars().all()
        return [HolidayOut(id=h.id, name=h.name, date=h.date.isoformat()) for h in rows]


@router.post("/holidays", response_model=HolidayOut, status_code=201)
async def create_holiday(payload: HolidayIn):
    async with SessionLocal() as session:  # type: AsyncSession
        exists = await session.get(Holiday, payload.id)
        if exists:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "HOLIDAY_EXISTS"})
        try:
            date_obj: DateType = DateType.fromisoformat(payload.date)
        except Exception:
            raise HTTPException(status_code=400, detail={"code": "INVALID_DATE", "message": "Use YYYY-MM-DD"})
        holiday = Holiday(id=payload.id, name=payload.name, date=date_obj)
        session.add(holiday)
        await session.commit()
        await session.refresh(holiday)
        return HolidayOut(id=holiday.id, name=holiday.name, date=holiday.date.isoformat())


@router.put("/holidays/{holidayId}", response_model=HolidayOut)
async def update_holiday(holidayId: str, payload: HolidayIn):
    async with SessionLocal() as session:  # type: AsyncSession
        holiday = await session.get(Holiday, holidayId)
        if not holiday:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND"})
        holiday.name = payload.name
        try:
            holiday.date = DateType.fromisoformat(payload.date)
        except Exception:
            raise HTTPException(status_code=400, detail={"code": "INVALID_DATE", "message": "Use YYYY-MM-DD"})
        await session.commit()
        await session.refresh(holiday)
        return HolidayOut(id=holiday.id, name=holiday.name, date=holiday.date.isoformat())


@router.delete("/holidays/{holidayId}", status_code=204)
async def delete_holiday(holidayId: str):
    async with SessionLocal() as session:  # type: AsyncSession
        holiday = await session.get(Holiday, holidayId)
        if not holiday:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND"})
        await session.delete(holiday)
        await session.commit()
        return None


