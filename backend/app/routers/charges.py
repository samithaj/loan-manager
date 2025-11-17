from __future__ import annotations

import time
import json
from datetime import date, datetime

from fastapi import APIRouter, HTTPException, status, Request, Header
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import SessionLocal
from app.models.loan import Loan, LoanCharge, LoanTransaction
from loguru import logger


router = APIRouter(prefix="/v1")


# Pydantic models
class LoanChargeIn(BaseModel):
    id: str | None = None
    name: str
    amount: float
    dueDate: str | None = None


class LoanChargeOut(BaseModel):
    id: str
    loanId: str
    name: str
    amount: float
    dueDate: str | None
    status: str


class PayChargeRequest(BaseModel):
    amount: float
    date: str


class LoanTransactionOut(BaseModel):
    id: str
    loanId: str
    type: str
    amount: float
    date: str
    receiptNumber: str
    postedBy: str | None


def generate_charge_id() -> str:
    return f"CHG-{int(time.time() * 1000)}"


def generate_transaction_id() -> str:
    return f"TX-{int(time.time() * 1000)}"


def generate_receipt_number() -> str:
    return f"RCPT-{int(time.time() * 1000)}"


async def check_idempotency(session: AsyncSession, key: str, path: str) -> dict | None:
    """Check if request with this idempotency key was already processed"""
    from app.models.idempotency import IdempotencyRecord
    record = await session.get(IdempotencyRecord, key)
    if record and record.request_path == path:
        return json.loads(record.response_body)
    return None


async def store_idempotency(session: AsyncSession, key: str, path: str, response_status: int, response_body: dict):
    """Store idempotency record"""
    from app.models.idempotency import IdempotencyRecord
    record = IdempotencyRecord(
        idempotency_key=key,
        request_path=path,
        response_status=response_status,
        response_body=json.dumps(response_body)
    )
    session.add(record)


@router.get("/loans/{loanId}/charges", response_model=list[LoanChargeOut])
async def list_charges(request: Request, loanId: str):
    async with SessionLocal() as session:
        # Verify loan exists
        loan = await session.get(Loan, loanId)
        if not loan:
            raise HTTPException(status_code=404, detail={"code": "LOAN_NOT_FOUND"})

        query = select(LoanCharge).where(LoanCharge.loan_id == loanId).order_by(LoanCharge.id)
        rows = (await session.execute(query)).scalars().all()

        charges = [
            LoanChargeOut(
                id=c.id,
                loanId=c.loan_id,
                name=c.name,
                amount=float(c.amount),
                dueDate=c.due_date.isoformat() if c.due_date else None,
                status=c.status
            )
            for c in rows
        ]

        logger.bind(
            route=f"/loans/{loanId}/charges",
            method="GET",
            count=len(charges),
            correlationId=getattr(request.state, "correlation_id", None)
        ).info("list loan charges")

        return charges


@router.post("/loans/{loanId}/charges", status_code=201, response_model=LoanChargeOut)
async def create_charge(request: Request, loanId: str, payload: LoanChargeIn):
    async with SessionLocal() as session:
        # Verify loan exists
        loan = await session.get(Loan, loanId)
        if not loan:
            raise HTTPException(status_code=404, detail={"code": "LOAN_NOT_FOUND"})

        charge_id = payload.id or generate_charge_id()

        charge = LoanCharge(
            id=charge_id,
            loan_id=loanId,
            name=payload.name,
            amount=payload.amount,
            due_date=datetime.fromisoformat(payload.dueDate) if payload.dueDate else None,
            status="PENDING"
        )
        session.add(charge)
        await session.commit()
        await session.refresh(charge)

        logger.bind(
            route=f"/loans/{loanId}/charges",
            method="POST",
            chargeId=charge.id,
            correlationId=getattr(request.state, "correlation_id", None)
        ).info("created loan charge")

        return LoanChargeOut(
            id=charge.id,
            loanId=charge.loan_id,
            name=charge.name,
            amount=float(charge.amount),
            dueDate=charge.due_date.isoformat() if charge.due_date else None,
            status=charge.status
        )


