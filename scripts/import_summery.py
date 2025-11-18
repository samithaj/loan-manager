#!/usr/bin/env python3
"""
Import historical bike data from summery.xlsx (Cost Summary Excel).

This script imports existing bike cost summary data from Excel format into the
bike lifecycle system database.

Usage:
    python scripts/import_summery.py --file summery.csv [--dry-run] [--verbose]

CSV Format Expected:
    stock_number,brand,model,year,company_id,branch_id,status,purchase_price,
    repair_cost,branch_expenses,selling_price,sale_date,customer_name,notes

Example:
    python scripts/import_summery.py --file data/summery.csv --dry-run
    python scripts/import_summery.py --file data/summery.csv --verbose
"""

import asyncio
import argparse
import csv
import sys
from pathlib import Path
from datetime import datetime, date
from typing import Dict, List, Any, Optional
from decimal import Decimal, InvalidOperation

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.db import SessionLocal
from app.models import Bicycle, BicycleSale, BicycleBranchExpense
from app.services.stock_number_service import StockNumberService
from loguru import logger
from sqlalchemy import select


class ImportStats:
    """Track import statistics."""

    def __init__(self):
        self.total_rows = 0
        self.bikes_created = 0
        self.bikes_skipped = 0
        self.sales_created = 0
        self.expenses_created = 0
        self.errors = []

    def add_error(self, row_num: int, error: str):
        """Add an error."""
        self.errors.append(f"Row {row_num}: {error}")

    def print_summary(self):
        """Print import summary."""
        logger.info("=" * 60)
        logger.info("IMPORT SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total rows processed: {self.total_rows}")
        logger.info(f"Bikes created: {self.bikes_created}")
        logger.info(f"Bikes skipped: {self.bikes_skipped}")
        logger.info(f"Sales created: {self.sales_created}")
        logger.info(f"Expenses created: {self.expenses_created}")
        logger.info(f"Errors: {len(self.errors)}")

        if self.errors:
            logger.error("\nERRORS:")
            for error in self.errors[:10]:  # Show first 10 errors
                logger.error(f"  {error}")
            if len(self.errors) > 10:
                logger.error(f"  ... and {len(self.errors) - 10} more errors")


def parse_decimal(value: str) -> Optional[Decimal]:
    """Parse decimal value safely."""
    if not value or value.strip() == "":
        return None

    try:
        # Remove currency symbols and commas
        cleaned = value.replace("LKR", "").replace("Rs.", "").replace(",", "").strip()
        return Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return None


def parse_date(value: str) -> Optional[date]:
    """Parse date value safely."""
    if not value or value.strip() == "":
        return None

    # Try common date formats
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


async def check_bike_exists(db, stock_number: str) -> bool:
    """Check if bike with stock number already exists."""
    result = await db.execute(
        select(Bicycle).where(Bicycle.current_stock_number == stock_number)
    )
    return result.scalar_one_or_none() is not None


