from __future__ import annotations

import time
import json
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, HTTPException, status, Request, Header
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import SessionLocal
from app.models.loan import Loan, LoanTransaction, LoanCharge, Collateral, VehicleInventory
from app.models.client import Client
from app.models.loan_product import LoanProduct
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


class DelinquencyStatusOut(BaseModel):
    currentBucketId: str
    daysPastDue: int
    asOfDate: str


class ScheduleInstallment(BaseModel):
    period: int
    dueDate: str
    principalDue: float
    interestDue: float
    totalDue: float
    paid: bool


class LoanAccountOut(BaseModel):
    id: str
    clientId: str
    productId: str
    principal: float
    interestRate: float | None
    termMonths: int
    status: str
    disbursedOn: str | None
    delinquencyStatus: DelinquencyStatusOut | None = None
    collateral: list[CollateralOut] = []
    schedule: list[ScheduleInstallment] = []


class LoanAccountIn(BaseModel):
    clientId: str
    productId: str
    principal: float
    interestRate: float | None = None
    termMonths: int
    collateral: list[CollateralIn] | None = None


class LoanTransactionOut(BaseModel):
    id: str
    loanId: str
    type: str
    amount: float
    date: str
    receiptNumber: str
    postedBy: str | None


class LoanCommandRequest(BaseModel):
    amount: float | None = None
    date: str | None = None
    vehicleInventoryId: str | None = None
    notes: str | None = None


class LoanCommandResponse(BaseModel):
    loan: LoanAccountOut
    transaction: LoanTransactionOut | None = None


class PagedLoans(BaseModel):
    items: list[LoanAccountOut]
    page: int
    pageSize: int
    total: int


# Helper functions
def generate_loan_id() -> str:
    return f"LN-{int(time.time() * 1000)}"


def generate_transaction_id() -> str:
    return f"TX-{int(time.time() * 1000)}"


def generate_receipt_number() -> str:
    return f"RCPT-{int(time.time() * 1000)}"


def calculate_schedule(principal: float, interest_rate: float, term_months: int, frequency: str, disbursement_date: date) -> list[ScheduleInstallment]:
    """
    Simple declining balance schedule calculation.
    This is a placeholder - real implementation would be more sophisticated.
    """
    schedule = []
    monthly_rate = interest_rate / 100 / 12
    installment_amount = principal * (monthly_rate * (1 + monthly_rate) ** term_months) / ((1 + monthly_rate) ** term_months - 1)

    remaining_balance = principal

    for period in range(1, term_months + 1):
        interest_due = remaining_balance * monthly_rate
        principal_due = installment_amount - interest_due

        # Calculate due date based on frequency
        if frequency == "MONTHLY":
            due_date = disbursement_date + timedelta(days=30 * period)
        elif frequency == "WEEKLY":
            due_date = disbursement_date + timedelta(days=7 * period)
        elif frequency == "BIWEEKLY":
            due_date = disbursement_date + timedelta(days=14 * period)
        else:
            due_date = disbursement_date + timedelta(days=30 * period)

        schedule.append(ScheduleInstallment(
            period=period,
            dueDate=due_date.isoformat(),
            principalDue=round(principal_due, 2),
            interestDue=round(interest_due, 2),
            totalDue=round(installment_amount, 2),
            paid=False
        ))

        remaining_balance -= principal_due

    return schedule


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


async def loan_to_dict(loan: Loan, session: AsyncSession) -> dict:
    """Convert loan ORM object to dictionary"""
    # Get collateral
    collateral_query = select(Collateral).where(Collateral.loan_id == loan.id)
    collateral_rows = (await session.execute(collateral_query)).scalars().all()

    collateral_list = [
        CollateralOut(
            id=c.id,
            type=c.type,
            value=float(c.value),
            details=json.loads(c.details) if c.details else None
        )
        for c in collateral_rows
    ]

    # Calculate schedule if disbursed
    schedule = []
    if loan.status == "DISBURSED" and loan.disbursed_on:
        product = await session.get(LoanProduct, loan.product_id)
        if product:
            schedule = calculate_schedule(
                float(loan.principal),
                float(loan.interest_rate or product.interest_rate),
                loan.term_months,
                product.repayment_frequency,
                loan.disbursed_on
            )

    return LoanAccountOut(
        id=loan.id,
        clientId=loan.client_id,
        productId=loan.product_id,
        principal=float(loan.principal),
        interestRate=float(loan.interest_rate) if loan.interest_rate else None,
        termMonths=loan.term_months,
        status=loan.status,
        disbursedOn=loan.disbursed_on.isoformat() if loan.disbursed_on else None,
        collateral=collateral_list,
        schedule=schedule
    ).model_dump()


