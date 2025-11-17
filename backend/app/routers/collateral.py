from __future__ import annotations

import time
import json
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import SessionLocal
from app.models.loan import Loan, Collateral, VehicleInventory
from loguru import logger


router = APIRouter(prefix="/v1")


# Pydantic models
class CollateralIn(BaseModel):
    id: str | None = None
    type: str  # VEHICLE, LAND
    value: float
    details: dict | None = None


class CollateralOut(BaseModel):
    id: str
    type: str
    value: float
    details: dict | None = None


class VehicleInventoryIn(BaseModel):
    id: str | None = None
    vinOrFrameNumber: str | None = None
    brand: str
    model: str
    plate: str | None = None
    color: str | None = None
    purchasePrice: float | None = None
    msrp: float | None = None
    status: str = "IN_STOCK"


class VehicleInventoryOut(BaseModel):
    id: str
    vinOrFrameNumber: str | None
    brand: str
    model: str
    plate: str | None
    color: str | None
    purchasePrice: float | None
    msrp: float | None
    status: str
    linkedLoanId: str | None


class PagedVehicleInventory(BaseModel):
    items: list[VehicleInventoryOut]
    page: int
    pageSize: int
    total: int


class AllocateVehicleRequest(BaseModel):
    loanId: str


def generate_collateral_id() -> str:
    return f"COL-{int(time.time() * 1000)}"


def generate_vehicle_id() -> str:
    return f"VEH-{int(time.time() * 1000)}"


# Collateral endpoints
@router.get("/loans/{loanId}/collaterals", response_model=list[CollateralOut])
async def list_collateral(request: Request, loanId: str):
    async with SessionLocal() as session:
        # Verify loan exists
        loan = await session.get(Loan, loanId)
        if not loan:
            raise HTTPException(status_code=404, detail={"code": "LOAN_NOT_FOUND"})

        query = select(Collateral).where(Collateral.loan_id == loanId).order_by(Collateral.id)
        rows = (await session.execute(query)).scalars().all()

        collateral_list = [
            CollateralOut(
                id=c.id,
                type=c.type,
                value=float(c.value),
                details=json.loads(c.details) if c.details else None
            )
            for c in rows
        ]

        logger.bind(
            route=f"/loans/{loanId}/collaterals",
            method="GET",
            count=len(collateral_list),
            correlationId=getattr(request.state, "correlation_id", None)
        ).info("list loan collateral")

        return collateral_list


@router.post("/loans/{loanId}/collaterals", status_code=201, response_model=CollateralOut)
async def create_collateral(request: Request, loanId: str, payload: CollateralIn):
    async with SessionLocal() as session:
        # Verify loan exists
        loan = await session.get(Loan, loanId)
        if not loan:
            raise HTTPException(status_code=404, detail={"code": "LOAN_NOT_FOUND"})

        collateral_id = payload.id or generate_collateral_id()

        collateral = Collateral(
            id=collateral_id,
            loan_id=loanId,
            type=payload.type,
            value=payload.value,
            details=json.dumps(payload.details) if payload.details else None
        )
        session.add(collateral)
        await session.commit()
        await session.refresh(collateral)

        logger.bind(
            route=f"/loans/{loanId}/collaterals",
            method="POST",
            collateralId=collateral.id,
            correlationId=getattr(request.state, "correlation_id", None)
        ).info("created loan collateral")

        return CollateralOut(
            id=collateral.id,
            type=collateral.type,
            value=float(collateral.value),
            details=json.loads(collateral.details) if collateral.details else None
        )


@router.put("/loans/{loanId}/collaterals/{collateralId}", response_model=CollateralOut)
async def update_collateral(request: Request, loanId: str, collateralId: str, payload: CollateralIn):
    async with SessionLocal() as session:
        collateral = await session.get(Collateral, collateralId)
        if not collateral or collateral.loan_id != loanId:
            raise HTTPException(status_code=404, detail={"code": "COLLATERAL_NOT_FOUND"})

        collateral.type = payload.type
        collateral.value = payload.value
        collateral.details = json.dumps(payload.details) if payload.details else None

        await session.commit()
        await session.refresh(collateral)

        logger.bind(
            route=f"/loans/{loanId}/collaterals/{collateralId}",
            method="PUT",
            correlationId=getattr(request.state, "correlation_id", None)
        ).info("updated loan collateral")

        return CollateralOut(
            id=collateral.id,
            type=collateral.type,
            value=float(collateral.value),
            details=json.loads(collateral.details) if collateral.details else None
        )


