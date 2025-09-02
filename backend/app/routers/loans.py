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
from ..models.client import Client
from ..models.loan_product import LoanProduct


router = APIRouter(prefix="/v1", tags=["loans"])


class LoanOut(BaseModel):
    id: str
    clientId: str
    productId: str
    principal: float
    interestRate: Optional[float]
    termMonths: int
    status: str
    disbursedOn: Optional[str] = None  # ISO date string
    createdOn: str  # ISO datetime string


class LoanIn(BaseModel):
    id: Optional[str] = None
    clientId: str
    productId: str
    principal: float
    interestRate: Optional[float] = None
    termMonths: Optional[int] = None


class LoanUpdate(BaseModel):
    clientId: Optional[str] = None
    productId: Optional[str] = None
    principal: Optional[float] = None
    interestRate: Optional[float] = None
    termMonths: Optional[int] = None


class TransactionOut(BaseModel):
    id: str
    loanId: str
    type: str
    amount: float
    date: str  # ISO date string
    receiptNumber: str
    postedBy: Optional[str] = None


class LoanCommandResponse(BaseModel):
    loan: LoanOut
    transaction: Optional[TransactionOut] = None


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


class ChargePaymentResponse(BaseModel):
    charge: ChargeOut
    transaction: TransactionOut


@router.post("/loans", response_model=LoanOut)
async def create_loan(loan_data: LoanIn):
    """Create a new loan in PENDING status"""
    async with SessionLocal() as session:  # type: AsyncSession
        # Validate client exists
        client_result = await session.execute(select(Client).where(Client.id == loan_data.clientId))
        client = client_result.scalar_one_or_none()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Validate product exists
        product_result = await session.execute(select(LoanProduct).where(LoanProduct.id == loan_data.productId))
        product = product_result.scalar_one_or_none()
        if not product:
            raise HTTPException(status_code=404, detail="Loan product not found")

        loan = Loan(
            id=loan_data.id or str(uuid.uuid4()),
            client_id=loan_data.clientId,
            product_id=loan_data.productId,
            principal=loan_data.principal,
            interest_rate=loan_data.interestRate or product.interest_rate,
            term_months=loan_data.termMonths or product.term_months,
            status="PENDING",
            created_on=datetime.utcnow()
        )
        
        session.add(loan)
        await session.commit()
        await session.refresh(loan)
        
        return LoanOut(
            id=loan.id,
            clientId=loan.client_id,
            productId=loan.product_id,
            principal=float(loan.principal),
            interestRate=float(loan.interest_rate) if loan.interest_rate else None,
            termMonths=loan.term_months,
            status=loan.status,
            disbursedOn=loan.disbursed_on.isoformat() if loan.disbursed_on else None,
            createdOn=loan.created_on.isoformat()
        )


@router.get("/loans", response_model=list[LoanOut])
async def list_loans(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    q: Optional[str] = Query(None)
):
    """List loans with optional search"""
    async with SessionLocal() as session:  # type: AsyncSession
        stmt = select(Loan).order_by(Loan.created_on.desc()).offset(skip).limit(limit)
        
        if q:
            # Search by client display name or loan ID - need to join with clients
            stmt = stmt.join(Client).where(
                (Client.display_name.ilike(f"%{q}%")) | 
                (Loan.id.ilike(f"%{q}%"))
            )
        
        result = await session.execute(stmt)
        loans = result.scalars().all()
        
        return [
            LoanOut(
                id=loan.id,
                clientId=loan.client_id,
                productId=loan.product_id,
                principal=float(loan.principal),
                interestRate=float(loan.interest_rate) if loan.interest_rate else None,
                termMonths=loan.term_months,
                status=loan.status,
                disbursedOn=loan.disbursed_on.isoformat() if loan.disbursed_on else None,
                createdOn=loan.created_on.isoformat()
            )
            for loan in loans
        ]


