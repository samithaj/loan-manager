from __future__ import annotations

import time
import hmac
import hashlib
import json
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy import select, Column, String, Boolean, DateTime, Integer, Text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column
from app.db import SessionLocal, Base
from loguru import logger


router = APIRouter(prefix="/v1")


# Models for webhooks (simple in-memory for now)
class WebhookModel(Base):
    __tablename__ = "webhooks"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    url: Mapped[str] = mapped_column(String, nullable=False)
    secret: Mapped[str] = mapped_column(String, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_on: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class WebhookDeliveryModel(Base):
    __tablename__ = "webhook_deliveries"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    webhook_id: Mapped[str] = mapped_column(String, nullable=False)
    event_id: Mapped[str] = mapped_column(String, nullable=False)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_response_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)


# Pydantic models
class WebhookCreate(BaseModel):
    url: str
    secret: str


class WebhookOut(BaseModel):
    id: str
    url: str
    active: bool
    createdOn: str


class WebhookDeliveryOut(BaseModel):
    id: str
    webhookId: str
    eventId: str
    eventType: str
    status: str
    attemptCount: int
    lastAttemptAt: str | None
    lastResponseStatus: int | None
    lastError: str | None


def generate_webhook_id() -> str:
    return f"WH-{int(time.time() * 1000)}"


def generate_delivery_id() -> str:
    return f"DEL-{int(time.time() * 1000)}"


@router.get("/webhooks", response_model=list[WebhookOut])
async def list_webhooks(request: Request):
    async with SessionLocal() as session:
        query = select(WebhookModel).order_by(WebhookModel.created_on.desc())
        rows = (await session.execute(query)).scalars().all()

        webhooks = [
            WebhookOut(
                id=w.id,
                url=w.url,
                active=w.active,
                createdOn=w.created_on.isoformat()
            )
            for w in rows
        ]

        logger.bind(
            route="/webhooks",
            method="GET",
            count=len(webhooks),
            correlationId=getattr(request.state, "correlation_id", None)
        ).info("list webhooks")

        return webhooks


@router.post("/webhooks", status_code=201, response_model=WebhookOut)
async def create_webhook(request: Request, payload: WebhookCreate):
    async with SessionLocal() as session:
        webhook_id = generate_webhook_id()

        webhook = WebhookModel(
            id=webhook_id,
            url=payload.url,
            secret=payload.secret,
            active=True
        )
        session.add(webhook)
        await session.commit()
        await session.refresh(webhook)

        logger.bind(
            route="/webhooks",
            method="POST",
            webhookId=webhook.id,
            correlationId=getattr(request.state, "correlation_id", None)
        ).info("created webhook")

        return WebhookOut(
            id=webhook.id,
            url=webhook.url,
            active=webhook.active,
            createdOn=webhook.created_on.isoformat()
        )


@router.delete("/webhooks/{id}", status_code=204)
async def delete_webhook(request: Request, id: str):
    async with SessionLocal() as session:
        webhook = await session.get(WebhookModel, id)
        if not webhook:
            raise HTTPException(status_code=404, detail={"code": "WEBHOOK_NOT_FOUND"})

        await session.delete(webhook)
        await session.commit()

        logger.bind(
            route=f"/webhooks/{id}",
            method="DELETE",
            correlationId=getattr(request.state, "correlation_id", None)
        ).info("deleted webhook")

        return None


@router.post("/webhooks/{id}:test", status_code=202)
async def test_webhook(request: Request, id: str):
    async with SessionLocal() as session:
        webhook = await session.get(WebhookModel, id)
        if not webhook:
            raise HTTPException(status_code=404, detail={"code": "WEBHOOK_NOT_FOUND"})

        # Send test event (placeholder)
        logger.bind(
            route=f"/webhooks/{id}:test",
            method="POST",
            correlationId=getattr(request.state, "correlation_id", None)
        ).info("test webhook")

        return {"message": "Test event enqueued"}


@router.get("/webhooks/deliveries")
async def list_webhook_deliveries(
    request: Request,
    webhookId: str | None = None,
    page: int = 1,
    pageSize: int = 25,
):
    async with SessionLocal() as session:
        query = select(WebhookDeliveryModel)

        if webhookId:
            query = query.where(WebhookDeliveryModel.webhook_id == webhookId)

        query = query.order_by(WebhookDeliveryModel.last_attempt_at.desc())

        # Get total count
        from sqlalchemy import func
        count_query = select(func.count()).select_from(query.subquery())
        total = (await session.execute(count_query)).scalar() or 0

        # Paginate
        query = query.offset((page - 1) * pageSize).limit(pageSize)
        rows = (await session.execute(query)).scalars().all()

        items = [
            WebhookDeliveryOut(
                id=d.id,
                webhookId=d.webhook_id,
                eventId=d.event_id,
                eventType=d.event_type,
                status=d.status,
                attemptCount=d.attempt_count,
                lastAttemptAt=d.last_attempt_at.isoformat() if d.last_attempt_at else None,
                lastResponseStatus=d.last_response_status,
                lastError=d.last_error
            )
            for d in rows
        ]

        logger.bind(
            route="/webhooks/deliveries",
            method="GET",
            count=len(items),
            correlationId=getattr(request.state, "correlation_id", None)
        ).info("list webhook deliveries")

        return {
            "items": items,
            "page": page,
            "pageSize": pageSize,
            "total": total
        }


@router.post("/webhooks/deliveries/{deliveryId}:redeliver", status_code=202)
async def redeliver_webhook(request: Request, deliveryId: str):
    async with SessionLocal() as session:
        delivery = await session.get(WebhookDeliveryModel, deliveryId)
        if not delivery:
            raise HTTPException(status_code=404, detail={"code": "DELIVERY_NOT_FOUND"})

        # Trigger redelivery (placeholder)
        logger.bind(
            route=f"/webhooks/deliveries/{deliveryId}:redeliver",
            method="POST",
            correlationId=getattr(request.state, "correlation_id", None)
        ).info("redelivery enqueued")

        return {"message": "Redelivery enqueued"}
