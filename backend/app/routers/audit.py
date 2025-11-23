"""Audit trail endpoints"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from ..db import get_db
from ..rbac import require_permission
from ..services.audit_service import AuditService
from ..models.audit_log import AuditLog

router = APIRouter(prefix="/v1/audit", tags=["Audit Trail"])


class AuditLogResponse(BaseModel):
    """Audit log response model"""
    id: str
    entity_type: str
    entity_id: str
    action: str
    username: str
    user_id: Optional[str]
    user_role: Optional[str]
    timestamp: datetime
    old_values: Optional[dict]
    new_values: Optional[dict]
    changes_summary: Optional[str]
    ip_address: Optional[str]
    metadata: Optional[dict]

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """Paginated audit log response"""
    items: list[AuditLogResponse]
    total: int
    limit: int
    offset: int


@router.get(
    "/logs",
    response_model=AuditLogListResponse,
    dependencies=[Depends(require_permission("audit:view"))],
)
async def get_audit_logs(
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    username: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Get audit logs with filters"""
    from_date = datetime.fromisoformat(date_from) if date_from else None
    to_date = datetime.fromisoformat(date_to) if date_to else None

    logs, total = await AuditService.search_audit_logs(
        db=db,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        username=username,
        date_from=from_date,
        date_to=to_date,
        limit=limit,
        offset=offset,
    )

    return AuditLogListResponse(
        items=[AuditLogResponse.model_validate(log) for log in logs],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/entity/{entity_type}/{entity_id}",
    response_model=list[AuditLogResponse],
    dependencies=[Depends(require_permission("audit:view"))],
)
async def get_entity_history(
    entity_type: str,
    entity_id: str,
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
):
    """Get audit history for a specific entity"""
    logs = await AuditService.get_entity_history(
        db=db,
        entity_type=entity_type,
        entity_id=entity_id,
        limit=limit,
    )

    return [AuditLogResponse.model_validate(log) for log in logs]


@router.get(
    "/user/{username}",
    response_model=list[AuditLogResponse],
    dependencies=[Depends(require_permission("audit:view"))],
)
async def get_user_activity(
    username: str,
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
):
    """Get audit logs for a specific user"""
    from_date = datetime.fromisoformat(date_from) if date_from else None
    to_date = datetime.fromisoformat(date_to) if date_to else None

    logs = await AuditService.get_user_activity(
        db=db,
        username=username,
        date_from=from_date,
        date_to=to_date,
        limit=limit,
    )

    return [AuditLogResponse.model_validate(log) for log in logs]


@router.get(
    "/recent",
    response_model=list[AuditLogResponse],
    dependencies=[Depends(require_permission("audit:view"))],
)
async def get_recent_activity(
    entity_type: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Get recent audit activity"""
    logs = await AuditService.get_recent_activity(
        db=db,
        entity_type=entity_type,
        action=action,
        limit=limit,
    )

    return [AuditLogResponse.model_validate(log) for log in logs]
