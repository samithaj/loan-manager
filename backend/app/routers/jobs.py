from __future__ import annotations

import uuid
import csv
import io
import json
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ..db import SessionLocal
from ..models.job import Job
from ..models.client import Client
from ..models.loan import Loan
from ..models.loan_product import LoanProduct


router = APIRouter(prefix="/v1", tags=["jobs"])


class JobOut(BaseModel):
    id: str
    type: str
    status: str
    createdOn: str
    startedOn: Optional[str] = None
    completedOn: Optional[str] = None
    totalRecords: Optional[int] = None
    processedRecords: Optional[int] = None
    successCount: Optional[int] = None
    errorCount: Optional[int] = None
    errorDetails: Optional[str] = None  # JSON string
    resultData: Optional[str] = None  # JSON string


@router.post("/bulk/clients", status_code=status.HTTP_202_ACCEPTED)
async def bulk_upload_clients(file: UploadFile = File(...)):
    """Bulk upload clients from CSV"""
    if not file.filename or not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    async with SessionLocal() as session:  # type: AsyncSession
        # Create job record
        job = Job(
            id=str(uuid.uuid4()),
            type="BULK_CLIENTS",
            status="PENDING",
            created_on=datetime.utcnow()
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)
        
        # Process CSV in background (simplified - in production use Celery/RQ)
        try:
            job.status = "RUNNING"
            job.started_on = datetime.utcnow()
            
            content = await file.read()
            csv_content = content.decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            
            total_records = 0
            success_count = 0
            error_count = 0
            errors = []
            
            for row_num, row in enumerate(csv_reader, 1):
                total_records += 1
                try:
                    # Validate required fields
                    if not row.get('displayName'):
                        raise ValueError("displayName is required")
                    
                    client = Client(
                        id=row.get('id') or f"C{uuid.uuid4()}",
                        display_name=row['displayName'],
                        mobile=row.get('mobile'),
                        national_id=row.get('nationalId'),
                        address=row.get('address')
                    )
                    session.add(client)
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    errors.append({
                        "row": row_num,
                        "data": row,
                        "error": str(e)
                    })
            
            job.total_records = total_records
            job.processed_records = total_records
            job.success_count = success_count
            job.error_count = error_count
            job.error_details = json.dumps(errors) if errors else None
            job.status = "SUCCEEDED" if error_count == 0 else "FAILED"
            job.completed_on = datetime.utcnow()
            
            await session.commit()
            
        except Exception as e:
            job.status = "FAILED"
            job.error_details = json.dumps([{"error": str(e)}])
            job.completed_on = datetime.utcnow()
            await session.commit()
        
        return {"jobId": job.id, "status": job.status}


@router.post("/bulk/loans", status_code=status.HTTP_202_ACCEPTED)
async def bulk_upload_loans(file: UploadFile = File(...)):
    """Bulk upload loans from CSV"""
    if not file.filename or not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    async with SessionLocal() as session:  # type: AsyncSession
        # Create job record
        job = Job(
            id=str(uuid.uuid4()),
            type="BULK_LOANS",
            status="PENDING",
            created_on=datetime.utcnow()
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)
        
        # Process CSV in background (simplified)
        try:
            job.status = "RUNNING"
            job.started_on = datetime.utcnow()
            
            content = await file.read()
            csv_content = content.decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            
            total_records = 0
            success_count = 0
            error_count = 0
            errors = []
            
            for row_num, row in enumerate(csv_reader, 1):
                total_records += 1
                try:
                    # Validate required fields
                    required_fields = ['clientId', 'productId', 'principal']
                    for field in required_fields:
                        if not row.get(field):
                            raise ValueError(f"{field} is required")
                    
                    # Validate client exists
                    client_result = await session.execute(select(Client).where(Client.id == row['clientId']))
                    if not client_result.scalar_one_or_none():
                        raise ValueError(f"Client {row['clientId']} not found")
                    
                    # Validate product exists
                    product_result = await session.execute(select(LoanProduct).where(LoanProduct.id == row['productId']))
                    product = product_result.scalar_one_or_none()
                    if not product:
                        raise ValueError(f"Loan product {row['productId']} not found")
                    
                    loan = Loan(
                        id=row.get('id') or f"L{uuid.uuid4()}",
                        client_id=row['clientId'],
                        product_id=row['productId'],
                        principal=float(row['principal']),
                        interest_rate=float(row.get('interestRate', product.interest_rate)),
                        term_months=int(row.get('termMonths', product.term_months)),
                        status="PENDING",
                        created_on=datetime.utcnow()
                    )
                    session.add(loan)
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    errors.append({
                        "row": row_num,
                        "data": row,
                        "error": str(e)
                    })
            
            job.total_records = total_records
            job.processed_records = total_records
            job.success_count = success_count
            job.error_count = error_count
            job.error_details = json.dumps(errors) if errors else None
            job.status = "SUCCEEDED" if error_count == 0 else "FAILED"
            job.completed_on = datetime.utcnow()
            
            await session.commit()
            
        except Exception as e:
            job.status = "FAILED"
            job.error_details = json.dumps([{"error": str(e)}])
            job.completed_on = datetime.utcnow()
            await session.commit()
        
        return {"jobId": job.id, "status": job.status}


@router.get("/jobs/{job_id}", response_model=JobOut)
async def get_job_status(job_id: str):
    """Get job status"""
    async with SessionLocal() as session:  # type: AsyncSession
        result = await session.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return JobOut(
            id=job.id,
            type=job.type,
            status=job.status,
            createdOn=job.created_on.isoformat(),
            startedOn=job.started_on.isoformat() if job.started_on else None,
            completedOn=job.completed_on.isoformat() if job.completed_on else None,
            totalRecords=job.total_records,
            processedRecords=job.processed_records,
            successCount=job.success_count,
            errorCount=job.error_count,
            errorDetails=job.error_details,
            resultData=job.result_data
        )


@router.get("/jobs", response_model=list[JobOut])
async def list_jobs(
    skip: int = 0,
    limit: int = 100,
    job_type: Optional[str] = None
):
    """List jobs"""
    async with SessionLocal() as session:  # type: AsyncSession
        stmt = select(Job).order_by(Job.created_on.desc()).offset(skip).limit(limit)
        
        if job_type:
            stmt = stmt.where(Job.type == job_type)
        
        result = await session.execute(stmt)
        jobs = result.scalars().all()
        
        return [
            JobOut(
                id=job.id,
                type=job.type,
                status=job.status,
                createdOn=job.created_on.isoformat(),
                startedOn=job.started_on.isoformat() if job.started_on else None,
                completedOn=job.completed_on.isoformat() if job.completed_on else None,
                totalRecords=job.total_records,
                processedRecords=job.processed_records,
                successCount=job.success_count,
                errorCount=job.error_count,
                errorDetails=job.error_details,
                resultData=job.result_data
            )
            for job in jobs
        ]