#!/usr/bin/env python3
"""
Performance and load testing for bike lifecycle system.

Tests:
- Create 1000+ bikes
- Test query performance
- Test report generation
- Identify slow queries

Usage:
    python tests/performance/test_load_performance.py
    python tests/performance/test_load_performance.py --bikes 5000
"""

import asyncio
import argparse
import time
import sys
from pathlib import Path
from datetime import datetime, date, timedelta
from decimal import Decimal
import random

# Add backend to path
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.db import SessionLocal
from app.models import Bicycle, BicycleSale, Company
from app.services.bike_lifecycle_service import BikeLifecycleService
from sqlalchemy import select, func, text
from loguru import logger


class PerformanceTimer:
    """Context manager for timing operations."""

    def __init__(self, name: str):
        self.name = name
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, *args):
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        logger.info(f"{self.name}: {duration:.3f}s")

    @property
    def duration(self):
        if self.end_time and self.start_time:
            return self.end_time - self.start_time
        return None


async def create_test_bikes(db, count: int = 1000) -> list:
    """Create test bikes for performance testing."""

    logger.info(f"Creating {count} test bikes...")

    brands = ["Honda", "Yamaha", "Bajaj", "TVS", "Hero", "Suzuki"]
    models = ["CB 125F", "FZ", "Pulsar 150", "Apache", "Splendor", "Gixxer"]
    companies = ["MA", "IN"]
    branches = ["WW", "HP", "BRC", "KA", "MO"]
    statuses = ["IN_STOCK", "SOLD", "MAINTENANCE"]

    bikes = []
    lifecycle_service = BikeLifecycleService()

    start_time = time.time()

    for i in range(count):
        brand = random.choice(brands)
        model = random.choice(models)
        year = random.randint(2018, 2024)
        company_id = random.choice(companies)
        branch_id = random.choice(branches)

        procurement_data = {
            "company_id": company_id,
            "branch_id": branch_id,
            "business_model": "SECOND_HAND_SALE",
            "title": f"{brand} {model} {year}",
            "brand": brand,
            "model": model,
            "year": year,
            "base_purchase_price": Decimal(random.randint(100000, 300000)),
            "procurement_date": date.today() - timedelta(days=random.randint(0, 365)),
            "procured_by": f"User{random.randint(1, 10)}",
            "condition": "USED"
        }

        bike = await lifecycle_service.procure_bike(db, procurement_data)

        # Randomly add repair costs
        if random.random() > 0.5:
            bike.total_repair_cost = Decimal(random.randint(5000, 50000))

        # Randomly add branch expenses
        if random.random() > 0.5:
            bike.total_branch_expenses = Decimal(random.randint(1000, 10000))

        # Randomly sell some bikes
        if random.random() > 0.4:
            bike.status = "SOLD"
            bike.selling_price = Decimal(random.randint(150000, 350000))
            bike.selling_date = date.today() - timedelta(days=random.randint(0, 180))

        bikes.append(bike)

        # Commit in batches
        if (i + 1) % 100 == 0:
            await db.commit()
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed
            logger.info(f"  Created {i + 1}/{count} bikes ({rate:.1f} bikes/sec)")

    # Final commit
    await db.commit()

    total_time = time.time() - start_time
    logger.info(f"✓ Created {count} bikes in {total_time:.2f}s ({count/total_time:.1f} bikes/sec)")

    return bikes