@router.put("/loans/{loanId}/charges/{chargeId}", response_model=LoanChargeOut)
async def update_charge(request: Request, loanId: str, chargeId: str, payload: LoanChargeIn):
    async with SessionLocal() as session:
        charge = await session.get(LoanCharge, chargeId)
        if not charge or charge.loan_id != loanId:
            raise HTTPException(status_code=404, detail={"code": "CHARGE_NOT_FOUND"})

        charge.name = payload.name
        charge.amount = payload.amount
        charge.due_date = datetime.fromisoformat(payload.dueDate) if payload.dueDate else None

        await session.commit()
        await session.refresh(charge)

        logger.bind(
            route=f"/loans/{loanId}/charges/{chargeId}",
            method="PUT",
            correlationId=getattr(request.state, "correlation_id", None)
        ).info("updated loan charge")

        return LoanChargeOut(
            id=charge.id,
            loanId=charge.loan_id,
            name=charge.name,
            amount=float(charge.amount),
            dueDate=charge.due_date.isoformat() if charge.due_date else None,
            status=charge.status
        )


@router.delete("/loans/{loanId}/charges/{chargeId}", status_code=204)
async def delete_charge(request: Request, loanId: str, chargeId: str):
    async with SessionLocal() as session:
        charge = await session.get(LoanCharge, chargeId)
        if not charge or charge.loan_id != loanId:
            raise HTTPException(status_code=404, detail={"code": "CHARGE_NOT_FOUND"})

        await session.delete(charge)
        await session.commit()

        logger.bind(
            route=f"/loans/{loanId}/charges/{chargeId}",
            method="DELETE",
            correlationId=getattr(request.state, "correlation_id", None)
        ).info("deleted loan charge")

        return None


@router.post("/loans/{loanId}/charges/{chargeId}/pay", response_model=LoanTransactionOut)
async def pay_charge(
    request: Request,
    loanId: str,
    chargeId: str,
    payload: PayChargeRequest,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
):
    async with SessionLocal() as session:
        # Check idempotency
        if idempotency_key:
            cached = await check_idempotency(session, idempotency_key, f"/v1/loans/{loanId}/charges/{chargeId}/pay")
            if cached:
                return cached

        # Verify charge exists
        charge = await session.get(LoanCharge, chargeId)
        if not charge or charge.loan_id != loanId:
            raise HTTPException(status_code=404, detail={"code": "CHARGE_NOT_FOUND"})

        if charge.status == "PAID":
            raise HTTPException(status_code=400, detail={"code": "ALREADY_PAID"})

        # Create transaction for charge payment
        tx_id = generate_transaction_id()
        receipt_num = generate_receipt_number()

        transaction = LoanTransaction(
            id=tx_id,
            loan_id=loanId,
            type="CHARGE_PAYMENT",
            amount=payload.amount,
            date=datetime.fromisoformat(payload.date),
            receipt_number=receipt_num,
            posted_by=getattr(request.state, "username", None)
        )
        session.add(transaction)

        # Mark charge as paid
        charge.status = "PAID"

        await session.commit()
        await session.refresh(transaction)

        response_body = LoanTransactionOut(
            id=transaction.id,
            loanId=transaction.loan_id,
            type=transaction.type,
            amount=float(transaction.amount),
            date=transaction.date.isoformat(),
            receiptNumber=transaction.receipt_number,
            postedBy=transaction.posted_by
        ).model_dump()

        # Store idempotency
        if idempotency_key:
            await store_idempotency(session, idempotency_key, f"/v1/loans/{loanId}/charges/{chargeId}/pay", 200, response_body)
            await session.commit()

        logger.bind(
            route=f"/loans/{loanId}/charges/{chargeId}/pay",
            method="POST",
            transactionId=transaction.id,
            correlationId=getattr(request.state, "correlation_id", None)
        ).info("paid loan charge")

        return response_body
