from __future__ import annotations

import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ..db import SessionLocal
from ..models.loan import Loan, Collateral


router = APIRouter(prefix="/v1", tags=["collateral"])


class CollateralOut(BaseModel):
    id: str
    loanId: Optional[str] = None
    type: str
    value: float
    details: Optional[str] = None  # JSON string


class CollateralIn(BaseModel):
    id: Optional[str] = None
    type: str
    value: float
    details: Optional[str] = None  # JSON string


@router.get("/loans/{loan_id}/collaterals", response_model=list[CollateralOut])
async def list_loan_collaterals(loan_id: str):
    """List all collaterals for a loan"""
    async with SessionLocal() as session:  # type: AsyncSession
        # Verify loan exists
        loan_result = await session.execute(select(Loan).where(Loan.id == loan_id))
        loan = loan_result.scalar_one_or_none()
        if not loan:
            raise HTTPException(status_code=404, detail="Loan not found")
        
        # Get collaterals
        result = await session.execute(
            select(Collateral).where(Collateral.loan_id == loan_id)
        )
        collaterals = result.scalars().all()
        
        return [
            CollateralOut(
                id=collateral.id,
                loanId=collateral.loan_id,
                type=collateral.type,
                value=float(collateral.value),
                details=collateral.details
            )
            for collateral in collaterals
        ]


@router.post("/loans/{loan_id}/collaterals", response_model=CollateralOut)
async def create_loan_collateral(loan_id: str, collateral_data: CollateralIn):
    """Create a new collateral for a loan"""
    async with SessionLocal() as session:  # type: AsyncSession
        # Verify loan exists
        loan_result = await session.execute(select(Loan).where(Loan.id == loan_id))
        loan = loan_result.scalar_one_or_none()
        if not loan:
            raise HTTPException(status_code=404, detail="Loan not found")
        
        collateral = Collateral(
            id=collateral_data.id or str(uuid.uuid4()),
            loan_id=loan_id,
            type=collateral_data.type,
            value=collateral_data.value,
            details=collateral_data.details
        )
        
        session.add(collateral)
        await session.commit()
        await session.refresh(collateral)
        
        return CollateralOut(
            id=collateral.id,
            loanId=collateral.loan_id,
            type=collateral.type,
            value=float(collateral.value),
            details=collateral.details
        )


@router.put("/loans/{loan_id}/collaterals/{collateral_id}", response_model=CollateralOut)
async def update_loan_collateral(loan_id: str, collateral_id: str, collateral_data: CollateralIn):
    """Update a collateral"""
    async with SessionLocal() as session:  # type: AsyncSession
        result = await session.execute(
            select(Collateral).where(
                Collateral.id == collateral_id,
                Collateral.loan_id == loan_id
            )
        )
        collateral = result.scalar_one_or_none()
        
        if not collateral:
            raise HTTPException(status_code=404, detail="Collateral not found")
        
        collateral.type = collateral_data.type
        collateral.value = collateral_data.value
        collateral.details = collateral_data.details
        
        await session.commit()
        await session.refresh(collateral)
        
        return CollateralOut(
            id=collateral.id,
            loanId=collateral.loan_id,
            type=collateral.type,
            value=float(collateral.value),
            details=collateral.details
        )


@router.delete("/loans/{loan_id}/collaterals/{collateral_id}")
async def delete_loan_collateral(loan_id: str, collateral_id: str):
    """Delete a collateral"""
    async with SessionLocal() as session:  # type: AsyncSession
        result = await session.execute(
            select(Collateral).where(
                Collateral.id == collateral_id,
                Collateral.loan_id == loan_id
            )
        )
        collateral = result.scalar_one_or_none()
        
        if not collateral:
            raise HTTPException(status_code=404, detail="Collateral not found")
        
        await session.delete(collateral)
        await session.commit()
        
        return {"message": "Collateral deleted"}