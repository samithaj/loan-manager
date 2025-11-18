from __future__ import annotations

from datetime import date as DateType
from fastapi import APIRouter, HTTPException, Query, Header, Request, status, Depends
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: F401
from ..db import SessionLocal
from ..models.loan import Loan
from ..models.audit import LoanAudit
from ..models.idempotency import IdempotencyKey
from ..rbac import require_roles
from datetime import datetime, timezone, timedelta
import uuid


router = APIRouter(prefix="/v1")


ALLOWED_STATUSES = {"PENDING", "APPROVED", "DISBURSED", "CLOSED"}


class LoanOut(BaseModel):
    id: str
    clientId: str
    productId: str
    principal: float
    interestRate: float | None = None
    termMonths: int
    status: str
    disbursedOn: str | None = None


class LoanIn(BaseModel):
    id: str
    clientId: str
    productId: str
    principal: float
    interestRate: float | None = None
    termMonths: int
    status: str | None = None

    @field_validator("principal")
    @classmethod
    def validate_principal(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("principal must be > 0")
        return v
class LoanAuditOut(BaseModel):
    id: str
    loanId: str
    actor: str
    action: str
    at: str
    correlationId: str | None = None
    meta: dict | None = None


def _audit_to_out(a: LoanAudit) -> LoanAuditOut:
    return LoanAuditOut(
        id=a.id,
        loanId=a.loan_id,
        actor=a.actor,
        action=a.action,
        at=a.at.isoformat() if hasattr(a.at, 'isoformat') else str(a.at),
        correlationId=a.correlation_id,
        meta=a.meta,
    )


    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if v not in ALLOWED_STATUSES:
            raise ValueError("invalid status")
        return v


def _to_out(row: Loan) -> LoanOut:
    return LoanOut(
        id=row.id,
        clientId=row.client_id,
        productId=row.product_id,
        principal=float(row.principal),
        interestRate=float(row.interest_rate) if row.interest_rate is not None else None,
        termMonths=row.term_months,
        status=row.status,
        disbursedOn=row.disbursed_on.isoformat() if getattr(row, "disbursed_on", None) else None,
    )


@router.post("/loans", response_model=LoanOut, status_code=201)
async def create_loan(request: Request, payload: LoanIn):
    async with SessionLocal() as session:  # type: AsyncSession
        exists = await session.get(Loan, payload.id)
        if exists:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "LOAN_EXISTS"})
        loan = Loan(
            id=payload.id,
            client_id=payload.clientId,
            product_id=payload.productId,
            principal=payload.principal,
            interest_rate=payload.interestRate,
            term_months=payload.termMonths,
            status=payload.status or "PENDING",
            disbursed_on=None,
        )
        session.add(loan)
        await session.commit()
        await session.refresh(loan)
        # audit
        session.add(LoanAudit(
            id=str(uuid.uuid4()),
            loan_id=loan.id,
            actor=getattr(getattr(request.state, 'principal', {}), 'get', lambda *_: None)('username') or 'unknown',
            action='create',
            correlation_id=getattr(request.state, 'correlation_id', None),
            meta={"principal": float(payload.principal)},
        ))
        await session.commit()
        return _to_out(loan)


@router.get("/loans/{loanId}", response_model=LoanOut)
async def get_loan(loanId: str):
    async with SessionLocal() as session:  # type: AsyncSession
        loan = await session.get(Loan, loanId)
        if not loan:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND"})
        return _to_out(loan)


@router.put("/loans/{loanId}", response_model=LoanOut)
async def update_loan(loanId: str, payload: LoanIn):
    async with SessionLocal() as session:  # type: AsyncSession
        loan = await session.get(Loan, loanId)
        if not loan:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND"})
        if loan.status != "PENDING":
            raise HTTPException(status_code=409, detail={"code": "INVALID_STATE"})
        loan.client_id = payload.clientId
        loan.product_id = payload.productId
        loan.principal = payload.principal
        loan.interest_rate = payload.interestRate
        loan.term_months = payload.termMonths
        await session.commit()
        await session.refresh(loan)
        return _to_out(loan)


