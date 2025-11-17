from __future__ import annotations

import time
import csv
import io
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, HTTPException, status, Request, UploadFile, File
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import SessionLocal
from app.models.client import Client
from app.models.loan import Loan
from loguru import logger


router = APIRouter(prefix="/v1")


# Pydantic models
class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class JobResponse(BaseModel):
    jobId: str


class JobStatusOut(BaseModel):
    id: str
    name: str
    status: JobStatus
    startedAt: str | None
    finishedAt: str | None
    stats: dict


# In-memory job storage (in production, use a proper job queue like Celery/RQ)
JOBS = {}


def generate_job_id() -> str:
    return f"JOB-{int(time.time() * 1000)}"


def create_job(name: str) -> str:
    job_id = generate_job_id()
    JOBS[job_id] = {
        "id": job_id,
        "name": name,
        "status": JobStatus.QUEUED,
        "startedAt": None,
        "finishedAt": None,
        "stats": {}
    }
    return job_id


async def process_bulk_clients(file_content: str) -> dict:
    """Process bulk client CSV upload"""
    stats = {"total": 0, "success": 0, "failed": 0, "errors": []}

    try:
        csv_reader = csv.DictReader(io.StringIO(file_content))
        async with SessionLocal() as session:
            for row in csv_reader:
                stats["total"] += 1
                try:
                    client_id = f"CL-{int(time.time() * 1000)}-{stats['total']}"
                    client = Client(
                        id=client_id,
                        display_name=row.get("displayName", ""),
                        mobile=row.get("mobile"),
                        national_id=row.get("nationalId"),
                        address=row.get("address")
                    )
                    session.add(client)
                    stats["success"] += 1
                except Exception as e:
                    stats["failed"] += 1
                    stats["errors"].append({"row": stats["total"], "error": str(e)})

            await session.commit()
    except Exception as e:
        stats["errors"].append({"error": f"CSV parsing error: {str(e)}"})

    return stats


async def process_bulk_loans(file_content: str) -> dict:
    """Process bulk loan CSV upload"""
    stats = {"total": 0, "success": 0, "failed": 0, "errors": []}

    try:
        csv_reader = csv.DictReader(io.StringIO(file_content))
        async with SessionLocal() as session:
            for row in csv_reader:
                stats["total"] += 1
                try:
                    loan_id = f"LN-{int(time.time() * 1000)}-{stats['total']}"
                    loan = Loan(
                        id=loan_id,
                        client_id=row.get("clientId", ""),
                        product_id=row.get("productId", ""),
                        principal=float(row.get("principal", 0)),
                        interest_rate=float(row.get("interestRate", 0)) if row.get("interestRate") else None,
                        term_months=int(row.get("termMonths", 0)),
                        status="PENDING",
                        disbursed_on=None
                    )
                    session.add(loan)
                    stats["success"] += 1
                except Exception as e:
                    stats["failed"] += 1
                    stats["errors"].append({"row": stats["total"], "error": str(e)})

            await session.commit()
    except Exception as e:
        stats["errors"].append({"error": f"CSV parsing error: {str(e)}"})

    return stats


# Bulk upload endpoints
@router.post("/bulk/clients", status_code=202, response_model=JobResponse)
async def bulk_upload_clients(request: Request, file: UploadFile = File(...)):
    content = await file.read()
    file_content = content.decode("utf-8")

    job_id = create_job("bulkClients")

    # Process synchronously for now (in production, use background tasks)
    JOBS[job_id]["status"] = JobStatus.RUNNING
    JOBS[job_id]["startedAt"] = datetime.utcnow().isoformat()

    stats = await process_bulk_clients(file_content)

    JOBS[job_id]["status"] = JobStatus.SUCCEEDED if stats["failed"] == 0 else JobStatus.FAILED
    JOBS[job_id]["finishedAt"] = datetime.utcnow().isoformat()
    JOBS[job_id]["stats"] = stats

    logger.bind(
        route="/bulk/clients",
        method="POST",
        jobId=job_id,
        correlationId=getattr(request.state, "correlation_id", None)
    ).info("bulk upload clients")

    return JobResponse(jobId=job_id)


@router.post("/bulk/loans", status_code=202, response_model=JobResponse)
async def bulk_upload_loans(request: Request, file: UploadFile = File(...)):
    content = await file.read()
    file_content = content.decode("utf-8")

    job_id = create_job("bulkLoans")

    # Process synchronously for now (in production, use background tasks)
    JOBS[job_id]["status"] = JobStatus.RUNNING
    JOBS[job_id]["startedAt"] = datetime.utcnow().isoformat()

    stats = await process_bulk_loans(file_content)

    JOBS[job_id]["status"] = JobStatus.SUCCEEDED if stats["failed"] == 0 else JobStatus.FAILED
    JOBS[job_id]["finishedAt"] = datetime.utcnow().isoformat()
    JOBS[job_id]["stats"] = stats

    logger.bind(
        route="/bulk/loans",
        method="POST",
        jobId=job_id,
        correlationId=getattr(request.state, "correlation_id", None)
    ).info("bulk upload loans")

    return JobResponse(jobId=job_id)


# Job management endpoints
@router.post("/jobs/{jobName}:run", status_code=202, response_model=JobResponse)
async def run_job(request: Request, jobName: str):
    """Run batch jobs: loanCOB, delinquencyClassification"""
    job_id = create_job(jobName)

    JOBS[job_id]["status"] = JobStatus.RUNNING
    JOBS[job_id]["startedAt"] = datetime.utcnow().isoformat()

    # Placeholder for actual job logic
    # In production, these would be proper background tasks
    if jobName == "loanCOB":
        # Close of business processing
        JOBS[job_id]["stats"] = {"processed": 0}
    elif jobName == "delinquencyClassification":
        # Delinquency classification
        JOBS[job_id]["stats"] = {"classified": 0}

    JOBS[job_id]["status"] = JobStatus.SUCCEEDED
    JOBS[job_id]["finishedAt"] = datetime.utcnow().isoformat()

    logger.bind(
        route=f"/jobs/{jobName}:run",
        method="POST",
        jobId=job_id,
        correlationId=getattr(request.state, "correlation_id", None)
    ).info(f"ran job: {jobName}")

    return JobResponse(jobId=job_id)


@router.get("/jobs/{jobId}", response_model=JobStatusOut)
async def get_job_status(request: Request, jobId: str):
    if jobId not in JOBS:
        raise HTTPException(status_code=404, detail={"code": "JOB_NOT_FOUND"})

    job = JOBS[jobId]

    return JobStatusOut(
        id=job["id"],
        name=job["name"],
        status=job["status"],
        startedAt=job["startedAt"],
        finishedAt=job["finishedAt"],
        stats=job["stats"]
    )
