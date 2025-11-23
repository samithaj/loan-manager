"""Analytics and KPI endpoints"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import Optional

from ..db import get_db
from ..rbac import require_permission
from ..services.analytics_service import AnalyticsService

router = APIRouter(prefix="/v1/analytics", tags=["Analytics"])


@router.get(
    "/executive-dashboard",
    dependencies=[Depends(require_permission("reports:view"))],
)
async def get_executive_dashboard_kpis(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get executive dashboard KPIs"""
    from_date = datetime.fromisoformat(date_from) if date_from else None
    to_date = datetime.fromisoformat(date_to) if date_to else None

    kpis = await AnalyticsService.get_executive_dashboard_kpis(db, from_date, to_date)
    return kpis


@router.get(
    "/sales",
    dependencies=[Depends(require_permission("reports:view"))],
)
async def get_sales_analytics(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    branch_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get sales analytics data"""
    from_date = datetime.fromisoformat(date_from) if date_from else None
    to_date = datetime.fromisoformat(date_to) if date_to else None

    analytics = await AnalyticsService.get_sales_analytics(db, from_date, to_date, branch_id)
    return analytics


@router.get(
    "/commissions",
    dependencies=[Depends(require_permission("view:commission_rules"))],
)
async def get_commission_analytics(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get commission analytics"""
    from_date = datetime.fromisoformat(date_from) if date_from else None
    to_date = datetime.fromisoformat(date_to) if date_to else None

    analytics = await AnalyticsService.get_commission_analytics(db, from_date, to_date)
    return analytics


@router.get(
    "/accounting-summary",
    dependencies=[Depends(require_permission("view:chart_of_accounts"))],
)
async def get_accounting_summary(db: AsyncSession = Depends(get_db)):
    """Get accounting summary statistics"""
    summary = await AnalyticsService.get_accounting_summary(db)
    return summary


@router.get(
    "/trends/{metric}",
    dependencies=[Depends(require_permission("reports:view"))],
)
async def get_trend_data(
    metric: str,
    date_from: str = Query(...),
    date_to: str = Query(...),
    interval: str = Query("day"),
    db: AsyncSession = Depends(get_db),
):
    """Get trend data for charting"""
    from_date = datetime.fromisoformat(date_from)
    to_date = datetime.fromisoformat(date_to)

    trend_data = await AnalyticsService.get_trend_data(db, metric, from_date, to_date, interval)
    return trend_data
