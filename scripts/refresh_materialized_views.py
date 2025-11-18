#!/usr/bin/env python3
"""
Script to refresh materialized views.

This script can be run:
1. Via cron: Add to crontab with `0 2 * * * /path/to/refresh_materialized_views.py`
2. Manually: Run `python scripts/refresh_materialized_views.py`
3. Via systemd timer: Use the provided service file

Usage:
    python scripts/refresh_materialized_views.py [--view VIEW_NAME] [--all] [--no-concurrent]

Examples:
    # Refresh all views
    python scripts/refresh_materialized_views.py --all

    # Refresh specific view
    python scripts/refresh_materialized_views.py --view mv_bike_cost_summary

    # Refresh without concurrent mode (locks the view)
    python scripts/refresh_materialized_views.py --all --no-concurrent
"""

import asyncio
import argparse
import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.db import SessionLocal
from app.services import materialized_view_service
from loguru import logger


async def refresh_views(view_name: str = None, refresh_all: bool = False, concurrently: bool = True):
    """
    Refresh materialized views.

    Args:
        view_name: Specific view to refresh
        refresh_all: Whether to refresh all views
        concurrently: Whether to use concurrent refresh
    """
    async with SessionLocal() as db:
        try:
            if refresh_all:
                logger.info("Starting refresh of all bike lifecycle views")
                result = await materialized_view_service.refresh_all_bike_lifecycle_views(
                    db,
                    concurrently
                )

                logger.info(f"Refresh completed in {result['total_duration_seconds']:.2f} seconds")
                logger.info(f"Success: {result['success_count']}, Errors: {result['error_count']}")

                if result['errors']:
                    logger.error(f"Errors occurred: {result['errors']}")
                    return False

                return True

            elif view_name:
                logger.info(f"Starting refresh of {view_name}")
                result = await materialized_view_service.refresh_materialized_view(
                    db,
                    view_name,
                    concurrently
                )

                logger.info(f"Refresh completed in {result['duration_seconds']:.2f} seconds")
                return True

            else:
                logger.error("Must specify either --view or --all")
                return False

        except Exception as e:
            logger.error(f"Failed to refresh views: {str(e)}")
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Refresh materialized views")
    parser.add_argument(
        "--view",
        type=str,
        help="Name of specific view to refresh"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Refresh all bike lifecycle views"
    )
    parser.add_argument(
        "--no-concurrent",
        action="store_true",
        help="Disable concurrent refresh (view will be locked during refresh)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress info logging"
    )

    args = parser.parse_args()

    # Configure logging
    if args.quiet:
        logger.remove()
        logger.add(sys.stderr, level="ERROR")

    # Validate arguments
    if not args.view and not args.all:
        parser.print_help()
        sys.exit(1)

    # Run refresh
    concurrently = not args.no_concurrent
    success = asyncio.run(refresh_views(args.view, args.all, concurrently))

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
