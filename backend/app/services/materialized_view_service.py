"""Service for managing materialized view refreshes."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime
from loguru import logger
from typing import Dict, Any


async def refresh_materialized_view(
    db: AsyncSession,
    view_name: str,
    concurrently: bool = True
) -> Dict[str, Any]:
    """
    Refresh a specific materialized view.

    Args:
        db: Database session
        view_name: Name of the materialized view to refresh
        concurrently: Whether to refresh concurrently (allows reads during refresh)

    Returns:
        Dictionary with refresh results
    """
    start_time = datetime.utcnow()

    try:
        logger.info(f"Starting refresh of materialized view: {view_name}")

        # Build refresh command
        refresh_cmd = f"REFRESH MATERIALIZED VIEW {'CONCURRENTLY' if concurrently else ''} {view_name}"

        # Execute refresh
        await db.execute(text(refresh_cmd))
        await db.commit()

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        logger.info(f"Successfully refreshed {view_name} in {duration:.2f} seconds")

        return {
            "view_name": view_name,
            "status": "success",
            "duration_seconds": duration,
            "refreshed_at": end_time.isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to refresh materialized view {view_name}: {str(e)}")
        await db.rollback()
        raise


async def refresh_all_bike_lifecycle_views(
    db: AsyncSession,
    concurrently: bool = True
) -> Dict[str, Any]:
    """
    Refresh all bike lifecycle materialized views.

    Args:
        db: Database session
        concurrently: Whether to refresh concurrently

    Returns:
        Dictionary with refresh results for all views
    """
    start_time = datetime.utcnow()
    views = [
        "mv_bike_cost_summary",
        "mv_bike_lifecycle_events"
    ]

    results = []
    errors = []

    for view_name in views:
        try:
            result = await refresh_materialized_view(db, view_name, concurrently)
            results.append(result)
        except Exception as e:
            errors.append({
                "view_name": view_name,
                "error": str(e)
            })

    end_time = datetime.utcnow()
    total_duration = (end_time - start_time).total_seconds()

    return {
        "total_duration_seconds": total_duration,
        "refreshed_at": end_time.isoformat(),
        "success_count": len(results),
        "error_count": len(errors),
        "results": results,
        "errors": errors
    }


async def get_materialized_view_stats(
    db: AsyncSession,
    view_name: str
) -> Dict[str, Any]:
    """
    Get statistics about a materialized view.

    Args:
        db: Database session
        view_name: Name of the materialized view

    Returns:
        Dictionary with view statistics
    """
    try:
        # Get row count
        count_result = await db.execute(
            text(f"SELECT COUNT(*) as count FROM {view_name}")
        )
        row_count = count_result.scalar()

        # Get view size
        size_result = await db.execute(
            text("""
                SELECT pg_size_pretty(pg_total_relation_size(:view_name::regclass)) as size
            """),
            {"view_name": view_name}
        )
        size = size_result.scalar()

        # Get last refresh time (if stats_last_vacuum is available)
        # Note: This requires pg_stat_user_tables
        refresh_result = await db.execute(
            text("""
                SELECT
                    schemaname,
                    matviewname,
                    last_vacuum,
                    last_autovacuum,
                    last_analyze,
                    last_autoanalyze
                FROM pg_stat_user_tables
                WHERE schemaname || '.' || tablename = :view_name
                   OR tablename = :view_name
            """),
            {"view_name": view_name}
        )
        stats_row = refresh_result.fetchone()

        return {
            "view_name": view_name,
            "row_count": row_count,
            "size": size,
            "last_vacuum": stats_row[2].isoformat() if stats_row and stats_row[2] else None,
            "last_analyze": stats_row[4].isoformat() if stats_row and stats_row[4] else None
        }

    except Exception as e:
        logger.error(f"Failed to get stats for {view_name}: {str(e)}")
        return {
            "view_name": view_name,
            "error": str(e)
        }


async def schedule_view_refresh(
    db: AsyncSession,
    view_name: str,
    schedule_type: str = "nightly"
) -> Dict[str, Any]:
    """
    Schedule a materialized view refresh.

    Note: This is a placeholder for actual scheduling logic.
    In production, use a task scheduler like Celery, APScheduler, or cron.

    Args:
        db: Database session
        view_name: Name of the view to schedule
        schedule_type: Type of schedule (nightly, hourly, etc.)

    Returns:
        Dictionary with scheduling confirmation
    """
    schedules = {
        "nightly": "0 2 * * *",  # 2 AM daily
        "hourly": "0 * * * *",    # Every hour
        "daily": "0 8 * * *",     # 8 AM daily
        "weekly": "0 2 * * 0"     # 2 AM on Sundays
    }

    cron_expression = schedules.get(schedule_type, schedules["nightly"])

    logger.info(f"Scheduling {view_name} refresh with schedule: {cron_expression}")

    return {
        "view_name": view_name,
        "schedule_type": schedule_type,
        "cron_expression": cron_expression,
        "status": "scheduled",
        "note": "This is a configuration record. Actual scheduling requires external cron/scheduler."
    }
