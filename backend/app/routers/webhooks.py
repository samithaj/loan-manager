from __future__ import annotations

import uuid
import secrets
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ..db import SessionLocal
from ..models.webhook import WebhookEndpoint, WebhookDelivery


router = APIRouter(prefix="/v1", tags=["webhooks"])


class WebhookEndpointOut(BaseModel):
    id: str
    url: str
    events: list[str]
    active: bool
    createdOn: str


class WebhookEndpointIn(BaseModel):
    id: Optional[str] = None
    url: str
    events: list[str]  # e.g., ["loan.approved", "loan.disbursed"]


class WebhookDeliveryOut(BaseModel):
    id: str
    endpointId: str
    eventType: str
    status: str
    attempts: int
    lastAttempt: Optional[str] = None
    responseStatus: Optional[int] = None
    createdOn: str


@router.get("/webhooks/endpoints", response_model=list[WebhookEndpointOut])
async def list_webhook_endpoints():
    """List webhook endpoints"""
    async with SessionLocal() as session:  # type: AsyncSession
        result = await session.execute(
            select(WebhookEndpoint).order_by(WebhookEndpoint.created_on.desc())
        )
        endpoints = result.scalars().all()
        
        return [
            WebhookEndpointOut(
                id=endpoint.id,
                url=endpoint.url,
                events=endpoint.events.split(","),
                active=endpoint.active,
                createdOn=endpoint.created_on.isoformat()
            )
            for endpoint in endpoints
        ]


@router.post("/webhooks/endpoints", response_model=WebhookEndpointOut)
async def create_webhook_endpoint(endpoint_data: WebhookEndpointIn):
    """Register a webhook endpoint"""
    async with SessionLocal() as session:  # type: AsyncSession
        endpoint = WebhookEndpoint(
            id=endpoint_data.id or str(uuid.uuid4()),
            url=endpoint_data.url,
            secret=secrets.token_urlsafe(32),  # Generate secret for HMAC
            events=",".join(endpoint_data.events),
            active=True,
            created_on=datetime.utcnow()
        )
        
        session.add(endpoint)
        await session.commit()
        await session.refresh(endpoint)
        
        return WebhookEndpointOut(
            id=endpoint.id,
            url=endpoint.url,
            events=endpoint.events.split(","),
            active=endpoint.active,
            createdOn=endpoint.created_on.isoformat()
        )


@router.delete("/webhooks/endpoints/{endpoint_id}")
async def delete_webhook_endpoint(endpoint_id: str):
    """Delete a webhook endpoint"""
    async with SessionLocal() as session:  # type: AsyncSession
        result = await session.execute(select(WebhookEndpoint).where(WebhookEndpoint.id == endpoint_id))
        endpoint = result.scalar_one_or_none()
        
        if not endpoint:
            raise HTTPException(status_code=404, detail="Webhook endpoint not found")
        
        await session.delete(endpoint)
        await session.commit()
        
        return {"message": "Webhook endpoint deleted"}


@router.get("/webhooks/deliveries", response_model=list[WebhookDeliveryOut])
async def list_webhook_deliveries(
    endpoint_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    """List webhook deliveries"""
    async with SessionLocal() as session:  # type: AsyncSession
        stmt = select(WebhookDelivery).order_by(WebhookDelivery.created_on.desc()).offset(skip).limit(limit)
        
        if endpoint_id:
            stmt = stmt.where(WebhookDelivery.endpoint_id == endpoint_id)
        
        result = await session.execute(stmt)
        deliveries = result.scalars().all()
        
        return [
            WebhookDeliveryOut(
                id=delivery.id,
                endpointId=delivery.endpoint_id,
                eventType=delivery.event_type,
                status=delivery.status,
                attempts=delivery.attempts,
                lastAttempt=delivery.last_attempt.isoformat() if delivery.last_attempt else None,
                responseStatus=delivery.response_status,
                createdOn=delivery.created_on.isoformat()
            )
            for delivery in deliveries
        ]


# Note: In production, webhook delivery would be handled by a background worker
# using the outbox pattern for reliability