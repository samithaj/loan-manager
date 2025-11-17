from __future__ import annotations

import time
from datetime import date

from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import SessionLocal
from app.models.loan import DelinquencyBucket, DelinquencyStatus, Loan
from loguru import logger


router = APIRouter(prefix="/v1")


# Pydantic models
class DelinquencyBucketIn(BaseModel):
    id: str | None = None
    name: str
    minDays: int
    maxDays: int


class DelinquencyBucketOut(BaseModel):
    id: str
    name: str
    minDays: int
    maxDays: int


def generate_bucket_id() -> str:
    return f"DB-{int(time.time() * 1000)}"


@router.get("/delinquency-buckets", response_model=list[DelinquencyBucketOut])
async def list_delinquency_buckets(request: Request):
    async with SessionLocal() as session:
        query = select(DelinquencyBucket).order_by(DelinquencyBucket.min_days)
        rows = (await session.execute(query)).scalars().all()

        buckets = [
            DelinquencyBucketOut(
                id=b.id,
                name=b.name,
                minDays=b.min_days,
                maxDays=b.max_days
            )
            for b in rows
        ]

        logger.bind(
            route="/delinquency-buckets",
            method="GET",
            count=len(buckets),
            correlationId=getattr(request.state, "correlation_id", None)
        ).info("list delinquency buckets")

        return buckets


@router.post("/delinquency-buckets", status_code=201, response_model=DelinquencyBucketOut)
async def create_delinquency_bucket(request: Request, payload: DelinquencyBucketIn):
    async with SessionLocal() as session:
        bucket_id = payload.id or generate_bucket_id()

        bucket = DelinquencyBucket(
            id=bucket_id,
            name=payload.name,
            min_days=payload.minDays,
            max_days=payload.maxDays
        )
        session.add(bucket)
        await session.commit()
        await session.refresh(bucket)

        logger.bind(
            route="/delinquency-buckets",
            method="POST",
            bucketId=bucket.id,
            correlationId=getattr(request.state, "correlation_id", None)
        ).info("created delinquency bucket")

        return DelinquencyBucketOut(
            id=bucket.id,
            name=bucket.name,
            minDays=bucket.min_days,
            maxDays=bucket.max_days
        )