@router.delete("/loans/{loanId}/collaterals/{collateralId}", status_code=204)
async def delete_collateral(request: Request, loanId: str, collateralId: str):
    async with SessionLocal() as session:
        collateral = await session.get(Collateral, collateralId)
        if not collateral or collateral.loan_id != loanId:
            raise HTTPException(status_code=404, detail={"code": "COLLATERAL_NOT_FOUND"})

        await session.delete(collateral)
        await session.commit()

        logger.bind(
            route=f"/loans/{loanId}/collaterals/{collateralId}",
            method="DELETE",
            correlationId=getattr(request.state, "correlation_id", None)
        ).info("deleted loan collateral")

        return None


# Vehicle inventory endpoints
@router.get("/vehicle-inventory", response_model=PagedVehicleInventory)
async def list_vehicle_inventory(
    request: Request,
    page: int = 1,
    pageSize: int = 25,
    status: str | None = None,
    q: str | None = None,
):
    async with SessionLocal() as session:
        query = select(VehicleInventory)

        if status:
            query = query.where(VehicleInventory.status == status)

        if q:
            query = query.where(
                (VehicleInventory.brand.ilike(f"%{q}%")) |
                (VehicleInventory.model.ilike(f"%{q}%")) |
                (VehicleInventory.plate.ilike(f"%{q}%"))
            )

        query = query.order_by(VehicleInventory.id)

        # Get total count
        from sqlalchemy import func
        count_query = select(func.count()).select_from(query.subquery())
        total = (await session.execute(count_query)).scalar() or 0

        # Paginate
        query = query.offset((page - 1) * pageSize).limit(pageSize)
        rows = (await session.execute(query)).scalars().all()

        items = [
            VehicleInventoryOut(
                id=v.id,
                vinOrFrameNumber=v.vin_or_frame_number,
                brand=v.brand,
                model=v.model,
                plate=v.plate,
                color=v.color,
                purchasePrice=float(v.purchase_price) if v.purchase_price else None,
                msrp=float(v.msrp) if v.msrp else None,
                status=v.status,
                linkedLoanId=v.linked_loan_id
            )
            for v in rows
        ]

        logger.bind(
            route="/vehicle-inventory",
            method="GET",
            count=len(items),
            correlationId=getattr(request.state, "correlation_id", None)
        ).info("list vehicle inventory")

        return PagedVehicleInventory(items=items, page=page, pageSize=pageSize, total=total)


@router.post("/vehicle-inventory", status_code=201, response_model=VehicleInventoryOut)
async def create_vehicle(request: Request, payload: VehicleInventoryIn):
    async with SessionLocal() as session:
        vehicle_id = payload.id or generate_vehicle_id()

        vehicle = VehicleInventory(
            id=vehicle_id,
            vin_or_frame_number=payload.vinOrFrameNumber,
            brand=payload.brand,
            model=payload.model,
            plate=payload.plate,
            color=payload.color,
            purchase_price=payload.purchasePrice,
            msrp=payload.msrp,
            status=payload.status,
            linked_loan_id=None
        )
        session.add(vehicle)
        await session.commit()
        await session.refresh(vehicle)

        logger.bind(
            route="/vehicle-inventory",
            method="POST",
            vehicleId=vehicle.id,
            correlationId=getattr(request.state, "correlation_id", None)
        ).info("created vehicle inventory")

        return VehicleInventoryOut(
            id=vehicle.id,
            vinOrFrameNumber=vehicle.vin_or_frame_number,
            brand=vehicle.brand,
            model=vehicle.model,
            plate=vehicle.plate,
            color=vehicle.color,
            purchasePrice=float(vehicle.purchase_price) if vehicle.purchase_price else None,
            msrp=float(vehicle.msrp) if vehicle.msrp else None,
            status=vehicle.status,
            linkedLoanId=vehicle.linked_loan_id
        )