@router.post("/loans", response_model=LoanOut)
async def create_loan(loan_data: LoanIn):
    """Create a new loan in PENDING status"""
    async with SessionLocal() as session:  # type: AsyncSession
        # Validate client exists
        client_result = await session.execute(select(Client).where(Client.id == loan_data.clientId))
        client = client_result.scalar_one_or_none()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Validate product exists
        product_result = await session.execute(select(LoanProduct).where(LoanProduct.id == loan_data.productId))
        product = product_result.scalar_one_or_none()
        if not product:
            raise HTTPException(status_code=404, detail="Loan product not found")

        loan = Loan(
            id=loan_data.id or str(uuid.uuid4()),
            client_id=loan_data.clientId,
            product_id=loan_data.productId,
            principal=loan_data.principal,
            interest_rate=loan_data.interestRate or product.interest_rate,
            term_months=loan_data.termMonths or product.term_months,
            status="PENDING",
            created_on=datetime.utcnow()
        )
        
        session.add(loan)
        await session.commit()
        await session.refresh(loan)
        
        return LoanOut(
            id=loan.id,
            clientId=loan.client_id,
            productId=loan.product_id,
            principal=float(loan.principal),
            interestRate=float(loan.interest_rate) if loan.interest_rate else None,
            termMonths=loan.term_months,
            status=loan.status,
            disbursedOn=loan.disbursed_on.isoformat() if loan.disbursed_on else None,
            createdOn=loan.created_on.isoformat()
        )


@router.get("/loans/{loan_id}", response_model=LoanOut)
async def get_loan(loan_id: str):
    """Get a specific loan"""
    async with SessionLocal() as session:  # type: AsyncSession
        result = await session.execute(select(Loan).where(Loan.id == loan_id))
        loan = result.scalar_one_or_none()
        
        if not loan:
            raise HTTPException(status_code=404, detail="Loan not found")
        
        return LoanOut(
            id=loan.id,
            clientId=loan.client_id,
            productId=loan.product_id,
            principal=float(loan.principal),
            interestRate=float(loan.interest_rate) if loan.interest_rate else None,
            termMonths=loan.term_months,
            status=loan.status,
            disbursedOn=loan.disbursed_on.isoformat() if loan.disbursed_on else None,
            createdOn=loan.created_on.isoformat()
        )


@router.put("/loans/{loan_id}", response_model=LoanOut)
async def update_loan(loan_id: str, loan_data: LoanUpdate):
    """Update a loan (only if status is PENDING)"""
    async with SessionLocal() as session:  # type: AsyncSession
        result = await session.execute(select(Loan).where(Loan.id == loan_id))
        loan = result.scalar_one_or_none()
        
        if not loan:
            raise HTTPException(status_code=404, detail="Loan not found")
        
        if loan.status != "PENDING":
            raise HTTPException(status_code=400, detail="Can only update loans in PENDING status")
        
        # Update fields
        update_data = loan_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if key == "clientId":
                loan.client_id = value
            elif key == "productId":
                loan.product_id = value
            elif key == "interestRate":
                loan.interest_rate = value
            elif key == "termMonths":
                loan.term_months = value
            elif hasattr(loan, key):
                setattr(loan, key, value)
        
        await session.commit()
        await session.refresh(loan)
        
        return LoanOut(
            id=loan.id,
            clientId=loan.client_id,
            productId=loan.product_id,
            principal=float(loan.principal),
            interestRate=float(loan.interest_rate) if loan.interest_rate else None,
            termMonths=loan.term_months,
            status=loan.status,
            disbursedOn=loan.disbursed_on.isoformat() if loan.disbursed_on else None,
            createdOn=loan.created_on.isoformat()
        )


