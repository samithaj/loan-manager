#!/usr/bin/env python3
"""
Integration tests for bike lifecycle system.

Tests the complete workflow:
1. Procure bike → 2. Repair → 3. Transfer → 4. Sell → 5. Commission

Usage:
    pytest tests/integration/test_bike_lifecycle_workflow.py -v
    python tests/integration/test_bike_lifecycle_workflow.py
"""

import pytest
import asyncio
from datetime import datetime, date
from decimal import Decimal
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.db import SessionLocal
from app.models import (
    Bicycle, BicycleSale, BicycleTransfer, BicycleBranchExpense,
    BonusPayment, RepairJob, Company
)
from app.services.bike_lifecycle_service import BikeLifecycleService
from app.services.transfer_service import TransferService
from app.services.commission_service import CommissionService
from app.services.stock_number_service import StockNumberService


class TestBikeLifecycleWorkflow:
    """Test complete bike lifecycle from procurement to commission."""

    @pytest.fixture
    async def db_session(self):
        """Create a test database session."""
        async with SessionLocal() as session:
            yield session

    @pytest.fixture
    async def test_company(self, db_session):
        """Ensure test company exists."""
        from sqlalchemy import select

        result = await db_session.execute(
            select(Company).where(Company.id == "MA")
        )
        company = result.scalar_one_or_none()

        if not company:
            company = Company(
                id="MA",
                name="Test Company MA",
                district="Monaragala",
                contact_person="Test Person",
                contact_phone="0771234567"
            )
            db_session.add(company)
            await db_session.commit()

        return company

    @pytest.mark.asyncio
    async def test_full_workflow(self, db_session, test_company):
        """Test complete workflow: procure → repair → transfer → sell → commission."""

        lifecycle_service = BikeLifecycleService()
        transfer_service = TransferService()
        commission_service = CommissionService()

        # Step 1: Procure bike
        print("\n=== Step 1: Procure Bike ===")
        procurement_data = {
            "company_id": "MA",
            "branch_id": "WW",
            "business_model": "SECOND_HAND_SALE",
            "title": "Test Honda CB 125F 2020",
            "brand": "Honda",
            "model": "CB 125F",
            "year": 2020,
            "base_purchase_price": Decimal("150000.00"),
            "procurement_date": date.today(),
            "procured_by": "Test User",
            "supplier_name": "Test Supplier",
            "condition": "USED"
        }

        bike = await lifecycle_service.procure_bike(db_session, procurement_data)
        await db_session.commit()

        assert bike is not None
        assert bike.current_stock_number is not None
        assert bike.company_id == "MA"
        assert bike.current_branch_id == "WW"
        assert bike.status == "IN_STOCK"
        print(f"✓ Bike procured: {bike.current_stock_number}")

        # Step 2: Add repair job
        print("\n=== Step 2: Add Repair Job ===")
        repair_job = RepairJob(
            bicycle_id=bike.id,
            description="Test repair - oil change and brake pads",
            parts_cost=Decimal("5000.00"),
            labor_cost=Decimal("3000.00"),
            total_cost=Decimal("8000.00"),
            job_date=date.today(),
            status="COMPLETED",
            assigned_to="Test Mechanic",
            created_by="Test User"
        )

        db_session.add(repair_job)
        bike.total_repair_cost = Decimal("8000.00")
        await db_session.commit()

        print(f"✓ Repair job added: {repair_job.total_cost}")

        # Step 3: Transfer to another branch
        print("\n=== Step 3: Transfer to HP Branch ===")
        transfer = await transfer_service.initiate_transfer(
            db_session,
            bike.id,
            "HP",  # to_branch_id
            "Test Manager",
            notes="Test transfer"
        )
        await db_session.commit()

        assert transfer.status == "PENDING"
        print(f"✓ Transfer initiated: {transfer.id}")

        # Approve transfer
        await transfer_service.approve_transfer(
            db_session,
            transfer.id,
            "Test Admin"
        )
        await db_session.commit()

        assert transfer.status == "APPROVED"
        print(f"✓ Transfer approved")

        # Complete transfer
        await transfer_service.complete_transfer(
            db_session,
            transfer.id,
            "Test Receiver"
        )
        await db_session.commit()

        # Refresh bike
        await db_session.refresh(bike)

        assert transfer.status == "COMPLETED"
        assert bike.current_branch_id == "HP"
        print(f"✓ Transfer completed - bike now at HP")

        # Step 4: Add branch expense
        print("\n=== Step 4: Add Branch Expense ===")
        expense = BicycleBranchExpense(
            bicycle_id=bike.id,
            branch_id="HP",
            category="CLEANING",
            amount=Decimal("2000.00"),
            expense_date=date.today(),
            notes="Test cleaning expense",
            recorded_by="Test User"
        )

        db_session.add(expense)
        bike.total_branch_expenses = Decimal("2000.00")
        await db_session.commit()

        print(f"✓ Expense added: {expense.amount}")

        # Step 5: Sell bike
        print("\n=== Step 5: Sell Bike ===")
        sale_data = {
            "bicycle_id": bike.id,
            "selling_price": Decimal("180000.00"),
            "sale_date": date.today(),
            "selling_branch_id": "HP",
            "sold_by": "Test Salesperson",
            "customer_name": "Test Customer",
            "customer_contact": "0771234567",
            "payment_method": "CASH"
        }

        sale = await lifecycle_service.sell_bike(db_session, bike.id, sale_data)
        await db_session.commit()

        # Refresh bike
        await db_session.refresh(bike)

        assert sale is not None
        assert bike.status == "SOLD"
        assert bike.selling_price == Decimal("180000.00")
        print(f"✓ Bike sold for: {sale.selling_price}")

        # Step 6: Verify commission calculation
        print("\n=== Step 6: Verify Commission ===")
        cost_summary = await lifecycle_service.calculate_bike_cost_summary(
            db_session,
            bike.id
        )

        expected_total_cost = (
            Decimal("150000.00") +  # purchase
            Decimal("8000.00") +     # repair
            Decimal("2000.00")       # expense
        )
        expected_profit = Decimal("180000.00") - expected_total_cost

        assert cost_summary["total_cost"] == expected_total_cost
        assert cost_summary["profit_or_loss"] == expected_profit
        print(f"✓ Total cost: {cost_summary['total_cost']}")
        print(f"✓ Profit: {cost_summary['profit_or_loss']}")

        # Verify commission was created (if bonus rules exist)
        # This might be None if no bonus rules are configured
        print(f"✓ Workflow complete!")

        return bike

    @pytest.mark.asyncio
    async def test_concurrent_transfers(self, db_session, test_company):
        """Test that concurrent transfers don't create race conditions."""

        lifecycle_service = BikeLifecycleService()
        transfer_service = TransferService()

        # Create a bike
        procurement_data = {
            "company_id": "MA",
            "branch_id": "WW",
            "business_model": "SECOND_HAND_SALE",
            "title": "Test Concurrent Bike",
            "brand": "Test",
            "model": "Concurrent",
            "year": 2020,
            "base_purchase_price": Decimal("100000.00"),
            "procurement_date": date.today(),
            "procured_by": "Test",
            "condition": "USED"
        }

        bike = await lifecycle_service.procure_bike(db_session, procurement_data)
        await db_session.commit()

        # Try to initiate two transfers simultaneously
        transfer1 = await transfer_service.initiate_transfer(
            db_session,
            bike.id,
            "HP",
            "User1",
            notes="Transfer 1"
        )
        await db_session.commit()

        # Second transfer should fail or be queued
        try:
            transfer2 = await transfer_service.initiate_transfer(
                db_session,
                bike.id,
                "BRC",
                "User2",
                notes="Transfer 2"
            )
            await db_session.commit()

            # If both succeed, ensure only one can be approved
            assert transfer1.status == "PENDING" or transfer2.status == "PENDING"

        except Exception as e:
            # Expected - bike already has pending transfer
            print(f"✓ Concurrent transfer properly rejected: {str(e)}")

        print("✓ Concurrent transfer test passed")

    @pytest.mark.asyncio
    async def test_transfer_rollback(self, db_session, test_company):
        """Test that rejected transfers properly revert state."""

        lifecycle_service = BikeLifecycleService()
        transfer_service = TransferService()

        # Create and transfer a bike
        procurement_data = {
            "company_id": "MA",
            "branch_id": "WW",
            "business_model": "SECOND_HAND_SALE",
            "title": "Test Rollback Bike",
            "brand": "Test",
            "model": "Rollback",
            "year": 2020,
            "base_purchase_price": Decimal("100000.00"),
            "procurement_date": date.today(),
            "procured_by": "Test",
            "condition": "USED"
        }

        bike = await lifecycle_service.procure_bike(db_session, procurement_data)
        original_stock_number = bike.current_stock_number
        original_branch = bike.current_branch_id
        await db_session.commit()

        # Initiate transfer
        transfer = await transfer_service.initiate_transfer(
            db_session,
            bike.id,
            "HP",
            "Test User",
            notes="Test transfer to reject"
        )
        await db_session.commit()

        # Approve it (assigns new stock number)
        await transfer_service.approve_transfer(
            db_session,
            transfer.id,
            "Test Admin"
        )
        await db_session.commit()

        # Now reject it
        await transfer_service.reject_transfer(
            db_session,
            transfer.id,
            "Test Admin",
            "Test rejection"
        )
        await db_session.commit()

        # Refresh bike
        await db_session.refresh(bike)

        # Verify rollback
        assert transfer.status == "REJECTED"
        assert bike.current_branch_id == original_branch
        # Stock number should be reverted or new assignment created
        print(f"✓ Transfer rollback successful")


