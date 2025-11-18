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
from app.models.bicycle import Bicycle
from app.models.bicycle_application import BicycleApplication
from loguru import logger


router = APIRouter(prefix="/v1")


@router.get("/reports/{reportName}/run")
async def run_report(
    request: Request,
    reportName: str,
    fromDate: str | None = None,
    toDate: str | None = None,
    format: str = "JSON",
    branchId: str | None = None,
):
    """
    Run reports: loanPortfolio, delinquency, bicycleInventory, applicationFunnel, branchPerformance
    """
    valid_reports = ["loanPortfolio", "delinquency", "bicycleInventory", "applicationFunnel", "branchPerformance"]
    if reportName not in valid_reports:
        raise HTTPException(status_code=400, detail={"code": "INVALID_REPORT", "message": f"Valid reports: {', '.join(valid_reports)}"})

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

        elif reportName == "bicycleInventory":
            from sqlalchemy import func as sql_func

            query = select(
                Bicycle.branch_id,
                Bicycle.status,
                Bicycle.condition,
                sql_func.count(Bicycle.id).label("count"),
                sql_func.sum(Bicycle.cash_price).label("total_value")
            ).group_by(Bicycle.branch_id, Bicycle.status, Bicycle.condition)

            if branchId:
                query = query.where(Bicycle.branch_id == branchId)

            rows = (await session.execute(query)).all()

            data = [
                {
                    "branchId": row.branch_id,
                    "status": row.status,
                    "condition": row.condition,
                    "count": row.count,
                    "totalValue": float(row.total_value) if row.total_value else 0
                }
                for row in rows
            ]

        elif reportName == "applicationFunnel":
            from sqlalchemy import func as sql_func

            query = select(
                BicycleApplication.status,
                sql_func.count(BicycleApplication.id).label("count")
            ).group_by(BicycleApplication.status)

            if branchId:
                query = query.where(BicycleApplication.branch_id == branchId)

            if fromDate:
                query = query.where(BicycleApplication.submitted_at >= fromDate)
            if toDate:
                query = query.where(BicycleApplication.submitted_at <= toDate)

            rows = (await session.execute(query)).all()

            total = sum(row.count for row in rows)
            data = [
                {
                    "status": row.status,
                    "count": row.count,
                    "percentage": round((row.count / total * 100), 2) if total > 0 else 0
                }
                for row in rows
            ]

        elif reportName == "branchPerformance":
            from sqlalchemy import func as sql_func

            # Get application counts and conversion rates per branch
            app_query = select(
                BicycleApplication.branch_id,
                sql_func.count(BicycleApplication.id).label("total_applications"),
                sql_func.sum(sql_func.case((BicycleApplication.status == "CONVERTED_TO_LOAN", 1), else_=0)).label("conversions")
            ).group_by(BicycleApplication.branch_id)

            if fromDate:
                app_query = app_query.where(BicycleApplication.submitted_at >= fromDate)
            if toDate:
                app_query = app_query.where(BicycleApplication.submitted_at <= toDate)

            if branchId:
                app_query = app_query.where(BicycleApplication.branch_id == branchId)

            app_rows = (await session.execute(app_query)).all()

            data = [
                {
                    "branchId": row.branch_id,
                    "totalApplications": row.total_applications,
                    "conversions": row.conversions,
                    "conversionRate": round((row.conversions / row.total_applications * 100), 2) if row.total_applications > 0 else 0
                }
                for row in app_rows
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