# Routes
@router.get("/loans", response_model=PagedLoans)
async def list_loans(
    request: Request,
    page: int = 1,
    pageSize: int = 25,
    clientId: str | None = None,
    status: str | None = None,
):
    async with SessionLocal() as session:
        query = select(Loan)

        if clientId:
            query = query.where(Loan.client_id == clientId)
        if status:
            query = query.where(Loan.status == status)

        query = query.order_by(Loan.created_on.desc())

        # Get total count
        from sqlalchemy import func
        count_query = select(func.count()).select_from(query.subquery())
        total = (await session.execute(count_query)).scalar() or 0

        # Paginate
        query = query.offset((page - 1) * pageSize).limit(pageSize)
        rows = (await session.execute(query)).scalars().all()

        items = [await loan_to_dict(loan, session) for loan in rows]

        logger.bind(
            route="/loans",
            method="GET",
            count=len(items),
            correlationId=getattr(request.state, "correlation_id", None)
        ).info("list loans")

        return PagedLoans(items=items, page=page, pageSize=pageSize, total=total)


@router.post("/loans", status_code=201)
async def create_loan(
    request: Request,
    payload: LoanAccountIn,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
):
    async with SessionLocal() as session:
        # Check idempotency
        if idempotency_key:
            cached = await check_idempotency(session, idempotency_key, "/v1/loans")
            if cached:
                return cached

        # Verify client exists
        client = await session.get(Client, payload.clientId)
        if not client:
            raise HTTPException(status_code=404, detail={"code": "CLIENT_NOT_FOUND"})

        # Verify product exists
        product = await session.get(LoanProduct, payload.productId)
        if not product:
            raise HTTPException(status_code=404, detail={"code": "PRODUCT_NOT_FOUND"})

        # Create loan
        loan_id = generate_loan_id()
        loan = Loan(
            id=loan_id,
            client_id=payload.clientId,
            product_id=payload.productId,
            principal=payload.principal,
            interest_rate=payload.interestRate if payload.interestRate else product.interest_rate,
            term_months=payload.termMonths,
            status="PENDING",
            disbursed_on=None,
        )
        session.add(loan)

        # Add collateral if provided
        if payload.collateral:
            for coll_in in payload.collateral:
                coll_id = coll_in.id or f"COL-{int(time.time() * 1000)}"
                collateral = Collateral(
                    id=coll_id,
                    loan_id=loan_id,
                    type=coll_in.type,
                    value=coll_in.value,
                    details=json.dumps(coll_in.details) if coll_in.details else None
                )
                session.add(collateral)

        await session.commit()
        await session.refresh(loan)

        response_body = await loan_to_dict(loan, session)

        # Store idempotency
        if idempotency_key:
            await store_idempotency(session, idempotency_key, "/v1/loans", 201, response_body)
            await session.commit()

        logger.bind(
            route="/loans",
            method="POST",
            id=loan.id,
            clientId=loan.client_id,
            correlationId=getattr(request.state, "correlation_id", None)
        ).info("created loan")

        return response_body


@router.get("/loans/{loanId}")
async def get_loan(request: Request, loanId: str):
    async with SessionLocal() as session:
        loan = await session.get(Loan, loanId)
        if not loan:
            raise HTTPException(status_code=404, detail={"code": "LOAN_NOT_FOUND"})

        return await loan_to_dict(loan, session)


@router.put("/loans/{loanId}")
async def update_loan(
    request: Request,
    loanId: str,
    payload: LoanAccountIn,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
):
    async with SessionLocal() as session:
        # Check idempotency
        if idempotency_key:
            cached = await check_idempotency(session, idempotency_key, f"/v1/loans/{loanId}")
            if cached:
                return cached

        loan = await session.get(Loan, loanId)
        if not loan:
            raise HTTPException(status_code=404, detail={"code": "LOAN_NOT_FOUND"})

        # Only allow updates when PENDING
        if loan.status != "PENDING":
            raise HTTPException(
                status_code=400,
                detail={"code": "INVALID_STATUS", "message": "Can only update PENDING loans"}
            )

        # Update loan
        loan.principal = payload.principal
        loan.interest_rate = payload.interestRate
        loan.term_months = payload.termMonths

        await session.commit()
        await session.refresh(loan)

        response_body = await loan_to_dict(loan, session)

        # Store idempotency
        if idempotency_key:
            await store_idempotency(session, idempotency_key, f"/v1/loans/{loanId}", 200, response_body)
            await session.commit()

        logger.bind(
            route=f"/loans/{loanId}",
            method="PUT",
            correlationId=getattr(request.state, "correlation_id", None)
        ).info("updated loan")

        return response_body