async def test_query_performance(db):
    """Test performance of common queries."""

    logger.info("\n" + "=" * 60)
    logger.info("QUERY PERFORMANCE TESTS")
    logger.info("=" * 60)

    # Test 1: Count all bikes
    with PerformanceTimer("Count all bikes"):
        result = await db.execute(select(func.count(Bicycle.id)))
        count = result.scalar()
        logger.info(f"  Total bikes: {count}")

    # Test 2: Filter by company and branch
    with PerformanceTimer("Filter by company and branch"):
        result = await db.execute(
            select(Bicycle).where(
                Bicycle.company_id == "MA",
                Bicycle.current_branch_id == "WW"
            ).limit(100)
        )
        bikes = result.scalars().all()
        logger.info(f"  Found {len(bikes)} bikes")

    # Test 3: Filter by status
    with PerformanceTimer("Filter by status"):
        result = await db.execute(
            select(Bicycle).where(Bicycle.status == "SOLD").limit(100)
        )
        bikes = result.scalars().all()
        logger.info(f"  Found {len(bikes)} sold bikes")

    # Test 4: Complex query with aggregations
    with PerformanceTimer("Aggregation query"):
        result = await db.execute(
            select(
                Bicycle.company_id,
                Bicycle.status,
                func.count(Bicycle.id).label("count"),
                func.sum(Bicycle.base_purchase_price).label("total_purchase"),
                func.sum(Bicycle.selling_price).label("total_sales")
            ).group_by(
                Bicycle.company_id,
                Bicycle.status
            )
        )
        rows = result.all()
        logger.info(f"  Aggregated {len(rows)} groups")

    # Test 5: Join with sales
    with PerformanceTimer("Join with sales"):
        result = await db.execute(
            select(Bicycle, BicycleSale)
            .join(BicycleSale, Bicycle.id == BicycleSale.bicycle_id)
            .limit(100)
        )
        rows = result.all()
        logger.info(f"  Joined {len(rows)} records")

    # Test 6: Date range query
    start_date = date.today() - timedelta(days=90)
    with PerformanceTimer("Date range query (90 days)"):
        result = await db.execute(
            select(Bicycle).where(
                Bicycle.procurement_date >= start_date
            ).limit(100)
        )
        bikes = result.scalars().all()
        logger.info(f"  Found {len(bikes)} bikes")

    # Test 7: EXPLAIN ANALYZE for slow query
    logger.info("\nRunning EXPLAIN ANALYZE on complex query...")
    explain_query = """
    EXPLAIN ANALYZE
    SELECT
        b.company_id,
        b.current_branch_id,
        b.status,
        COUNT(*) as bike_count,
        SUM(b.base_purchase_price) as total_purchase,
        SUM(b.total_repair_cost) as total_repair,
        SUM(b.selling_price) as total_sales
    FROM bicycles b
    WHERE b.business_model = 'SECOND_HAND_SALE'
    GROUP BY b.company_id, b.current_branch_id, b.status
    """

    result = await db.execute(text(explain_query))
    explain_output = result.fetchall()

    logger.info("EXPLAIN ANALYZE output:")
    for row in explain_output:
        logger.info(f"  {row[0]}")


async def test_report_generation(db):
    """Test report generation performance."""

    logger.info("\n" + "=" * 60)
    logger.info("REPORT GENERATION TESTS")
    logger.info("=" * 60)

    # Test 1: Acquisition ledger
    with PerformanceTimer("Acquisition ledger (1000 bikes)"):
        result = await db.execute(
            select(Bicycle)
            .where(Bicycle.business_model == "SECOND_HAND_SALE")
            .order_by(Bicycle.procurement_date.desc())
            .limit(1000)
        )
        bikes = result.scalars().all()
        logger.info(f"  Retrieved {len(bikes)} bikes")

    # Test 2: Cost summary with calculations
    with PerformanceTimer("Cost summary with P/L calculations"):
        result = await db.execute(
            select(Bicycle)
            .where(Bicycle.business_model == "SECOND_HAND_SALE")
            .limit(1000)
        )
        bikes = result.scalars().all()

        # Calculate P/L for each
        for bike in bikes:
            total_cost = (
                (bike.base_purchase_price or Decimal(0)) +
                (bike.total_repair_cost or Decimal(0)) +
                (bike.total_branch_expenses or Decimal(0))
            )
            if bike.selling_price:
                profit = bike.selling_price - total_cost

        logger.info(f"  Calculated P/L for {len(bikes)} bikes")

    # Test 3: Branch stock summary
    with PerformanceTimer("Branch stock summary"):
        result = await db.execute(
            select(
                Bicycle.current_branch_id,
                Bicycle.status,
                func.count(Bicycle.id).label("count"),
                func.sum(Bicycle.base_purchase_price).label("value")
            )
            .where(Bicycle.business_model == "SECOND_HAND_SALE")
            .group_by(Bicycle.current_branch_id, Bicycle.status)
        )
        rows = result.all()
        logger.info(f"  Generated summary for {len(rows)} groups")


