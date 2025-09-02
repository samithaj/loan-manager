from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Header, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ..db import SessionLocal
from ..models.loan import Loan, LoanTransaction, LoanCharge


router = APIRouter(prefix="/v1", tags=["charges"])


class ChargeOut(BaseModel):
    id: str
    loanId: str
    name: str
    amount: float
    dueDate: Optional[str] = None  # ISO date string
    status: str


class ChargeIn(BaseModel):
    id: Optional[str] = None
    name: str
    amount: float
    dueDate: Optional[str] = None  # ISO date string


class TransactionOut(BaseModel):
    id: str
    loanId: str
    type: str
    amount: float
    date: str  # ISO date string
    receiptNumber: str
    postedBy: Optional[str] = None


class ChargePaymentResponse(BaseModel):
    charge: ChargeOut
    transaction: TransactionOut


@router.get("/loans/{loan_id}/charges", response_model=list[ChargeOut])
async def list_loan_charges(loan_id: str):
    """List all charges for a loan"""
    async with SessionLocal() as session:  # type: AsyncSession
        # Verify loan exists
        loan_result = await session.execute(select(Loan).where(Loan.id == loan_id))
        loan = loan_result.scalar_one_or_none()
        if not loan:
            raise HTTPException(status_code=404, detail="Loan not found")
        
        # Get charges
        result = await session.execute(
            select(LoanCharge)
            .where(LoanCharge.loan_id == loan_id)
            .order_by(LoanCharge.due_date.asc())
        )
        charges = result.scalars().all()
        
        return [
            ChargeOut(
                id=charge.id,
                loanId=charge.loan_id,
                name=charge.name,
                amount=float(charge.amount),
                dueDate=charge.due_date.isoformat() if charge.due_date else None,
                status=charge.status
            )
            for charge in charges
        ]


@router.post("/loans/{loan_id}/charges", response_model=ChargeOut)
async def create_loan_charge(loan_id: str, charge_data: ChargeIn):
    """Create a new charge for a loan"""
    async with SessionLocal() as session:  # type: AsyncSession
        # Verify loan exists
        loan_result = await session.execute(select(Loan).where(Loan.id == loan_id))
        loan = loan_result.scalar_one_or_none()
        if not loan:
            raise HTTPException(status_code=404, detail="Loan not found")
        
        # Parse due date
        due_date = None
        if charge_data.dueDate:
            try:
                due_date = datetime.fromisoformat(charge_data.dueDate).date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid dueDate format. Use ISO date (YYYY-MM-DD)")
        
        charge = LoanCharge(
            id=charge_data.id or str(uuid.uuid4()),
            loan_id=loan_id,
            name=charge_data.name,
            amount=charge_data.amount,
            due_date=due_date,
            status="PENDING"
        )
        
        session.add(charge)
        await session.commit()
        await session.refresh(charge)
        
        return ChargeOut(
            id=charge.id,
            loanId=charge.loan_id,
            name=charge.name,
            amount=float(charge.amount),
            dueDate=charge.due_date.isoformat() if charge.due_date else None,
            status=charge.status
        )


@router.put("/loans/{loan_id}/charges/{charge_id}", response_model=ChargeOut)
async def update_loan_charge(loan_id: str, charge_id: str, charge_data: ChargeIn):
    """Update a charge"""
    async with SessionLocal() as session:  # type: AsyncSession
        result = await session.execute(
            select(LoanCharge).where(
                LoanCharge.id == charge_id,
                LoanCharge.loan_id == loan_id
            )
        )
        charge = result.scalar_one_or_none()
        
        if not charge:
            raise HTTPException(status_code=404, detail="Charge not found")
        
        if charge.status == "PAID":
            raise HTTPException(status_code=400, detail="Cannot update paid charges")
        
        # Parse due date
        due_date = None
        if charge_data.dueDate:
            try:
                due_date = datetime.fromisoformat(charge_data.dueDate).date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid dueDate format. Use ISO date (YYYY-MM-DD)")
        
        charge.name = charge_data.name
        charge.amount = charge_data.amount
        charge.due_date = due_date
        
        await session.commit()
        await session.refresh(charge)
        
        return ChargeOut(
            id=charge.id,
            loanId=charge.loan_id,
            name=charge.name,
            amount=float(charge.amount),
            dueDate=charge.due_date.isoformat() if charge.due_date else None,
            status=charge.status
        )


