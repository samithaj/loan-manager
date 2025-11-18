#!/usr/bin/env python3
"""
Reconcile BRC (Bike Repair Center) costs from Excel with existing repair jobs.

This script matches repair costs from the BRC Excel file with existing repair
jobs in the database, creating missing jobs and updating costs as needed.

Usage:
    python scripts/reconcile_brc.py --file brc_costs.csv [--dry-run] [--verbose]

CSV Format Expected:
    stock_number,license_plate,brand,model,job_date,description,parts_cost,
    labor_cost,total_cost,mechanic,job_status,notes

Example:
    python scripts/reconcile_brc.py --file data/brc_costs.csv --dry-run
    python scripts/reconcile_brc.py --file data/brc_costs.csv --create-missing
"""

import asyncio
import argparse
import csv
import sys
from pathlib import Path
from datetime import datetime, date
from typing import Dict, Optional, List
from decimal import Decimal

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.db import SessionLocal
from app.models import Bicycle, RepairJob
from loguru import logger
from sqlalchemy import select, and_


class ReconciliationStats:
    """Track reconciliation statistics."""

    def __init__(self):
        self.total_rows = 0
        self.bikes_found = 0
        self.bikes_not_found = 0
        self.jobs_matched = 0
        self.jobs_created = 0
        self.jobs_updated = 0
        self.cost_discrepancies = []
        self.errors = []

    def add_error(self, row_num: int, error: str):
        """Add an error."""
        self.errors.append(f"Row {row_num}: {error}")

    def add_discrepancy(self, stock_number: str, db_cost: Decimal, excel_cost: Decimal):
        """Add a cost discrepancy."""
        diff = excel_cost - db_cost
        self.cost_discrepancies.append({
            "stock_number": stock_number,
            "db_cost": float(db_cost),
            "excel_cost": float(excel_cost),
            "difference": float(diff)
        })

    def print_summary(self):
        """Print reconciliation summary."""
        logger.info("=" * 60)
        logger.info("BRC RECONCILIATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total rows processed: {self.total_rows}")
        logger.info(f"Bikes found: {self.bikes_found}")
        logger.info(f"Bikes not found: {self.bikes_not_found}")
        logger.info(f"Jobs matched: {self.jobs_matched}")
        logger.info(f"Jobs created: {self.jobs_created}")
        logger.info(f"Jobs updated: {self.jobs_updated}")
        logger.info(f"Cost discrepancies: {len(self.cost_discrepancies)}")
        logger.info(f"Errors: {len(self.errors)}")

        if self.cost_discrepancies:
            logger.warning("\nCOST DISCREPANCIES:")
            for disc in self.cost_discrepancies[:10]:
                logger.warning(
                    f"  {disc['stock_number']}: "
                    f"DB={disc['db_cost']:.2f}, Excel={disc['excel_cost']:.2f}, "
                    f"Diff={disc['difference']:.2f}"
                )
            if len(self.cost_discrepancies) > 10:
                logger.warning(f"  ... and {len(self.cost_discrepancies) - 10} more discrepancies")

        if self.errors:
            logger.error("\nERRORS:")
            for error in self.errors[:10]:
                logger.error(f"  {error}")
            if len(self.errors) > 10:
                logger.error(f"  ... and {len(self.errors) - 10} more errors")


def parse_decimal(value: str) -> Optional[Decimal]:
    """Parse decimal value safely."""
    if not value or value.strip() == "":
        return None

    try:
        cleaned = value.replace("LKR", "").replace("Rs.", "").replace(",", "").strip()
        return Decimal(cleaned)
    except Exception:
        return None


def parse_date(value: str) -> Optional[date]:
    """Parse date value safely."""
    if not value or value.strip() == "":
        return None

    formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%d-%m-%Y",
        "%Y/%m/%d"
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue

    return None


async def find_bike_by_identifier(
    db,
    stock_number: Optional[str],
    license_plate: Optional[str],
    brand: Optional[str],
    model: Optional[str]
) -> Optional[Bicycle]:
    """
    Find bike by stock number, license plate, or brand/model.

    Args:
        db: Database session
        stock_number: Stock number to search
        license_plate: License plate to search
        brand: Brand name
        model: Model name

    Returns:
        Bicycle if found, None otherwise
    """
    # Try stock number first
    if stock_number:
        result = await db.execute(
            select(Bicycle).where(Bicycle.current_stock_number == stock_number)
        )
        bike = result.scalar_one_or_none()
        if bike:
            return bike

    # Try license plate
    if license_plate:
        result = await db.execute(
            select(Bicycle).where(Bicycle.license_plate == license_plate)
        )
        bike = result.scalar_one_or_none()
        if bike:
            return bike

    # Try brand and model (less reliable)
    if brand and model:
        result = await db.execute(
            select(Bicycle).where(
                and_(
                    Bicycle.brand == brand,
                    Bicycle.model == model
                )
            ).limit(1)
        )
        bike = result.scalar_one_or_none()
        if bike:
            logger.warning(f"Matched {brand} {model} by brand/model only - verify correctness")
            return bike

    return None