async def test_index_usage(db):
    """Check if indexes are being used."""

    logger.info("\n" + "=" * 60)
    logger.info("INDEX USAGE CHECK")
    logger.info("=" * 60)

    # Check index usage on common queries
    queries = [
        ("Company/Branch filter", """
            EXPLAIN
            SELECT * FROM bicycles
            WHERE company_id = 'MA' AND current_branch_id = 'WW'
            LIMIT 100
        """),
        ("Status filter", """
            EXPLAIN
            SELECT * FROM bicycles
            WHERE status = 'SOLD'
            LIMIT 100
        """),
        ("Stock number lookup", """
            EXPLAIN
            SELECT * FROM bicycles
            WHERE current_stock_number = 'MA/WW/ST/0001'
        """),
        ("Date range", """
            EXPLAIN
            SELECT * FROM bicycles
            WHERE procurement_date >= CURRENT_DATE - INTERVAL '90 days'
            LIMIT 100
        """),
    ]

    for name, query in queries:
        logger.info(f"\n{name}:")
        result = await db.execute(text(query))
        plan = result.fetchall()

        uses_index = any("Index Scan" in str(row[0]) for row in plan)
        uses_seq_scan = any("Seq Scan" in str(row[0]) for row in plan)

        if uses_index:
            logger.info("  ✓ Using index")
        elif uses_seq_scan:
            logger.warning("  ⚠ Using sequential scan (consider adding index)")

        for row in plan:
            logger.info(f"    {row[0]}")


async def cleanup_test_data(db):
    """Clean up test bikes."""

    logger.info("\n" + "=" * 60)
    logger.info("CLEANUP")
    logger.info("=" * 60)

    # Delete test bikes (those created today)
    result = await db.execute(
        select(func.count(Bicycle.id)).where(
            Bicycle.procurement_notes.like("%Imported%") == False,
            Bicycle.procured_by.like("User%")
        )
    )
    count = result.scalar()

    if count > 0:
        logger.info(f"Found {count} test bikes to clean up")

        # Delete associated sales first
        await db.execute(
            text("""
                DELETE FROM bicycle_sales
                WHERE bicycle_id IN (
                    SELECT id FROM bicycles
                    WHERE procured_by LIKE 'User%'
                )
            """)
        )

        # Delete bikes
        await db.execute(
            text("""
                DELETE FROM bicycles
                WHERE procured_by LIKE 'User%'
            """)
        )

        await db.commit()
        logger.info(f"✓ Cleaned up {count} test bikes")
    else:
        logger.info("No test bikes to clean up")


async def run_performance_tests(num_bikes: int = 1000, cleanup: bool = True):
    """Run all performance tests."""

    logger.remove()
    logger.add(sys.stderr, level="INFO")

    logger.info("=" * 60)
    logger.info("BIKE LIFECYCLE PERFORMANCE TESTS")
    logger.info("=" * 60)
    logger.info(f"Test size: {num_bikes} bikes")
    logger.info(f"Cleanup after: {cleanup}")

    async with SessionLocal() as db:
        try:
            # Ensure test company exists
            result = await db.execute(select(Company).where(Company.id == "MA"))
            if not result.scalar_one_or_none():
                company = Company(
                    id="MA",
                    name="Test Company",
                    district="Monaragala",
                    contact_person="Test",
                    contact_phone="0771234567"
                )
                db.add(company)
                await db.commit()

            # Create test data
            bikes = await create_test_bikes(db, num_bikes)

            # Run tests
            await test_query_performance(db)
            await test_report_generation(db)
            await test_index_usage(db)

            # Cleanup
            if cleanup:
                await cleanup_test_data(db)

            logger.info("\n" + "=" * 60)
            logger.info("✓ ALL PERFORMANCE TESTS COMPLETED")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"✗ Performance test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run performance tests")
    parser.add_argument(
        "--bikes",
        type=int,
        default=1000,
        help="Number of bikes to create (default: 1000)"
    )
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Don't clean up test data after tests"
    )

    args = parser.parse_args()

    asyncio.run(run_performance_tests(args.bikes, not args.no_cleanup))


if __name__ == "__main__":
    main()