@router.delete("/loans/{loan_id}/charges/{charge_id}")
async def delete_loan_charge(loan_id: str, charge_id: str):
    """Delete a charge"""
    async with SessionLocal() as session:  # type: AsyncSession
        result = await session.execute(
            select(LoanCharge).where(
                LoanCharge.id == charge_id,
                LoanCharge.loan_id == loan_id
            )
        )
        charge = result.scalar_one_or_none()
        
        if not charge:
            raise HTTPException(status_code=404, detail="Charge not found")
        
        if charge.status == "PAID":
            raise HTTPException(status_code=400, detail="Cannot delete paid charges")
        
        await session.delete(charge)
        await session.commit()
        
        return {"message": "Charge deleted"}


@router.post("/loans/{loan_id}/charges/{charge_id}/pay", response_model=ChargePaymentResponse)
async def pay_charge(
    loan_id: str,
    charge_id: str,
    amount: Optional[float] = Query(None),
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    payment_date: Optional[str] = Query(None)
):
    """Pay a charge (creates a transaction)"""
    async with SessionLocal() as session:  # type: AsyncSession
        result = await session.execute(
            select(LoanCharge).where(
                LoanCharge.id == charge_id,
                LoanCharge.loan_id == loan_id
            )
        )
        charge = result.scalar_one_or_none()
        
        if not charge:
            raise HTTPException(status_code=404, detail="Charge not found")
        
        if charge.status == "PAID":
            # Return existing payment transaction (idempotent)
            tx_result = await session.execute(
                select(LoanTransaction).where(
                    LoanTransaction.loan_id == loan_id,
                    LoanTransaction.type == "CHARGE_PAYMENT",
                    LoanTransaction.receipt_number.like(f"%{charge_id[:8]}%")
                )
            )
            transaction = tx_result.scalar_one_or_none()
            
            return ChargePaymentResponse(
                charge=ChargeOut(
                    id=charge.id,
                    loanId=charge.loan_id,
                    name=charge.name,
                    amount=float(charge.amount),
                    dueDate=charge.due_date.isoformat() if charge.due_date else None,
                    status=charge.status
                ),
                transaction=TransactionOut(
                    id=transaction.id,
                    loanId=transaction.loan_id,
                    type=transaction.type,
                    amount=float(transaction.amount),
                    date=transaction.date.isoformat(),
                    receiptNumber=transaction.receipt_number,
                    postedBy=transaction.posted_by
                ) if transaction else None
            )
        
        # Use provided amount or full charge amount
        payment_amount = amount or float(charge.amount)
        
        # Parse payment date
        pay_date = date.today()
        if payment_date:
            try:
                pay_date = datetime.fromisoformat(payment_date).date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid payment_date format. Use ISO date (YYYY-MM-DD)")
        
        # Mark charge as paid
        charge.status = "PAID"
        
        # Create payment transaction
        transaction = LoanTransaction(
            id=str(uuid.uuid4()),
            loan_id=loan_id,
            type="CHARGE_PAYMENT",
            amount=payment_amount,
            date=pay_date,
            receipt_number=f"CHRG-{charge_id[:8]}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            posted_by=None  # TODO: Get from auth context
        )
        
        session.add(transaction)
        await session.commit()
        await session.refresh(charge)
        await session.refresh(transaction)
        
        return ChargePaymentResponse(
            charge=ChargeOut(
                id=charge.id,
                loanId=charge.loan_id,
                name=charge.name,
                amount=float(charge.amount),
                dueDate=charge.due_date.isoformat() if charge.due_date else None,
                status=charge.status
            ),
            transaction=TransactionOut(
                id=transaction.id,
                loanId=transaction.loan_id,
                type=transaction.type,
                amount=float(transaction.amount),
                date=transaction.date.isoformat(),
                receiptNumber=transaction.receipt_number,
                postedBy=transaction.posted_by
            )
        )