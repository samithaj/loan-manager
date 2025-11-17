from __future__ import annotations

import csv
import io
from datetime import date

from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import SessionLocal
from app.models.loan import Loan, DelinquencyStatus
from loguru import logger


router = APIRouter(prefix="/v1")


@router.get("/reports/{reportName}/run")
async def run_report(
    request: Request,
    reportName: str,
    fromDate: str | None = None,
    toDate: str | None = None,
    format: str = "JSON",
):
    """
    Run reports: loanPortfolio, delinquency
    """
    if reportName not in ["loanPortfolio", "delinquency"]:
        raise HTTPException(status_code=400, detail={"code": "INVALID_REPORT"})

    async with SessionLocal() as session:
        if reportName == "loanPortfolio":
            query = select(Loan).order_by(Loan.created_on.desc())

            if fromDate:
                query = query.where(Loan.created_on >= fromDate)
            if toDate:
                query = query.where(Loan.created_on <= toDate)

            rows = (await session.execute(query)).scalars().all()

            data = [
                {
                    "id": loan.id,
                    "clientId": loan.client_id,
                    "principal": float(loan.principal),
                    "status": loan.status,
                    "disbursedOn": loan.disbursed_on.isoformat() if loan.disbursed_on else None
                }
                for loan in rows
            ]

        elif reportName == "delinquency":
            query = select(DelinquencyStatus).join(Loan)
            rows = (await session.execute(query)).scalars().all()

            data = [
                {
                    "loanId": ds.loan_id,
                    "daysPastDue": ds.days_past_due,
                    "bucketId": ds.current_bucket_id,
                    "asOfDate": ds.as_of_date.isoformat()
                }
                for ds in rows
            ]

        else:
            data = []

        logger.bind(
            route=f"/reports/{reportName}/run",
            method="GET",
            format=format,
            correlationId=getattr(request.state, "correlation_id", None)
        ).info(f"ran report: {reportName}")

        if format == "CSV":
            # Convert to CSV
            output = io.StringIO()
            if data:
                writer = csv.DictWriter(output, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)

            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={reportName}.csv"}
            )
        else:
            return data