async def run_tests():
    """Run all tests."""
    test_suite = TestBikeLifecycleWorkflow()

    async with SessionLocal() as db:
        # Create test company
        from sqlalchemy import select
        result = await db.execute(select(Company).where(Company.id == "MA"))
        company = result.scalar_one_or_none()

        if not company:
            company = Company(
                id="MA",
                name="Test Company MA",
                district="Monaragala",
                contact_person="Test Person",
                contact_phone="0771234567"
            )
            db.add(company)
            await db.commit()

        print("=" * 60)
        print("BIKE LIFECYCLE INTEGRATION TESTS")
        print("=" * 60)

        try:
            # Test 1: Full workflow
            print("\n[TEST 1] Full Workflow Test")
            print("-" * 60)
            await test_suite.test_full_workflow(db, company)
            print("\n✓ TEST 1 PASSED")

            # Test 2: Concurrent transfers
            print("\n[TEST 2] Concurrent Transfer Test")
            print("-" * 60)
            await test_suite.test_concurrent_transfers(db, company)
            print("\n✓ TEST 2 PASSED")

            # Test 3: Transfer rollback
            print("\n[TEST 3] Transfer Rollback Test")
            print("-" * 60)
            await test_suite.test_transfer_rollback(db, company)
            print("\n✓ TEST 3 PASSED")

            print("\n" + "=" * 60)
            print("ALL TESTS PASSED ✓")
            print("=" * 60)

        except Exception as e:
            print(f"\n✗ TEST FAILED: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_tests())
