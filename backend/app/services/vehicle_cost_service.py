"""
Vehicle Cost Ledger Service
Handles all vehicle cost tracking, aggregation, and reporting
"""
from __future__ import annotations

from typing import Optional, Sequence, Tuple
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from ..models.vehicle_cost_ledger import VehicleCostLedger, CostEventType
from ..models.vehicle_cost_summary import VehicleCostSummary
from ..models.bicycle import Bicycle, BicycleStatus
from ..models.fund_source import FundSource
from ..models.branch import Branch
from ..schemas.vehicle_cost_schemas import (
    VehicleCostCreate,
    VehicleCostUpdate,
    VehicleCostFilters,
    VehicleSaleRequest,
)
from .bill_number_service import BillNumberService


class VehicleCostService:
    """Service for managing vehicle costs and aggregations"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.bill_service = BillNumberService(db)

    async def create_cost_entry(
        self, data: VehicleCostCreate, created_by: UUID, auto_generate_bill: bool = True
    ) -> VehicleCostLedger:
        """
        Create a new cost entry for a vehicle

        Args:
            data: Cost entry data
            created_by: User ID creating the entry
            auto_generate_bill: Auto-generate bill number if not provided
        """
        # Validate vehicle exists
        vehicle = await self.db.get(Bicycle, data.vehicle_id)
        if not vehicle:
            raise ValueError(f"Vehicle {data.vehicle_id} not found")

        # Check if vehicle costs are locked
        summary = await self._get_or_create_summary(data.vehicle_id)
        if summary.locked_entries > 0:
            # Check if all entries are locked
            stmt = select(func.count()).select_from(VehicleCostLedger).where(
                and_(
                    VehicleCostLedger.vehicle_id == data.vehicle_id,
                    VehicleCostLedger.is_locked == True
                )
            )
            locked_count = await self.db.scalar(stmt)
            if locked_count > 0:
                raise ValueError("Cannot add costs to a vehicle with locked entries (sold vehicle)")

        # Generate bill number
        bill_no = await self.bill_service.generate_bill_number(
            data.branch_id,
            data.fund_source_id,
            data.transaction_date or date.today()
        )

        # Create cost entry
        cost_entry = VehicleCostLedger(
            vehicle_id=data.vehicle_id,
            branch_id=data.branch_id,
            event_type=data.event_type,
            bill_no=bill_no,
            fund_source_id=data.fund_source_id,
            amount=data.amount,
            currency=data.currency,
            description=data.description,
            notes=data.notes,
            reference_table=data.reference_table,
            reference_id=data.reference_id,
            receipt_urls=data.receipt_urls or [],
            meta_json=data.meta_json or {},
            created_by=created_by,
        )

        self.db.add(cost_entry)
        await self.db.flush()

        # Update summary
        await self._update_summary(data.vehicle_id)

        await self.db.commit()
        await self.db.refresh(cost_entry)

        logger.info(f"Created cost entry {bill_no} for vehicle {data.vehicle_id}: {data.amount}")
        return cost_entry

    async def update_cost_entry(
        self, entry_id: UUID, data: VehicleCostUpdate
    ) -> VehicleCostLedger:
        """Update a cost entry (only if not locked)"""
        cost_entry = await self.db.get(VehicleCostLedger, entry_id)
        if not cost_entry:
            raise ValueError("Cost entry not found")

        if cost_entry.is_locked:
            raise ValueError("Cannot update locked cost entry")

        # Update fields
        if data.amount is not None:
            cost_entry.amount = data.amount
        if data.description is not None:
            cost_entry.description = data.description
        if data.notes is not None:
            cost_entry.notes = data.notes
        if data.receipt_urls is not None:
            cost_entry.receipt_urls = data.receipt_urls
        if data.meta_json is not None:
            cost_entry.meta_json = data.meta_json

        # Update summary
        await self._update_summary(cost_entry.vehicle_id)

        await self.db.commit()
        await self.db.refresh(cost_entry)

        logger.info(f"Updated cost entry {cost_entry.bill_no}")
        return cost_entry

    async def get_cost_entry(self, entry_id: UUID) -> Optional[VehicleCostLedger]:
        """Get cost entry by ID"""
        return await self.db.get(VehicleCostLedger, entry_id)

    async def list_cost_entries(
        self,
        filters: VehicleCostFilters,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[Sequence[VehicleCostLedger], int]:
        """List cost entries with filters and pagination"""
        stmt = select(VehicleCostLedger)

        # Apply filters
        if filters.vehicle_id:
            stmt = stmt.where(VehicleCostLedger.vehicle_id == filters.vehicle_id)
        if filters.branch_id:
            stmt = stmt.where(VehicleCostLedger.branch_id == filters.branch_id)
        if filters.event_type:
            stmt = stmt.where(VehicleCostLedger.event_type == filters.event_type)
        if filters.fund_source_id:
            stmt = stmt.where(VehicleCostLedger.fund_source_id == filters.fund_source_id)
        if filters.bill_no:
            stmt = stmt.where(VehicleCostLedger.bill_no.ilike(f"%{filters.bill_no}%"))
        if filters.is_locked is not None:
            stmt = stmt.where(VehicleCostLedger.is_locked == filters.is_locked)
        if filters.is_approved is not None:
            stmt = stmt.where(VehicleCostLedger.is_approved == filters.is_approved)
        if filters.from_date:
            stmt = stmt.where(VehicleCostLedger.created_at >= filters.from_date)
        if filters.to_date:
            stmt = stmt.where(VehicleCostLedger.created_at <= filters.to_date)
        if filters.min_amount is not None:
            stmt = stmt.where(VehicleCostLedger.amount >= filters.min_amount)
        if filters.max_amount is not None:
            stmt = stmt.where(VehicleCostLedger.amount <= filters.max_amount)

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await self.db.scalar(count_stmt) or 0

        # Apply pagination
        stmt = stmt.order_by(VehicleCostLedger.created_at.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        # Execute query
        result = await self.db.execute(stmt)
        items = result.scalars().all()

        return items, total

    async def get_vehicle_summary(self, vehicle_id: str) -> VehicleCostSummary:
        """Get cost summary for a vehicle"""
        summary = await self._get_or_create_summary(vehicle_id)
        return summary

    async def lock_vehicle_costs(
        self, vehicle_id: str, locked_by: UUID
    ) -> int:
        """
        Lock all cost entries for a vehicle (typically after sale)

        Returns:
            Number of entries locked
        """
        stmt = (
            select(VehicleCostLedger)
            .where(
                and_(
                    VehicleCostLedger.vehicle_id == vehicle_id,
                    VehicleCostLedger.is_locked == False
                )
            )
        )

        result = await self.db.execute(stmt)
        entries = result.scalars().all()

        locked_count = 0
        for entry in entries:
            entry.is_locked = True
            entry.locked_at = datetime.utcnow()
            entry.locked_by = locked_by
            locked_count += 1

        await self._update_summary(vehicle_id)
        await self.db.commit()

        logger.info(f"Locked {locked_count} cost entries for vehicle {vehicle_id}")
        return locked_count

    async def record_vehicle_sale(
        self, data: VehicleSaleRequest, sold_by: UUID
    ) -> dict:
        """
        Record vehicle sale and lock costs

        Returns:
            Sale summary with profit calculation
        """
        # Get vehicle
        vehicle = await self.db.get(Bicycle, data.vehicle_id)
        if not vehicle:
            raise ValueError(f"Vehicle {data.vehicle_id} not found")

        # Get cost summary
        summary = await self._get_or_create_summary(data.vehicle_id)

        # Calculate profit
        total_cost = float(summary.total_cost)
        profit = float(data.sale_price) - total_cost
        profit_margin = (profit / float(data.sale_price)) * 100 if data.sale_price > 0 else 0

        # Update summary with sale details
        summary.sale_price = data.sale_price
        summary.profit = profit
        summary.profit_margin_pct = profit_margin

        # Update vehicle status
        vehicle.status = BicycleStatus.SOLD.value

        # Lock costs if requested
        if data.lock_costs:
            await self.lock_vehicle_costs(data.vehicle_id, sold_by)

        await self.db.commit()

        logger.info(
            f"Recorded sale of vehicle {data.vehicle_id}: "
            f"Sale=${data.sale_price}, Cost=${total_cost}, Profit=${profit}"
        )

        return {
            "vehicle_id": data.vehicle_id,
            "sale_price": float(data.sale_price),
            "total_cost": total_cost,
            "profit": profit,
            "profit_margin_pct": profit_margin,
            "sold_at": data.sold_at,
            "costs_locked": data.lock_costs,
        }

    async def _get_or_create_summary(self, vehicle_id: str) -> VehicleCostSummary:
        """Get or create cost summary for a vehicle"""
        stmt = select(VehicleCostSummary).where(
            VehicleCostSummary.vehicle_id == vehicle_id
        )
        result = await self.db.execute(stmt)
        summary = result.scalar_one_or_none()

        if not summary:
            summary = VehicleCostSummary(vehicle_id=vehicle_id)
            self.db.add(summary)
            await self.db.flush()

        return summary

    async def _update_summary(self, vehicle_id: str) -> None:
        """Recalculate and update cost summary for a vehicle"""
        summary = await self._get_or_create_summary(vehicle_id)

        # Get all cost entries
        stmt = select(VehicleCostLedger).where(
            VehicleCostLedger.vehicle_id == vehicle_id
        )
        result = await self.db.execute(stmt)
        entries = result.scalars().all()

        # Reset totals
        summary.purchase_cost = 0
        summary.transfer_cost = 0
        summary.repair_cost = 0
        summary.parts_cost = 0
        summary.admin_cost = 0
        summary.registration_cost = 0
        summary.insurance_cost = 0
        summary.transport_cost = 0
        summary.other_cost = 0
        summary.total_cost = 0
        summary.total_entries = len(entries)
        summary.locked_entries = 0

        # Aggregate by event type
        for entry in entries:
            amount = float(entry.amount)

            if entry.event_type == CostEventType.PURCHASE:
                summary.purchase_cost += amount
            elif entry.event_type == CostEventType.BRANCH_TRANSFER:
                summary.transfer_cost += amount
            elif entry.event_type == CostEventType.REPAIR_JOB:
                summary.repair_cost += amount
            elif entry.event_type == CostEventType.SPARE_PARTS:
                summary.parts_cost += amount
            elif entry.event_type == CostEventType.ADMIN_FEES:
                summary.admin_cost += amount
            elif entry.event_type == CostEventType.REGISTRATION:
                summary.registration_cost += amount
            elif entry.event_type == CostEventType.INSURANCE:
                summary.insurance_cost += amount
            elif entry.event_type in [CostEventType.TRANSPORT, CostEventType.FUEL]:
                summary.transport_cost += amount
            else:
                summary.other_cost += amount

            summary.total_cost += amount

            if entry.is_locked:
                summary.locked_entries += 1

        # Recalculate profit if sold
        if summary.sale_price is not None:
            summary.profit = float(summary.sale_price) - float(summary.total_cost)
            if summary.sale_price > 0:
                summary.profit_margin_pct = (summary.profit / float(summary.sale_price)) * 100

        summary.updated_at = datetime.utcnow()
        await self.db.flush()

    async def get_cost_statistics(
        self, filters: VehicleCostFilters
    ) -> dict:
        """Get cost statistics with filters"""
        stmt = select(VehicleCostLedger)

        # Apply filters (same as list_cost_entries)
        if filters.vehicle_id:
            stmt = stmt.where(VehicleCostLedger.vehicle_id == filters.vehicle_id)
        if filters.branch_id:
            stmt = stmt.where(VehicleCostLedger.branch_id == filters.branch_id)
        if filters.from_date:
            stmt = stmt.where(VehicleCostLedger.created_at >= filters.from_date)
        if filters.to_date:
            stmt = stmt.where(VehicleCostLedger.created_at <= filters.to_date)

        result = await self.db.execute(stmt)
        entries = result.scalars().all()

        # Calculate statistics
        total_amount = sum(float(e.amount) for e in entries)
        by_event = {}
        by_fund = {}

        for entry in entries:
            # By event type
            event_key = entry.event_type.value
            by_event[event_key] = by_event.get(event_key, 0) + float(entry.amount)

            # By fund source (would need to join to get name)
            fund_key = str(entry.fund_source_id)
            by_fund[fund_key] = by_fund.get(fund_key, 0) + float(entry.amount)

        # Count unique vehicles
        unique_vehicles = len(set(e.vehicle_id for e in entries))

        return {
            "total_vehicles": unique_vehicles,
            "total_cost_entries": len(entries),
            "total_amount": total_amount,
            "avg_cost_per_vehicle": total_amount / unique_vehicles if unique_vehicles > 0 else 0,
            "locked_entries": sum(1 for e in entries if e.is_locked),
            "pending_approval": sum(1 for e in entries if not e.is_approved),
            "by_event_type": by_event,
            "by_fund_source": by_fund,
        }