@router.post("/loans/{loan_id}", response_model=LoanCommandResponse)
async def execute_loan_command(
    loan_id: str,
    command: str = Query(..., regex="^(approve|disburse|close)$"),
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    disbursement_date: Optional[str] = Query(None)  # ISO date string for disburse command
):
    """Execute loan commands: approve, disburse, or close"""
    async with SessionLocal() as session:  # type: AsyncSession
        result = await session.execute(select(Loan).where(Loan.id == loan_id))
        loan = result.scalar_one_or_none()
        
        if not loan:
            raise HTTPException(status_code=404, detail="Loan not found")
        
        transaction = None
        
        if command == "approve":
            # Check if already approved (idempotent)
            if loan.status == "APPROVED":
                pass  # Already approved, return as-is
            elif loan.status != "PENDING":
                raise HTTPException(status_code=400, detail="Can only approve loans in PENDING status")
            else:
                loan.status = "APPROVED"
                await session.commit()
                await session.refresh(loan)
        
        elif command == "disburse":
            # Check if already disbursed (idempotent)
            if loan.status == "DISBURSED":
                # Return existing disbursement transaction
                tx_result = await session.execute(
                    select(LoanTransaction).where(
                        LoanTransaction.loan_id == loan_id,
                        LoanTransaction.type == "DISBURSEMENT"
                    )
                )
                transaction = tx_result.scalar_one_or_none()
            elif loan.status != "APPROVED":
                raise HTTPException(status_code=400, detail="Can only disburse loans in APPROVED status")
            else:
                # Parse disbursement date
                disburse_date = date.today()
                if disbursement_date:
                    try:
                        disburse_date = datetime.fromisoformat(disbursement_date).date()
                    except ValueError:
                        raise HTTPException(status_code=400, detail="Invalid disbursement_date format. Use ISO date (YYYY-MM-DD)")
                
                # Update loan status
                loan.status = "DISBURSED"
                loan.disbursed_on = disburse_date
                
                # Create disbursement transaction
                transaction = LoanTransaction(
                    id=str(uuid.uuid4()),
                    loan_id=loan_id,
                    type="DISBURSEMENT",
                    amount=loan.principal,
                    date=disburse_date,
                    receipt_number=f"DISB-{loan_id[:8]}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    posted_by=None  # TODO: Get from auth context
                )
                
                session.add(transaction)
                await session.commit()
                await session.refresh(loan)
                await session.refresh(transaction)
        
        elif command == "close":
            # Check if already closed (idempotent)
            if loan.status == "CLOSED":
                pass  # Already closed, return as-is
            elif loan.status not in ["APPROVED", "DISBURSED"]:
                raise HTTPException(status_code=400, detail="Can only close loans in APPROVED or DISBURSED status")
            else:
                loan.status = "CLOSED"
                await session.commit()
                await session.refresh(loan)
        
        return LoanCommandResponse(
            loan=LoanOut(
                id=loan.id,
                clientId=loan.client_id,
                productId=loan.product_id,
                principal=float(loan.principal),
                interestRate=float(loan.interest_rate) if loan.interest_rate else None,
                termMonths=loan.term_months,
                status=loan.status,
                disbursedOn=loan.disbursed_on.isoformat() if loan.disbursed_on else None,
                createdOn=loan.created_on.isoformat()
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


@router.post("/loans/{loan_id}/transactions", response_model=LoanCommandResponse)
async def execute_transaction_command(
    loan_id: str,
    command: str = Query(..., regex="^(repayment|prepay|foreclosure|writeoff|waiveInterest|recovery)$"),
    amount: float = Query(..., gt=0),
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    transaction_date: Optional[str] = Query(None)  # ISO date string
):
    """Execute transaction commands: repayment, prepay, foreclosure, writeoff, waiveInterest, recovery"""
    async with SessionLocal() as session:  # type: AsyncSession
        result = await session.execute(select(Loan).where(Loan.id == loan_id))
        loan = result.scalar_one_or_none()
        
        if not loan:
            raise HTTPException(status_code=404, detail="Loan not found")
        
        if loan.status not in ["DISBURSED"]:
            raise HTTPException(status_code=400, detail="Can only create transactions for disbursed loans")
        
        # Parse transaction date
        tx_date = date.today()
        if transaction_date:
            try:
                tx_date = datetime.fromisoformat(transaction_date).date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid transaction_date format. Use ISO date (YYYY-MM-DD)")
        
        # Check for existing transaction with same idempotency key (simplified check by receipt pattern)
        existing_tx_result = await session.execute(
            select(LoanTransaction).where(
                LoanTransaction.loan_id == loan_id,
                LoanTransaction.receipt_number.like(f"%{idempotency_key[:8]}%")
            )
        )
        existing_transaction = existing_tx_result.scalar_one_or_none()
        
        if existing_transaction:
            # Return existing transaction (idempotent)
            return LoanCommandResponse(
                loan=LoanOut(
                    id=loan.id,
                    clientId=loan.client_id,
                    productId=loan.product_id,
                    principal=float(loan.principal),
                    interestRate=float(loan.interest_rate) if loan.interest_rate else None,
                    termMonths=loan.term_months,
                    status=loan.status,
                    disbursedOn=loan.disbursed_on.isoformat() if loan.disbursed_on else None,
                    createdOn=loan.created_on.isoformat()
                ),
                transaction=TransactionOut(
                    id=existing_transaction.id,
                    loanId=existing_transaction.loan_id,
                    type=existing_transaction.type,
                    amount=float(existing_transaction.amount),
                    date=existing_transaction.date.isoformat(),
                    receiptNumber=existing_transaction.receipt_number,
                    postedBy=existing_transaction.posted_by
                )
            )
        
        # Create new transaction
        transaction = LoanTransaction(
            id=str(uuid.uuid4()),
            loan_id=loan_id,
            type=command.upper(),
            amount=amount,
            date=tx_date,
            receipt_number=f"{command.upper()[:4]}-{loan_id[:8]}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            posted_by=None  # TODO: Get from auth context
        )
        
        session.add(transaction)
        await session.commit()
        await session.refresh(loan)
        await session.refresh(transaction)
        
        return LoanCommandResponse(
            loan=LoanOut(
                id=loan.id,
                clientId=loan.client_id,
                productId=loan.product_id,
                principal=float(loan.principal),
                interestRate=float(loan.interest_rate) if loan.interest_rate else None,
                termMonths=loan.term_months,
                status=loan.status,
                disbursedOn=loan.disbursed_on.isoformat() if loan.disbursed_on else None,
                createdOn=loan.created_on.isoformat()
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


@router.get("/loans/{loan_id}/transactions", response_model=list[TransactionOut])
async def list_loan_transactions(loan_id: str):
    """List all transactions for a loan"""
    async with SessionLocal() as session:  # type: AsyncSession
        # Verify loan exists
        loan_result = await session.execute(select(Loan).where(Loan.id == loan_id))
        loan = loan_result.scalar_one_or_none()
        if not loan:
            raise HTTPException(status_code=404, detail="Loan not found")
        
        # Get transactions
        result = await session.execute(
            select(LoanTransaction)
            .where(LoanTransaction.loan_id == loan_id)
            .order_by(LoanTransaction.date.desc())
        )
        transactions = result.scalars().all()
        
        return [
            TransactionOut(
                id=tx.id,
                loanId=tx.loan_id,
                type=tx.type,
                amount=float(tx.amount),
                date=tx.date.isoformat(),
                receiptNumber=tx.receipt_number,
                postedBy=tx.posted_by
            )
            for tx in transactions
        ]


@router.get("/loans/{loan_id}/transactions/template")
async def get_transaction_template(
    loan_id: str,
    command: str = Query(..., regex="^(repayment|prepay|foreclosure|writeoff|waiveInterest|recovery)$")
):
    """Get a transaction template for preview"""
    async with SessionLocal() as session:  # type: AsyncSession
        result = await session.execute(select(Loan).where(Loan.id == loan_id))
        loan = result.scalar_one_or_none()
        
        if not loan:
            raise HTTPException(status_code=404, detail="Loan not found")
        
        # Calculate suggested amounts based on command type
        suggested_amount = 0.0
        if command in ["repayment", "prepay"]:
            # For demo, suggest a portion of principal
            suggested_amount = float(loan.principal) * 0.1  # 10% of principal
        elif command in ["foreclosure", "writeoff"]:
            # Suggest remaining principal (simplified)
            suggested_amount = float(loan.principal)
        
        return {
            "command": command,
            "suggestedAmount": suggested_amount,
            "currency": "USD",
            "receiptNumberPreview": f"{command.upper()[:4]}-{loan_id[:8]}-YYYYMMDDHHMMSS"
        )