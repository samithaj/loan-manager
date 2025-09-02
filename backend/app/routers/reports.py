from __future__ import annotations

import csv
import io
from datetime import date, datetime
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Response
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ..db import SessionLocal
from ..models.loan import Loan, DelinquencyStatus, DelinquencyBucket
from ..models.client import Client


router = APIRouter(prefix="/v1", tags=["reports"])


@router.get("/reports/loan-portfolio/run")
async def run_loan_portfolio_report(
    format: str = Query("JSON", regex="^(JSON|CSV)$"),
    status: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None)
):
    """Generate loan portfolio report"""
    async with SessionLocal() as session:  # type: AsyncSession
        stmt = select(Loan).join(Client)
        
        # Apply filters
        if status:
            stmt = stmt.where(Loan.status == status)
        if from_date:
            try:
                from_dt = datetime.fromisoformat(from_date).date()
                stmt = stmt.where(Loan.created_on >= from_dt)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid from_date format")
        if to_date:
            try:
                to_dt = datetime.fromisoformat(to_date).date()
                stmt = stmt.where(Loan.created_on <= to_dt)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid to_date format")
        
        result = await session.execute(stmt)
        loans = result.scalars().all()
        
        # Prepare report data
        report_data = []
        for loan in loans:
            report_data.append({
                "loanId": loan.id,
                "clientId": loan.client_id,
                "productId": loan.product_id,
                "principal": float(loan.principal),
                "interestRate": float(loan.interest_rate) if loan.interest_rate else None,
                "termMonths": loan.term_months,
                "status": loan.status,
                "disbursedOn": loan.disbursed_on.isoformat() if loan.disbursed_on else None,
                "createdOn": loan.created_on.isoformat()
            })
        
        if format == "CSV":
            # Generate CSV
            output = io.StringIO()
            if report_data:
                writer = csv.DictWriter(output, fieldnames=report_data[0].keys())
                writer.writeheader()
                writer.writerows(report_data)
            
            csv_content = output.getvalue()
            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=loan_portfolio_{date.today().isoformat()}.csv"}
            )
        else:
            return {
                "reportType": "loanPortfolio",
                "generatedOn": datetime.utcnow().isoformat(),
                "filters": {
                    "status": status,
                    "fromDate": from_date,
                    "toDate": to_date
                },
                "totalLoans": len(report_data),
                "data": report_data
            }


@router.get("/reports/delinquency/run")
async def run_delinquency_report(
    format: str = Query("JSON", regex="^(JSON|CSV)$"),
    bucket_id: Optional[str] = Query(None)
):
    """Generate delinquency report"""
    async with SessionLocal() as session:  # type: AsyncSession
        stmt = (
            select(DelinquencyStatus, DelinquencyBucket, Loan, Client)
            .join(DelinquencyBucket, DelinquencyStatus.current_bucket_id == DelinquencyBucket.id)
            .join(Loan, DelinquencyStatus.loan_id == Loan.id)
            .join(Client, Loan.client_id == Client.id)
        )
        
        if bucket_id:
            stmt = stmt.where(DelinquencyStatus.current_bucket_id == bucket_id)
        
        result = await session.execute(stmt)
        rows = result.all()
        
        # Prepare report data
        report_data = []
        for status, bucket, loan, client in rows:
            report_data.append({
                "loanId": loan.id,
                "clientId": client.id,
                "clientName": client.display_name,
                "principal": float(loan.principal),
                "status": loan.status,
                "bucketId": bucket.id,
                "bucketName": bucket.name,
                "daysPastDue": status.days_past_due,
                "asOfDate": status.as_of_date.isoformat()
            })
        
        if format == "CSV":
            # Generate CSV
            output = io.StringIO()
            if report_data:
                writer = csv.DictWriter(output, fieldnames=report_data[0].keys())
                writer.writeheader()
                writer.writerows(report_data)
            
            csv_content = output.getvalue()
            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=delinquency_report_{date.today().isoformat()}.csv"}
            )
        else:
            return {
                "reportType": "delinquency",
                "generatedOn": datetime.utcnow().isoformat(),
                "filters": {
                    "bucketId": bucket_id
                },
                "totalLoans": len(report_data),
                "data": report_data
            }