async def reconcile_repair_row(
    db,
    row: Dict[str, str],
    row_num: int,
    stats: ReconciliationStats,
    dry_run: bool = False,
    create_missing: bool = False
) -> bool:
    """
    Reconcile a single repair record from BRC Excel.

    Returns:
        True if successful, False otherwise
    """
    try:
        # Extract identifiers
        stock_number = row.get("stock_number", "").strip() or None
        license_plate = row.get("license_plate", "").strip() or None
        brand = row.get("brand", "").strip() or None
        model = row.get("model", "").strip() or None

        # Find bike
        bike = await find_bike_by_identifier(db, stock_number, license_plate, brand, model)

        if not bike:
            stats.bikes_not_found += 1
            stats.add_error(
                row_num,
                f"Bike not found: stock={stock_number}, plate={license_plate}, {brand} {model}"
            )
            return False

        stats.bikes_found += 1

        # Parse repair data
        job_date = parse_date(row.get("job_date", "")) or datetime.now().date()
        description = row.get("description", "").strip() or "Repair from BRC Excel"
        parts_cost = parse_decimal(row.get("parts_cost", "0")) or Decimal(0)
        labor_cost = parse_decimal(row.get("labor_cost", "0")) or Decimal(0)
        total_cost = parse_decimal(row.get("total_cost", ""))

        # Calculate total if not provided
        if not total_cost:
            total_cost = parts_cost + labor_cost

        if total_cost <= 0:
            stats.add_error(row_num, f"Invalid cost for {bike.current_stock_number}")
            return False

        mechanic = row.get("mechanic", "").strip() or "Unknown"
        job_status = row.get("job_status", "COMPLETED").strip().upper()
        notes = row.get("notes", "").strip()

        # Check if similar job already exists
        result = await db.execute(
            select(RepairJob).where(
                and_(
                    RepairJob.bicycle_id == bike.id,
                    RepairJob.description.ilike(f"%{description[:20]}%"),
                    RepairJob.total_cost == total_cost
                )
            ).limit(1)
        )
        existing_job = result.scalar_one_or_none()

        if existing_job:
            logger.debug(f"Matched existing job for {bike.current_stock_number}: {description}")
            stats.jobs_matched += 1

            # Check cost discrepancy
            if existing_job.total_cost != total_cost:
                stats.add_discrepancy(
                    bike.current_stock_number or bike.id,
                    existing_job.total_cost,
                    total_cost
                )

            return True

        # Create new job if not found and create_missing is True
        if create_missing:
            if dry_run:
                logger.info(
                    f"[DRY RUN] Would create repair job for {bike.current_stock_number}: "
                    f"{description} - {total_cost}"
                )
                stats.jobs_created += 1
                return True

            # Create repair job
            repair_job = RepairJob(
                bicycle_id=bike.id,
                description=description,
                parts_cost=parts_cost,
                labor_cost=labor_cost,
                total_cost=total_cost,
                job_date=job_date,
                status=job_status,
                assigned_to=mechanic,
                notes=notes or "Imported from BRC Excel",
                created_by="IMPORT"
            )

            db.add(repair_job)

            # Update bike's total repair cost
            current_repair_cost = bike.total_repair_cost or Decimal(0)
            bike.total_repair_cost = current_repair_cost + total_cost

            logger.info(
                f"Created repair job for {bike.current_stock_number}: "
                f"{description} - {total_cost}"
            )
            stats.jobs_created += 1

            return True
        else:
            logger.warning(
                f"Job not found for {bike.current_stock_number} but --create-missing not set"
            )
            return False

    except Exception as e:
        stats.add_error(row_num, f"Error: {str(e)}")
        logger.error(f"Error reconciling row {row_num}: {str(e)}")
        return False


async def reconcile_brc(
    csv_file: Path,
    dry_run: bool = False,
    verbose: bool = False,
    create_missing: bool = False
) -> ReconciliationStats:
    """
    Reconcile BRC repair costs with database.

    Args:
        csv_file: Path to CSV file
        dry_run: If True, don't actually create/update records
        verbose: Enable verbose logging
        create_missing: If True, create missing repair jobs

    Returns:
        ReconciliationStats object with results
    """
    stats = ReconciliationStats()

    if verbose:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")

    logger.info(f"Starting BRC reconciliation from {csv_file}")
    logger.info(f"Create missing jobs: {create_missing}")
    logger.info(f"Dry run: {dry_run}")

    if not csv_file.exists():
        logger.error(f"File not found: {csv_file}")
        return stats

    async with SessionLocal() as db:
        try:
            with open(csv_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                for row_num, row in enumerate(reader, start=2):
                    stats.total_rows += 1

                    await reconcile_repair_row(
                        db,
                        row,
                        row_num,
                        stats,
                        dry_run,
                        create_missing
                    )

                    # Commit every 20 rows
                    if stats.total_rows % 20 == 0:
                        if not dry_run:
                            await db.commit()
                        logger.info(f"Processed {stats.total_rows} rows...")

            # Final commit
            if not dry_run:
                await db.commit()
                logger.info("All changes committed")
            else:
                logger.info("DRY RUN - No changes committed")

        except Exception as e:
            logger.error(f"Fatal error during reconciliation: {str(e)}")
            if not dry_run:
                await db.rollback()
            stats.add_error(0, f"Fatal error: {str(e)}")

    return stats


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Reconcile BRC repair costs with database"
    )
    parser.add_argument(
        "--file",
        type=Path,
        required=True,
        help="Path to CSV file exported from BRC Excel"
    )
    parser.add_argument(
        "--create-missing",
        action="store_true",
        help="Create repair jobs that don't exist in database"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode - don't actually create/update records"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Run reconciliation
    stats = asyncio.run(
        reconcile_brc(
            args.file,
            args.dry_run,
            args.verbose,
            args.create_missing
        )
    )

    # Print summary
    stats.print_summary()

    # Exit with error code if there were errors
    sys.exit(1 if stats.errors else 0)


if __name__ == "__main__":
    main()
