"""Admin endpoints for system management."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..db import SessionLocal
from ..rbac import require_permission
from ..services import materialized_view_service
from loguru import logger


router = APIRouter(prefix="/v1/admin", tags=["admin"])


class RefreshViewRequest(BaseModel):
    """Request to refresh a materialized view."""

    view_name: str = Field(..., description="Name of the materialized view to refresh")
    concurrently: bool = Field(
        default=True,
        description="Whether to refresh concurrently (allows reads during refresh)"
    )


class RefreshViewResponse(BaseModel):
    """Response from materialized view refresh."""

    view_name: str
    status: str
    duration_seconds: float
    refreshed_at: str


class RefreshAllViewsResponse(BaseModel):
    """Response from refreshing all views."""

    total_duration_seconds: float
    refreshed_at: str
    success_count: int
    error_count: int
    results: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]


class ViewStatsResponse(BaseModel):
    """Statistics about a materialized view."""

    view_name: str
    row_count: Optional[int] = None
    size: Optional[str] = None
    last_vacuum: Optional[str] = None
    last_analyze: Optional[str] = None
    error: Optional[str] = None


@router.post("/refresh-view", response_model=RefreshViewResponse)
async def refresh_materialized_view(
    request: RefreshViewRequest,
    user: dict = Depends(require_permission("admin"))
) -> RefreshViewResponse:
    """
    Manually refresh a materialized view.

    **Permissions**: Requires admin role

    **Use Cases**:
    - Refresh data after bulk imports
    - Update reports after major data changes
    - Force refresh outside of scheduled time

    **Available Views**:
    - `mv_bike_cost_summary` - Bike cost aggregations
    - `mv_bike_lifecycle_events` - Bike lifecycle timeline
    """
    async with SessionLocal() as db:
        try:
            result = await materialized_view_service.refresh_materialized_view(
                db,
                request.view_name,
                request.concurrently
            )
            return RefreshViewResponse(**result)

        except Exception as e:
            logger.error(f"Failed to refresh view: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "code": "REFRESH_FAILED",
                    "message": f"Failed to refresh materialized view: {str(e)}"
                }
            )


@router.post("/refresh-all-views", response_model=RefreshAllViewsResponse)
async def refresh_all_views(
    concurrently: bool = True,
    user: dict = Depends(require_permission("admin"))
) -> RefreshAllViewsResponse:
    """
    Refresh all bike lifecycle materialized views.

    **Permissions**: Requires admin role

    **This refreshes**:
    - mv_bike_cost_summary
    - mv_bike_lifecycle_events

    **Recommended**: Run this nightly via cron job
    """
    async with SessionLocal() as db:
        try:
            result = await materialized_view_service.refresh_all_bike_lifecycle_views(
                db,
                concurrently
            )
            return RefreshAllViewsResponse(**result)

        except Exception as e:
            logger.error(f"Failed to refresh all views: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "code": "REFRESH_ALL_FAILED",
                    "message": f"Failed to refresh all views: {str(e)}"
                }
            )


@router.get("/view-stats/{view_name}", response_model=ViewStatsResponse)
async def get_view_statistics(
    view_name: str,
    user: dict = Depends(require_permission("admin"))
) -> ViewStatsResponse:
    """
    Get statistics about a materialized view.

    **Permissions**: Requires admin role

    Returns row count, size, and last refresh time.
    """
    async with SessionLocal() as db:
        try:
            result = await materialized_view_service.get_materialized_view_stats(
                db,
                view_name
            )
            return ViewStatsResponse(**result)

        except Exception as e:
            logger.error(f"Failed to get view stats: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "code": "STATS_FAILED",
                    "message": f"Failed to get view statistics: {str(e)}"
                }
            )


@router.get("/health")
async def admin_health_check(
    user: dict = Depends(require_permission("admin"))
) -> Dict[str, Any]:
    """
    Admin health check endpoint.

    **Permissions**: Requires admin role

    Returns system status and statistics.
    """
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "user": user.get("username"),
        "message": "Admin endpoints are operational"
    }
