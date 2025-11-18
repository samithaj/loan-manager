#!/usr/bin/env python3
"""
Import procurement records from November notebook CSV.

This script imports bike procurement records from the November notebook,
which tracks initial bike purchases. It auto-generates stock numbers based
on the company/branch/sequence pattern.

Usage:
    python scripts/import_notebook.py --file notebook.csv [--dry-run] [--verbose]

CSV Format Expected:
    date,company_id,branch_id,license_plate,brand,model,year,purchase_price,
    supplier_name,supplier_contact,procured_by,payment_method,invoice_number,notes

Example:
    python scripts/import_notebook.py --file data/november_notebook.csv --dry-run
    python scripts/import_notebook.py --file data/november_notebook.csv --company MA
"""

import asyncio
import argparse
import csv
import sys
from pathlib import Path
from datetime import datetime, date
from typing import Dict, Optional
from decimal import Decimal

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.db import SessionLocal
from app.models import Bicycle
from app.services.stock_number_service import StockNumberService
from loguru import logger


class NotebookImportStats:
    """Track import statistics."""

    def __init__(self):
        self.total_rows = 0
        self.bikes_created = 0
        self.bikes_skipped = 0
        self.stock_numbers_assigned = 0
        self.errors = []

    def add_error(self, row_num: int, error: str):
        """Add an error."""
        self.errors.append(f"Row {row_num}: {error}")

    def print_summary(self):
        """Print import summary."""
        logger.info("=" * 60)
        logger.info("NOTEBOOK IMPORT SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total rows processed: {self.total_rows}")
        logger.info(f"Bikes created: {self.bikes_created}")
        logger.info(f"Bikes skipped: {self.bikes_skipped}")
        logger.info(f"Stock numbers assigned: {self.stock_numbers_assigned}")
        logger.info(f"Errors: {len(self.errors)}")

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
        "%Y/%m/%d",
        "%d.%m.%Y"
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue

    return None


async def import_procurement_row(
    db,
    row: Dict[str, str],
    row_num: int,
    stats: NotebookImportStats,
    stock_service: StockNumberService,
    dry_run: bool = False,
    default_company: str = "MA"
) -> Optional[str]:
    """
    Import a single procurement record from notebook.

    Returns:
        Bike ID if created, None otherwise
    """
    try:
        # Extract required fields
        brand = row.get("brand", "").strip()
        model = row.get("model", "").strip()

        if not brand or not model:
            stats.add_error(row_num, "Missing brand or model")
            return None

        # Parse fields
        procurement_date = parse_date(row.get("date", "")) or datetime.now().date()
        company_id = row.get("company_id", default_company).strip().upper()
        branch_id = row.get("branch_id", company_id).strip().upper()

        # Parse year
        year_str = row.get("year", "").strip()
        try:
            year = int(year_str) if year_str else datetime.now().year
        except ValueError:
            year = datetime.now().year

        # Financial data
        purchase_price = parse_decimal(row.get("purchase_price", "0"))

        if not purchase_price or purchase_price <= 0:
            stats.add_error(row_num, "Invalid purchase price")
            return None

        # Supplier and procurement details
        supplier_name = row.get("supplier_name", "").strip()
        supplier_contact = row.get("supplier_contact", "").strip()
        procured_by = row.get("procured_by", "Unknown").strip()
        invoice_number = row.get("invoice_number", "").strip()
        payment_method = row.get("payment_method", "").strip()
        license_plate = row.get("license_plate", "").strip()
        notes = row.get("notes", "").strip()

        # Create bike title
        title = f"{brand} {model} {year}"

        if dry_run:
            logger.info(f"[DRY RUN] Would create procurement: {title} at {branch_id}")
            stats.bikes_created += 1
            stats.stock_numbers_assigned += 1
            return "dry-run-id"

        # Create bike
        bike = Bicycle(
            title=title,
            brand=brand,
            model=model,
            year=year,
            company_id=company_id,
            current_branch_id=branch_id,
            business_model="SECOND_HAND_SALE",
            status="IN_STOCK",
            base_purchase_price=purchase_price,
            procurement_date=procurement_date,
            procured_by=procured_by,
            supplier_name=supplier_name or None,
            supplier_contact=supplier_contact or None,
            procurement_invoice_number=invoice_number or None,
            procurement_notes=notes or f"Imported from November notebook",
            license_plate=license_plate or None,
            condition="USED",
            total_repair_cost=Decimal(0),
            total_branch_expenses=Decimal(0)
        )

        db.add(bike)
        await db.flush()  # Get bike ID

        # Assign stock number
        sequence_num, stock_number = await stock_service.assign_stock_number(
            db,
            bike.id,
            company_id,
            branch_id,
            reason="PROCUREMENT",
            notes="Imported from November notebook"
        )

        # Update bike with stock number
        bike.current_stock_number = stock_number

        logger.info(
            f"Created bike: {stock_number} - {title} "
            f"(ID: {bike.id}, Date: {procurement_date}, Price: {purchase_price})"
        )

        stats.bikes_created += 1
        stats.stock_numbers_assigned += 1

        return bike.id

    except Exception as e:
        stats.add_error(row_num, f"Error: {str(e)}")
        logger.error(f"Error importing row {row_num}: {str(e)}")
        return None


async def import_notebook(
    csv_file: Path,
    dry_run: bool = False,
    verbose: bool = False,
    default_company: str = "MA"
) -> NotebookImportStats:
    """
    Import procurement records from November notebook CSV.

    Args:
        csv_file: Path to CSV file
        dry_run: If True, don't actually create records
        verbose: Enable verbose logging
        default_company: Default company ID if not specified in CSV

    Returns:
        NotebookImportStats object with results
    """
    stats = NotebookImportStats()

    if verbose:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")

    logger.info(f"Starting notebook import from {csv_file}")
    logger.info(f"Default company: {default_company}")
    logger.info(f"Dry run: {dry_run}")

    if not csv_file.exists():
        logger.error(f"File not found: {csv_file}")
        return stats

    async with SessionLocal() as db:
        try:
            stock_service = StockNumberService()

            with open(csv_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                for row_num, row in enumerate(reader, start=2):
                    stats.total_rows += 1

                    await import_procurement_row(
                        db,
                        row,
                        row_num,
                        stats,
                        stock_service,
                        dry_run,
                        default_company
                    )

                    # Commit every 25 rows
                    if stats.total_rows % 25 == 0:
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
        description="Import procurement records from November notebook CSV"
    )
    parser.add_argument(
        "--file",
        type=Path,
        required=True,
        help="Path to CSV file from November notebook"
    )
    parser.add_argument(
        "--company",
        type=str,
        default="MA",
        help="Default company ID (default: MA)"
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
    stats = asyncio.run(
        import_notebook(
            args.file,
            args.dry_run,
            args.verbose,
            args.company
        )
    )

    # Print summary
    stats.print_summary()

    # Exit with error code if there were errors
    sys.exit(1 if stats.errors else 0)


if __name__ == "__main__":
    main()
