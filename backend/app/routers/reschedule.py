from __future__ import annotations

import time
import json
from datetime import date, datetime

from fastapi import APIRouter, HTTPException, status, Request, Header
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import SessionLocal
from app.models.loan import Loan
from loguru import logger


router = APIRouter(prefix="/v1")


# Pydantic models
class ScheduleChangeRequest(BaseModel):
    rescheduleFromDate: str | None = None
    newInterestRate: float | None = None
    extraTerms: int | None = None


class ScheduleInstallment(BaseModel):
    period: int
    dueDate: str
    principalDue: float
    interestDue: float
    totalDue: float
    paid: bool


class SchedulePreviewResponse(BaseModel):
    previewVersion: str
    schedule: list[ScheduleInstallment]


def generate_preview_version() -> str:
    return f"PV-{int(time.time() * 1000)}"


def calculate_new_schedule(loan: Loan, change_request: ScheduleChangeRequest) -> list[ScheduleInstallment]:
    """
    Placeholder schedule recalculation.
    Real implementation would be more sophisticated.
    """
    # Simplified placeholder
    return [
        ScheduleInstallment(
            period=1,
            dueDate=date.today().isoformat(),
            principalDue=100.0,
            interestDue=10.0,
            totalDue=110.0,
            paid=False
        )
    ]


@router.post("/loans/{loanId}/reschedule/preview", response_model=SchedulePreviewResponse)
async def preview_reschedule(request: Request, loanId: str, payload: ScheduleChangeRequest):
    async with SessionLocal() as session:
        loan = await session.get(Loan, loanId)
        if not loan:
            raise HTTPException(status_code=404, detail={"code": "LOAN_NOT_FOUND"})

        if loan.status != "DISBURSED":
            raise HTTPException(
                status_code=400,
                detail={"code": "INVALID_STATUS", "message": "Can only reschedule disbursed loans"}
            )

        preview_version = generate_preview_version()
        new_schedule = calculate_new_schedule(loan, payload)

        logger.bind(
            route=f"/loans/{loanId}/reschedule/preview",
            method="POST",
            previewVersion=preview_version,
            correlationId=getattr(request.state, "correlation_id", None)
        ).info("generated reschedule preview")

        return SchedulePreviewResponse(
            previewVersion=preview_version,
            schedule=new_schedule
        )


@router.post("/loans/{loanId}/reschedule/commit")
async def commit_reschedule(
    request: Request,
    loanId: str,
    payload: ScheduleChangeRequest,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
):
    async with SessionLocal() as session:
        loan = await session.get(Loan, loanId)
        if not loan:
            raise HTTPException(status_code=404, detail={"code": "LOAN_NOT_FOUND"})

        if loan.status != "DISBURSED":
            raise HTTPException(
                status_code=400,
                detail={"code": "INVALID_STATUS", "message": "Can only reschedule disbursed loans"}
            )

        # In production, verify previewVersion matches
        # For now, just apply changes

        if payload.newInterestRate:
            loan.interest_rate = payload.newInterestRate

        if payload.extraTerms:
            loan.term_months += payload.extraTerms

        await session.commit()
        await session.refresh(loan)

        logger.bind(
            route=f"/loans/{loanId}/reschedule/commit",
            method="POST",
            correlationId=getattr(request.state, "correlation_id", None)
        ).info("committed reschedule")

        return {
            "id": loan.id,
            "status": loan.status,
            "interestRate": float(loan.interest_rate) if loan.interest_rate else None,
            "termMonths": loan.term_months
        }
