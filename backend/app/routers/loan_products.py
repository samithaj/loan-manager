from __future__ import annotations

from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel, field_validator
from sqlalchemy import select
# SQLAlchemy session type imported for clarity in comments; not used directly
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: F401
from app.db import SessionLocal
from app.models.loan_product import LoanProduct
from loguru import logger


router = APIRouter(prefix="/v1")


ALLOWED_FREQUENCIES = {"DAILY", "WEEKLY", "BIWEEKLY", "MONTHLY"}


class LoanProductOut(BaseModel):
    id: str
    name: str
    interestRate: float
    termMonths: int
    repaymentFrequency: str


class LoanProductIn(BaseModel):
    id: str | None = None
    name: str
    interestRate: float
    termMonths: int
    repaymentFrequency: str

    @field_validator("interestRate")
    @classmethod
    def validate_interest_rate(cls, v: float) -> float:
        if v < 0 or v > 100:
            raise ValueError("interestRate must be between 0 and 100")
        return v

    @field_validator("repaymentFrequency")
    @classmethod
    def validate_freq(cls, v: str) -> str:
        if v not in ALLOWED_FREQUENCIES:
            raise ValueError("repaymentFrequency must be one of: " + ", ".join(sorted(ALLOWED_FREQUENCIES)))
        return v


@router.get("/loan-products", response_model=list[LoanProductOut])
async def list_products(request: Request):
    async with SessionLocal() as session:  # type: AsyncSession
        rows = (await session.execute(select(LoanProduct).order_by(LoanProduct.id))).scalars().all()
        logger.bind(route="/loan-products", method="GET", count=len(rows), correlationId=getattr(request.state, "correlation_id", None)).info("list loan products")
        return [
            LoanProductOut(
                id=r.id,
                name=r.name,
                interestRate=float(r.interest_rate),
                termMonths=r.term_months,
                repaymentFrequency=r.repayment_frequency,
            )
            for r in rows
        ]


@router.post("/loan-products", response_model=LoanProductOut, status_code=201)
async def create_product(request: Request, payload: LoanProductIn):
    async with SessionLocal() as session:  # type: AsyncSession
        new_id = payload.id or f"LP-{int(__import__('time').time()*1000):.0f}"
        exists = await session.get(LoanProduct, new_id)
        if exists:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "PRODUCT_EXISTS"})
        lp = LoanProduct(
            id=new_id,
            name=payload.name,
            interest_rate=payload.interestRate,
            term_months=payload.termMonths,
            repayment_frequency=payload.repaymentFrequency,
        )
        session.add(lp)
        await session.commit()
        await session.refresh(lp)
        logger.bind(route="/loan-products", method="POST", id=lp.id, name=lp.name, correlationId=getattr(request.state, "correlation_id", None)).info("created loan product")
        return LoanProductOut(
            id=lp.id,
            name=lp.name,
            interestRate=float(lp.interest_rate),
            termMonths=lp.term_months,
            repaymentFrequency=lp.repayment_frequency,
        )


