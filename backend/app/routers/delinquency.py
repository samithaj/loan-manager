from __future__ import annotations

import uuid
from datetime import datetime, date
from typing import Optional
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ..db import SessionLocal
from ..models.loan import DelinquencyBucket, DelinquencyStatus, Loan


router = APIRouter(prefix="/v1", tags=["delinquency"])


class DelinquencyBucketOut(BaseModel):
    id: str
    name: str
    minDays: int
    maxDays: int


class DelinquencyBucketIn(BaseModel):
    id: Optional[str] = None
    name: str
    minDays: int
    maxDays: int


class DelinquencyStatusOut(BaseModel):
    loanId: str
    currentBucketId: str
    daysPastDue: int
    asOfDate: str  # ISO date string


@router.get("/delinquency/buckets", response_model=list[DelinquencyBucketOut])
async def list_delinquency_buckets():
    """List delinquency buckets"""
    async with SessionLocal() as session:  # type: AsyncSession
        result = await session.execute(
            select(DelinquencyBucket).order_by(DelinquencyBucket.min_days)
        )
        buckets = result.scalars().all()
        
        return [
            DelinquencyBucketOut(
                id=bucket.id,
                name=bucket.name,
                minDays=bucket.min_days,
                maxDays=bucket.max_days
            )
            for bucket in buckets
        ]


@router.post("/delinquency/buckets", response_model=DelinquencyBucketOut)
async def create_delinquency_bucket(bucket_data: DelinquencyBucketIn):
    """Create a delinquency bucket"""
    async with SessionLocal() as session:  # type: AsyncSession
        bucket = DelinquencyBucket(
            id=bucket_data.id or str(uuid.uuid4()),
            name=bucket_data.name,
            min_days=bucket_data.minDays,
            max_days=bucket_data.maxDays
        )
        
        session.add(bucket)
        await session.commit()
        await session.refresh(bucket)
        
        return DelinquencyBucketOut(
            id=bucket.id,
            name=bucket.name,
            minDays=bucket.min_days,
            maxDays=bucket.max_days
        )


@router.get("/delinquency/status", response_model=list[DelinquencyStatusOut])
async def list_delinquency_status():
    """List current delinquency status for all loans"""
    async with SessionLocal() as session:  # type: AsyncSession
        result = await session.execute(
            select(DelinquencyStatus).order_by(DelinquencyStatus.days_past_due.desc())
        )
        statuses = result.scalars().all()
        
        return [
            DelinquencyStatusOut(
                loanId=status.loan_id,
                currentBucketId=status.current_bucket_id,
                daysPastDue=status.days_past_due,
                asOfDate=status.as_of_date.isoformat()
            )
            for status in statuses
        ]


@router.post("/jobs/delinquency-classification")
async def run_delinquency_classification():
    """Run daily delinquency classification job"""
    async with SessionLocal() as session:  # type: AsyncSession
        # Create job record
        job_id = str(uuid.uuid4())
        
        # Simplified delinquency classification
        # In production, this would be a proper background job
        
        # Get all disbursed loans
        loans_result = await session.execute(
            select(Loan).where(Loan.status == "DISBURSED")
        )
        loans = loans_result.scalars().all()
        
        # Get buckets
        buckets_result = await session.execute(
            select(DelinquencyBucket).order_by(DelinquencyBucket.min_days)
        )
        buckets = buckets_result.scalars().all()
        
        if not buckets:
            # Create default buckets if none exist
            default_buckets = [
                DelinquencyBucket(id="CURRENT", name="Current", min_days=0, max_days=0),
                DelinquencyBucket(id="DPD_1_30", name="1-30 Days", min_days=1, max_days=30),
                DelinquencyBucket(id="DPD_31_60", name="31-60 Days", min_days=31, max_days=60),
                DelinquencyBucket(id="DPD_61_90", name="61-90 Days", min_days=61, max_days=90),
                DelinquencyBucket(id="DPD_90_PLUS", name="90+ Days", min_days=91, max_days=9999)
            ]
            for bucket in default_buckets:
                session.add(bucket)
            await session.commit()
            buckets = default_buckets
        
        processed_count = 0
        today = date.today()
        
        for loan in loans:
            if not loan.disbursed_on:
                continue
                
            # Calculate days past due (simplified - should consider payment schedule)
            days_since_disbursement = (today - loan.disbursed_on).days
            days_past_due = max(0, days_since_disbursement - 30)  # Simplified: assume 30-day grace period
            
            # Find appropriate bucket
            bucket_id = "CURRENT"
            for bucket in buckets:
                if bucket.min_days <= days_past_due <= bucket.max_days:
                    bucket_id = bucket.id
                    break
            
            # Update or create delinquency status
            status_result = await session.execute(
                select(DelinquencyStatus).where(DelinquencyStatus.loan_id == loan.id)
            )
            status = status_result.scalar_one_or_none()
            
            if status:
                status.current_bucket_id = bucket_id
                status.days_past_due = days_past_due
                status.as_of_date = today
            else:
                status = DelinquencyStatus(
                    loan_id=loan.id,
                    current_bucket_id=bucket_id,
                    days_past_due=days_past_due,
                    as_of_date=today
                )
                session.add(status)
            
            processed_count += 1
        
        await session.commit()
        
        return {
            "jobId": job_id,
            "status": "SUCCEEDED",
            "processedLoans": processed_count,
            "asOfDate": today.isoformat()
        }