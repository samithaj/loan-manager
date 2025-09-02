from __future__ import annotations

import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ..db import SessionLocal
from ..models.loan import VehicleInventory, Loan


router = APIRouter(prefix="/v1", tags=["vehicle-inventory"])


class VehicleOut(BaseModel):
    id: str
    vinOrFrameNumber: Optional[str] = None
    brand: str
    model: str
    plate: Optional[str] = None
    color: Optional[str] = None
    purchasePrice: Optional[float] = None
    msrp: Optional[float] = None
    status: str
    linkedLoanId: Optional[str] = None


class VehicleIn(BaseModel):
    id: Optional[str] = None
    vinOrFrameNumber: Optional[str] = None
    brand: str
    model: str
    plate: Optional[str] = None
    color: Optional[str] = None
    purchasePrice: Optional[float] = None
    msrp: Optional[float] = None


@router.get("/vehicle-inventory", response_model=list[VehicleOut])
async def list_vehicles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None)
):
    """List vehicle inventory"""
    async with SessionLocal() as session:  # type: AsyncSession
        stmt = select(VehicleInventory).offset(skip).limit(limit)
        
        if status:
            stmt = stmt.where(VehicleInventory.status == status)
        
        result = await session.execute(stmt)
        vehicles = result.scalars().all()
        
        return [
            VehicleOut(
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
            for vehicle in vehicles
        ]


@router.post("/vehicle-inventory", response_model=VehicleOut)
async def create_vehicle(vehicle_data: VehicleIn):
    """Create a new vehicle in inventory"""
    async with SessionLocal() as session:  # type: AsyncSession
        vehicle = VehicleInventory(
            id=vehicle_data.id or str(uuid.uuid4()),
            vin_or_frame_number=vehicle_data.vinOrFrameNumber,
            brand=vehicle_data.brand,
            model=vehicle_data.model,
            plate=vehicle_data.plate,
            color=vehicle_data.color,
            purchase_price=vehicle_data.purchasePrice,
            msrp=vehicle_data.msrp,
            status="IN_STOCK",
            linked_loan_id=None
        )
        
        session.add(vehicle)
        await session.commit()
        await session.refresh(vehicle)
        
        return VehicleOut(
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


@router.get("/vehicle-inventory/{vehicle_id}", response_model=VehicleOut)
async def get_vehicle(vehicle_id: str):
    """Get a specific vehicle"""
    async with SessionLocal() as session:  # type: AsyncSession
        result = await session.execute(select(VehicleInventory).where(VehicleInventory.id == vehicle_id))
        vehicle = result.scalar_one_or_none()
        
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        return VehicleOut(
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


@router.put("/vehicle-inventory/{vehicle_id}", response_model=VehicleOut)
async def update_vehicle(vehicle_id: str, vehicle_data: VehicleIn):
    """Update a vehicle"""
    async with SessionLocal() as session:  # type: AsyncSession
        result = await session.execute(select(VehicleInventory).where(VehicleInventory.id == vehicle_id))
        vehicle = result.scalar_one_or_none()
        
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        vehicle.vin_or_frame_number = vehicle_data.vinOrFrameNumber
        vehicle.brand = vehicle_data.brand
        vehicle.model = vehicle_data.model
        vehicle.plate = vehicle_data.plate
        vehicle.color = vehicle_data.color
        vehicle.purchase_price = vehicle_data.purchasePrice
        vehicle.msrp = vehicle_data.msrp
        
        await session.commit()
        await session.refresh(vehicle)
        
        return VehicleOut(
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


@router.delete("/vehicle-inventory/{vehicle_id}")
async def delete_vehicle(vehicle_id: str):
    """Delete a vehicle"""
    async with SessionLocal() as session:  # type: AsyncSession
        result = await session.execute(select(VehicleInventory).where(VehicleInventory.id == vehicle_id))
        vehicle = result.scalar_one_or_none()
        
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        if vehicle.status == "SOLD":
            raise HTTPException(status_code=400, detail="Cannot delete sold vehicles")
        
        await session.delete(vehicle)
        await session.commit()
        
        return {"message": "Vehicle deleted"}


@router.post("/vehicle-inventory/{vehicle_id}/allocate")
async def allocate_vehicle(vehicle_id: str, loan_id: str = Query(...)):
    """Allocate a vehicle to a loan"""
    async with SessionLocal() as session:  # type: AsyncSession
        # Get vehicle
        vehicle_result = await session.execute(select(VehicleInventory).where(VehicleInventory.id == vehicle_id))
        vehicle = vehicle_result.scalar_one_or_none()
        
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        if vehicle.status != "IN_STOCK":
            raise HTTPException(status_code=409, detail="Vehicle is not available for allocation")
        
        # Verify loan exists
        loan_result = await session.execute(select(Loan).where(Loan.id == loan_id))
        loan = loan_result.scalar_one_or_none()
        if not loan:
            raise HTTPException(status_code=404, detail="Loan not found")
        
        # Allocate vehicle
        vehicle.status = "ALLOCATED"
        vehicle.linked_loan_id = loan_id
        
        await session.commit()
        await session.refresh(vehicle)
        
        return VehicleOut(
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


@router.post("/vehicle-inventory/{vehicle_id}/release")
async def release_vehicle(vehicle_id: str):
    """Release a vehicle from loan allocation"""
    async with SessionLocal() as session:  # type: AsyncSession
        result = await session.execute(select(VehicleInventory).where(VehicleInventory.id == vehicle_id))
        vehicle = result.scalar_one_or_none()
        
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        if vehicle.status not in ["ALLOCATED"]:
            raise HTTPException(status_code=400, detail="Vehicle is not allocated")
        
        # Release vehicle
        vehicle.status = "IN_STOCK"
        vehicle.linked_loan_id = None
        
        await session.commit()
        await session.refresh(vehicle)
        
        return VehicleOut(
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


@router.post("/vehicle-inventory/{vehicle_id}/sell")
async def sell_vehicle(vehicle_id: str):
    """Mark a vehicle as sold (for disbursement)"""
    async with SessionLocal() as session:  # type: AsyncSession
        result = await session.execute(select(VehicleInventory).where(VehicleInventory.id == vehicle_id))
        vehicle = result.scalar_one_or_none()
        
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        if vehicle.status == "SOLD":
            # Already sold (idempotent)
            return VehicleOut(
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
        
        if vehicle.status not in ["IN_STOCK", "ALLOCATED"]:
            raise HTTPException(status_code=409, detail="Vehicle cannot be sold in current status")
        
        # Mark as sold
        vehicle.status = "SOLD"
        
        await session.commit()
        await session.refresh(vehicle)
        
        return VehicleOut(
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