async def import_bike_row(
    db,
    row: Dict[str, str],
    row_num: int,
    stats: ImportStats,
    dry_run: bool = False
) -> Optional[str]:
    """
    Import a single bike row from CSV.

    Returns:
        Bike ID if created, None otherwise
    """
    try:
        # Extract and validate required fields
        stock_number = row.get("stock_number", "").strip()
        brand = row.get("brand", "").strip()
        model = row.get("model", "").strip()

        if not stock_number:
            stats.add_error(row_num, "Missing stock number")
            return None

        if not brand or not model:
            stats.add_error(row_num, f"Missing brand or model for {stock_number}")
            return None

        # Check if bike already exists
        if await check_bike_exists(db, stock_number):
            logger.debug(f"Bike {stock_number} already exists, skipping")
            stats.bikes_skipped += 1
            return None

        # Parse year
        year_str = row.get("year", "").strip()
        try:
            year = int(year_str) if year_str else datetime.now().year
        except ValueError:
            year = datetime.now().year

        # Parse financial fields
        purchase_price = parse_decimal(row.get("purchase_price", "0"))
        repair_cost = parse_decimal(row.get("repair_cost", "0"))
        branch_expenses = parse_decimal(row.get("branch_expenses", "0"))
        selling_price = parse_decimal(row.get("selling_price", ""))

        # Extract other fields
        company_id = row.get("company_id", "MA").strip().upper()
        branch_id = row.get("branch_id", "").strip().upper()
        status = row.get("status", "IN_STOCK").strip().upper()

        # Determine status based on selling price
        if selling_price:
            status = "SOLD"

        # Create bike title
        title = f"{brand} {model} {year}"

        if dry_run:
            logger.info(f"[DRY RUN] Would create bike: {stock_number} - {title}")
            stats.bikes_created += 1
            return "dry-run-id"

        # Create bike
        bike = Bicycle(
            title=title,
            brand=brand,
            model=model,
            year=year,
            company_id=company_id,
            current_branch_id=branch_id or company_id,
            business_model="SECOND_HAND_SALE",
            status=status,
            current_stock_number=stock_number,
            base_purchase_price=purchase_price,
            total_repair_cost=repair_cost or Decimal(0),
            total_branch_expenses=branch_expenses or Decimal(0),
            procurement_date=datetime.now().date(),
            procured_by="IMPORT",
            procurement_notes=f"Imported from summery.xlsx on {datetime.now().date()}",
            condition="USED"
        )

        db.add(bike)
        await db.flush()  # Get bike ID

        logger.info(f"Created bike: {stock_number} - {title} (ID: {bike.id})")
        stats.bikes_created += 1

        # Create sale if selling price exists
        if selling_price:
            sale_date = parse_date(row.get("sale_date", "")) or datetime.now().date()
            customer_name = row.get("customer_name", "Unknown").strip()

            if not dry_run:
                sale = BicycleSale(
                    bicycle_id=bike.id,
                    selling_price=selling_price,
                    sale_date=sale_date,
                    selling_branch_id=branch_id or company_id,
                    sold_by="IMPORT",
                    customer_name=customer_name,
                    customer_contact="N/A",
                    payment_method="CASH",
                    notes=f"Imported from summery.xlsx"
                )

                # Update bike with sale info
                bike.selling_price = selling_price
                bike.selling_date = sale_date
                bike.status = "SOLD"

                db.add(sale)
                logger.info(f"  Created sale for {stock_number}: {selling_price}")
                stats.sales_created += 1

        # Create branch expenses if any
        if branch_expenses and branch_expenses > 0:
            if not dry_run:
                expense = BicycleBranchExpense(
                    bicycle_id=bike.id,
                    branch_id=branch_id or company_id,
                    category="OTHER",
                    amount=branch_expenses,
                    expense_date=datetime.now().date(),
                    notes="Imported from summery.xlsx",
                    recorded_by="IMPORT"
                )

                db.add(expense)
                logger.info(f"  Created expense for {stock_number}: {branch_expenses}")
                stats.expenses_created += 1

        return bike.id

    except Exception as e:
        stats.add_error(row_num, f"Error importing: {str(e)}")
        logger.error(f"Error importing row {row_num}: {str(e)}")
        return None


async def import_summery(
    csv_file: Path,
    dry_run: bool = False,
    verbose: bool = False
) -> ImportStats:
    """
    Import bikes from summery.xlsx CSV export.

    Args:
        csv_file: Path to CSV file
        dry_run: If True, don't actually create records
        verbose: Enable verbose logging

    Returns:
        ImportStats object with results
    """
    stats = ImportStats()

    if verbose:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")

    logger.info(f"Starting import from {csv_file}")
    logger.info(f"Dry run: {dry_run}")

    if not csv_file.exists():
        logger.error(f"File not found: {csv_file}")
        return stats

    async with SessionLocal() as db:
        try:
            with open(csv_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                    stats.total_rows += 1

                    await import_bike_row(db, row, row_num, stats, dry_run)

                    # Commit every 50 rows
                    if stats.total_rows % 50 == 0:
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
            logger.error(f"Fatal error during import: {str(e)}")
            if not dry_run:
                await db.rollback()
            stats.add_error(0, f"Fatal error: {str(e)}")

    return stats


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Import historical bike data from summery.xlsx CSV export"
    )
    parser.add_argument(
        "--file",
        type=Path,
        required=True,
        help="Path to CSV file exported from summery.xlsx"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode - don't actually import data"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Run import
    stats = asyncio.run(import_summery(args.file, args.dry_run, args.verbose))

    # Print summary
    stats.print_summary()

    # Exit with error code if there were errors
    sys.exit(1 if stats.errors else 0)


if __name__ == "__main__":
    main()