@router.post("/loans/{loanId}", response_model=LoanCommandResponse)
async def loan_command(
    request: Request,
    loanId: str,
    command: str,
    payload: LoanCommandRequest,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
):
    """
    Perform loan commands: approve, disburse, close, repayment, prepay, foreclosure, writeoff, waiveInterest, recovery
    """
    async with SessionLocal() as session:
        # Check idempotency
        if idempotency_key:
            cached = await check_idempotency(session, idempotency_key, f"/v1/loans/{loanId}?command={command}")
            if cached:
                return cached

        loan = await session.get(Loan, loanId)
        if not loan:
            raise HTTPException(status_code=404, detail={"code": "LOAN_NOT_FOUND"})

        transaction = None

        # State machine transitions
        if command == "approve":
            if loan.status != "PENDING":
                raise HTTPException(
                    status_code=400,
                    detail={"code": "INVALID_TRANSITION", "message": f"Cannot approve loan in {loan.status} status"}
                )
            loan.status = "APPROVED"

        elif command == "disburse":
            if loan.status != "APPROVED":
                raise HTTPException(
                    status_code=400,
                    detail={"code": "INVALID_TRANSITION", "message": f"Cannot disburse loan in {loan.status} status"}
                )

            loan.status = "DISBURSED"
            loan.disbursed_on = datetime.fromisoformat(payload.date) if payload.date else date.today()

            # Handle vehicle inventory allocation if provided
            if payload.vehicleInventoryId:
                vehicle = await session.get(VehicleInventory, payload.vehicleInventoryId)
                if not vehicle:
                    raise HTTPException(status_code=404, detail={"code": "VEHICLE_NOT_FOUND"})

                if vehicle.status != "IN_STOCK":
                    raise HTTPException(
                        status_code=409,
                        detail={"code": "VEHICLE_CONFLICT", "message": "Vehicle is not available for allocation"}
                    )

                vehicle.status = "SOLD"
                vehicle.linked_loan_id = loanId

        elif command == "close":
            if loan.status not in ["APPROVED", "DISBURSED"]:
                raise HTTPException(
                    status_code=400,
                    detail={"code": "INVALID_TRANSITION", "message": f"Cannot close loan in {loan.status} status"}
                )
            loan.status = "CLOSED"

        elif command in ["repayment", "prepay", "foreclosure", "writeoff", "waiveInterest", "recovery"]:
            if loan.status != "DISBURSED":
                raise HTTPException(
                    status_code=400,
                    detail={"code": "INVALID_STATUS", "message": "Loan must be disbursed for transactions"}
                )

            if not payload.amount or not payload.date:
                raise HTTPException(
                    status_code=400,
                    detail={"code": "MISSING_FIELDS", "message": "amount and date are required"}
                )

            # Create transaction
            tx_id = generate_transaction_id()
            receipt_num = generate_receipt_number()

            transaction = LoanTransaction(
                id=tx_id,
                loan_id=loanId,
                type=command.upper(),
                amount=payload.amount,
                date=datetime.fromisoformat(payload.date),
                receipt_number=receipt_num,
                posted_by=getattr(request.state, "username", None)
            )
            session.add(transaction)

            # For writeoff, change loan status
            if command == "writeoff":
                loan.status = "WRITTEN_OFF"

        else:
            raise HTTPException(
                status_code=400,
                detail={"code": "INVALID_COMMAND", "message": f"Unknown command: {command}"}
            )

        await session.commit()
        await session.refresh(loan)

        loan_dict = await loan_to_dict(loan, session)

        transaction_dict = None
        if transaction:
            await session.refresh(transaction)
            transaction_dict = LoanTransactionOut(
                id=transaction.id,
                loanId=transaction.loan_id,
                type=transaction.type,
                amount=float(transaction.amount),
                date=transaction.date.isoformat(),
                receiptNumber=transaction.receipt_number,
                postedBy=transaction.posted_by
            ).model_dump()

        response_body = {
            "loan": loan_dict,
            "transaction": transaction_dict
        }

        # Store idempotency
        if idempotency_key:
            await store_idempotency(session, idempotency_key, f"/v1/loans/{loanId}?command={command}", 200, response_body)
            await session.commit()

        logger.bind(
            route=f"/loans/{loanId}",
            command=command,
            method="POST",
            correlationId=getattr(request.state, "correlation_id", None)
        ).info(f"executed loan command: {command}")

        return response_body


@router.get("/loans/{loanId}/transactions/template")
async def get_transaction_template(request: Request, loanId: str, command: str):
    """Get a template for transaction commands"""
    async with SessionLocal() as session:
        loan = await session.get(Loan, loanId)
        if not loan:
            raise HTTPException(status_code=404, detail={"code": "LOAN_NOT_FOUND"})

        if command in ["repayment", "prepay", "foreclosure", "recovery"]:
            return {
                "amount": 0.0,
                "date": date.today().isoformat(),
                "notes": ""
            }
        elif command == "waiveInterest":
            return {
                "amount": 0.0,
                "date": date.today().isoformat(),
                "notes": "Interest waiver"
            }
        elif command == "writeoff":
            return {
                "amount": float(loan.principal),
                "date": date.today().isoformat(),
                "notes": "Write-off"
            }
        else:
            raise HTTPException(status_code=400, detail={"code": "INVALID_COMMAND"})


@router.get("/clients/{clientId}/accounts")
async def get_client_loans(request: Request, clientId: str):
    """Get all loans for a client"""
    async with SessionLocal() as session:
        # Verify client exists
        client = await session.get(Client, clientId)
        if not client:
            raise HTTPException(status_code=404, detail={"code": "CLIENT_NOT_FOUND"})

        query = select(Loan).where(Loan.client_id == clientId).order_by(Loan.created_on.desc())
        rows = (await session.execute(query)).scalars().all()

        items = [await loan_to_dict(loan, session) for loan in rows]

        return items