@router.put("/vehicle-inventory/{id}", response_model=VehicleInventoryOut)
async def update_vehicle(request: Request, id: str, payload: VehicleInventoryIn):
    async with SessionLocal() as session:
        vehicle = await session.get(VehicleInventory, id)
        if not vehicle:
            raise HTTPException(status_code=404, detail={"code": "VEHICLE_NOT_FOUND"})

        vehicle.vin_or_frame_number = payload.vinOrFrameNumber
        vehicle.brand = payload.brand
        vehicle.model = payload.model
        vehicle.plate = payload.plate
        vehicle.color = payload.color
        vehicle.purchase_price = payload.purchasePrice
        vehicle.msrp = payload.msrp

        await session.commit()
        await session.refresh(vehicle)

        logger.bind(
            route=f"/vehicle-inventory/{id}",
            method="PUT",
            correlationId=getattr(request.state, "correlation_id", None)
        ).info("updated vehicle inventory")

        return VehicleInventoryOut(
            id=vehicle.id,
            vinOrFrameNumber=vehicle.vin_or_frame_number,
            brand=vehicle.brand,
            model=vehicle.model,
            plate=vehicle.plate,
            color=vehicle.color,
            purchasePrice=float(vehicle.purchase_price) if vehicle.purchase_price else None,
            msrp=float(vehicle.msrp) if vehicle.msrp else None,
            status=vehicle.status,
            linkedLoanId=vehicle.linked_loan_id
        )


@router.post("/vehicle-inventory/{id}:allocate", response_model=VehicleInventoryOut)
async def allocate_vehicle(request: Request, id: str, payload: AllocateVehicleRequest):
    async with SessionLocal() as session:
        vehicle = await session.get(VehicleInventory, id)
        if not vehicle:
            raise HTTPException(status_code=404, detail={"code": "VEHICLE_NOT_FOUND"})

        if vehicle.status != "IN_STOCK":
            raise HTTPException(
                status_code=409,
                detail={"code": "VEHICLE_CONFLICT", "message": "Vehicle is not available for allocation"}
            )

        # Verify loan exists
        loan = await session.get(Loan, payload.loanId)
        if not loan:
            raise HTTPException(status_code=404, detail={"code": "LOAN_NOT_FOUND"})

        vehicle.status = "ALLOCATED"
        vehicle.linked_loan_id = payload.loanId

        await session.commit()
        await session.refresh(vehicle)

        logger.bind(
            route=f"/vehicle-inventory/{id}:allocate",
            method="POST",
            loanId=payload.loanId,
            correlationId=getattr(request.state, "correlation_id", None)
        ).info("allocated vehicle to loan")

        return VehicleInventoryOut(
            id=vehicle.id,
            vinOrFrameNumber=vehicle.vin_or_frame_number,
            brand=vehicle.brand,
            model=vehicle.model,
            plate=vehicle.plate,
            color=vehicle.color,
            purchasePrice=float(vehicle.purchase_price) if vehicle.purchase_price else None,
            msrp=float(vehicle.msrp) if vehicle.msrp else None,
            status=vehicle.status,
            linkedLoanId=vehicle.linked_loan_id
        )


@router.post("/vehicle-inventory/{id}:release", response_model=VehicleInventoryOut)
async def release_vehicle(request: Request, id: str, payload: AllocateVehicleRequest):
    async with SessionLocal() as session:
        vehicle = await session.get(VehicleInventory, id)
        if not vehicle:
            raise HTTPException(status_code=404, detail={"code": "VEHICLE_NOT_FOUND"})

        if vehicle.linked_loan_id != payload.loanId:
            raise HTTPException(
                status_code=409,
                detail={"code": "VEHICLE_CONFLICT", "message": "Vehicle is not allocated to this loan"}
            )

        vehicle.status = "IN_STOCK"
        vehicle.linked_loan_id = None

        await session.commit()
        await session.refresh(vehicle)

        logger.bind(
            route=f"/vehicle-inventory/{id}:release",
            method="POST",
            loanId=payload.loanId,
            correlationId=getattr(request.state, "correlation_id", None)
        ).info("released vehicle from loan")

        return VehicleInventoryOut(
            id=vehicle.id,
            vinOrFrameNumber=vehicle.vin_or_frame_number,
            brand=vehicle.brand,
            model=vehicle.model,
            plate=vehicle.plate,
            color=vehicle.color,
            purchasePrice=float(vehicle.purchase_price) if vehicle.purchase_price else None,
            msrp=float(vehicle.msrp) if vehicle.msrp else None,
            status=vehicle.status,
            linkedLoanId=vehicle.linked_loan_id
        )