@router.post("/loans/{loanId}", response_model=LoanOut, dependencies=[Depends(require_roles("admin", "user"))])
async def loan_command(
    request: Request,
    loanId: str,
    command: str = Query(..., pattern="^(approve|disburse|close)$"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    if not idempotency_key:
        raise HTTPException(status_code=400, detail={"code": "MISSING_IDEMPOTENCY_KEY"})
    async with SessionLocal() as session:  # type: AsyncSession
        loan = await session.get(Loan, loanId)
        if not loan:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND"})

        # idempotency lookup within 24h
        scope = f"loan:{loanId}:{command}"
        existing = await session.get(IdempotencyKey, idempotency_key)
        if existing and existing.scope == scope:
            # return stored response
            stored = existing.response_json
            return LoanOut(**stored)

        # For now, accept one operation per state transition; no persistence of idempotency keys yet
        if command == "approve":
            if loan.status != "PENDING":
                raise HTTPException(status_code=409, detail={"code": "INVALID_STATE"})
            loan.status = "APPROVED"
        elif command == "disburse":
            if loan.status != "APPROVED":
                raise HTTPException(status_code=409, detail={"code": "INVALID_STATE"})
            loan.status = "DISBURSED"
            loan.disbursed_on = DateType.today()
        elif command == "close":
            if loan.status not in {"DISBURSED"}:
                raise HTTPException(status_code=409, detail={"code": "INVALID_STATE"})
            loan.status = "CLOSED"
        else:
            raise HTTPException(status_code=400, detail={"code": "INVALID_COMMAND"})

        await session.commit()
        await session.refresh(loan)
        # store idempotency record (24h later cleanup done by DB job externally)
        session.add(IdempotencyKey(
            key=idempotency_key,
            scope=scope,
            response_json=_to_out(loan).model_dump(),
            created_at=datetime.now(timezone.utc),
        ))
        # audit
        session.add(LoanAudit(
            id=str(uuid.uuid4()),
            loan_id=loan.id,
            actor=getattr(getattr(request.state, 'principal', {}), 'get', lambda *_: None)('username') or 'unknown',
            action=command,
            correlation_id=getattr(request.state, 'correlation_id', None),
            meta=None,
        ))
        await session.commit()
        return _to_out(loan)


@router.get("/loans", response_model=list[LoanOut])
async def list_loans(
    clientId: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    sort: str | None = Query(default=None, description="e.g. created_on,desc"),
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=50, ge=1, le=200),
):
    async with SessionLocal() as session:  # type: AsyncSession
        from sqlalchemy import select
        stmt = select(Loan)
        if clientId:
            stmt = stmt.where(Loan.client_id == clientId)
        if status_filter:
            stmt = stmt.where(Loan.status == status_filter)
        # sorting
        if sort:
            field, _, direction = sort.partition(",")
            field = field.strip()
            direction = (direction or "asc").strip().lower()
            col = getattr(Loan, field, Loan.created_on)
            stmt = stmt.order_by(col.desc() if direction == "desc" else col.asc())
        else:
            stmt = stmt.order_by(Loan.created_on.desc())
        offset_val = (page - 1) * pageSize
        stmt = stmt.offset(offset_val).limit(pageSize)
        rows = (await session.execute(stmt)).scalars().all()
        return [_to_out(r) for r in rows]


@router.get("/loans/{loanId}/audit", response_model=list[LoanAuditOut])
async def get_loan_audit(loanId: str):
    async with SessionLocal() as session:  # type: AsyncSession
        from sqlalchemy import select
        rows = (await session.execute(
            select(LoanAudit).where(LoanAudit.loan_id == loanId).order_by(LoanAudit.at.desc())
        )).scalars().all()
        return [_audit_to_out(a) for a in rows]


