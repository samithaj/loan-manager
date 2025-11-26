"""
Transfer Service

Handles bicycle transfers between branches with approval workflow:
1. Initiate transfer (PENDING)
2. Approve transfer (APPROVED -> IN_TRANSIT) - assigns new stock number
3. Complete transfer (COMPLETED) - posts costs to VehicleCostLedger
Or reject at any stage
"""

from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import secrets
from typing import TYPE_CHECKING
from decimal import Decimal
from uuid import UUID

from ..models import Bicycle, BicycleTransfer, Office
from .stock_number_service import StockNumberService

if TYPE_CHECKING:
    from .vehicle_cost_service import VehicleCostService


class TransferService:
    """Service for managing bicycle transfers between branches"""

    @staticmethod
    async def initiate_transfer(
        db: AsyncSession,
        bicycle_id: str,
        to_branch_id: str,
        requested_by: str,
        transfer_reason: str = None,
        reference_doc_number: str = None
    ) -> BicycleTransfer:
        """
        Create new transfer request.

        Args:
            db: Database session
            bicycle_id: Bicycle ID
            to_branch_id: Destination branch ID
            requested_by: User ID or name of requester
            transfer_reason: Reason for transfer
            reference_doc_number: Physical transfer document number

        Returns:
            BicycleTransfer object in PENDING status

        Raises:
            ValueError: If bike status is invalid or already at target branch
        """
        # Get bike
        result = await db.execute(
            select(Bicycle).where(Bicycle.id == bicycle_id)
        )
        bike = result.scalar_one()

        # Validate
        if bike.status not in ["IN_STOCK", "AVAILABLE", "MAINTENANCE"]:
            raise ValueError(f"Cannot transfer bicycle in status {bike.status}")

        if bike.current_branch_id == to_branch_id:
            raise ValueError("Bike already at target branch")

        # Verify target branch exists
        result = await db.execute(
            select(Office).where(Office.id == to_branch_id)
        )
        to_branch = result.scalar_one_or_none()
        if not to_branch:
            raise ValueError(f"Target branch {to_branch_id} not found")

        # Get current stock number
        current_assignment = await StockNumberService.get_current_assignment(db, bicycle_id)
        from_stock_number = current_assignment.full_stock_number if current_assignment else None

        # Create transfer
        transfer_id = f"TRF-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"
        transfer = BicycleTransfer(
            id=transfer_id,
            bicycle_id=bicycle_id,
            from_branch_id=bike.current_branch_id,
            to_branch_id=to_branch_id,
            from_stock_number=from_stock_number,
            status="PENDING",
            requested_by=requested_by,
            requested_at=datetime.utcnow(),
            transfer_reason=transfer_reason,
            reference_doc_number=reference_doc_number,
        )
        db.add(transfer)

        return transfer

    @staticmethod
    async def approve_transfer(
        db: AsyncSession,
        transfer_id: str,
        approved_by: str
    ) -> BicycleTransfer:
        """
        Approve transfer and assign new stock number for destination branch.
        Updates status to IN_TRANSIT.

        Args:
            db: Database session
            transfer_id: Transfer ID
            approved_by: User ID or name of approver

        Returns:
            BicycleTransfer object with updated status and new stock number

        Raises:
            ValueError: If transfer is not in PENDING status
        """
        # Get transfer
        result = await db.execute(
            select(BicycleTransfer).where(BicycleTransfer.id == transfer_id)
        )
        transfer = result.scalar_one()

        # Approve (will raise ValueError if not PENDING)
        transfer.approve(approved_by)

        # Get target branch company
        result = await db.execute(
            select(Office).where(Office.id == transfer.to_branch_id)
        )
        to_branch = result.scalar_one()

        if not to_branch.company_id:
            raise ValueError(f"Target branch {transfer.to_branch_id} is not linked to a company")

        # Assign new stock number
        assignment = await StockNumberService.assign_stock_number(
            db,
            bicycle_id=transfer.bicycle_id,
            company_id=to_branch.company_id,
            branch_id=transfer.to_branch_id,
            reason="TRANSFER_IN",
            notes=f"Transfer from {transfer.from_branch_id} (Transfer ID: {transfer_id})"
        )

        transfer.to_stock_number = assignment.full_stock_number
        transfer.status = "IN_TRANSIT"

        return transfer

    @staticmethod
    async def complete_transfer(
        db: AsyncSession,
        transfer_id: str,
        completed_by: str,
        post_to_cost_ledger: bool = True
    ) -> BicycleTransfer:
        """
        Mark transfer as completed and optionally post costs to VehicleCostLedger.
        Updates transfer status to COMPLETED.

        Args:
            db: Database session
            transfer_id: Transfer ID
            completed_by: User ID or name of person completing transfer
            post_to_cost_ledger: Whether to post transfer costs to VehicleCostLedger (default: True)

        Returns:
            BicycleTransfer object with COMPLETED status

        Raises:
            ValueError: If transfer is not in APPROVED/IN_TRANSIT status
        """
        result = await db.execute(
            select(BicycleTransfer).where(BicycleTransfer.id == transfer_id)
        )
        transfer = result.scalar_one()

        # Complete (will raise ValueError if not in correct status)
        transfer.complete(completed_by)

        # Post costs to VehicleCostLedger if enabled and transfer has costs
        if post_to_cost_ledger and transfer.transfer_cost and transfer.transfer_cost > 0:
            try:
                from .vehicle_cost_service import VehicleCostService
                from ..schemas.vehicle_cost_schemas import VehicleCostCreate
                from ..models.vehicle_cost_ledger import CostEventType

                # Get the destination branch to find fund source
                to_branch = await db.get(Office, transfer.to_branch_id)
                if not to_branch:
                    raise ValueError(f"Destination branch {transfer.to_branch_id} not found")

                # Use a default fund source or get from branch configuration
                # For now, we'll need to query for an active fund source
                from ..models.fund_source import FundSource
                fund_result = await db.execute(
                    select(FundSource)
                    .where(FundSource.is_active == True)
                    .limit(1)
                )
                fund_source = fund_result.scalar_one_or_none()

                if not fund_source:
                    # Skip cost posting if no fund source available
                    # Log warning but don't fail the transfer
                    import logging
                    logging.warning(f"No active fund source found for transfer cost posting: {transfer_id}")
                else:
                    # Create cost entry
                    cost_service = VehicleCostService(db)

                    # Build description from cost breakdown if available
                    description_parts = [f"Transfer from {transfer.from_branch_id} to {transfer.to_branch_id}"]
                    if transfer.cost_breakdown:
                        breakdown_items = [
                            f"{k.replace('_', ' ').title()}: {v}"
                            for k, v in transfer.cost_breakdown.items()
                            if v and v > 0
                        ]
                        if breakdown_items:
                            description_parts.append(f"Breakdown: {', '.join(breakdown_items)}")

                    cost_data = VehicleCostCreate(
                        vehicle_id=transfer.bicycle_id,
                        branch_id=transfer.to_branch_id,  # Post to destination branch
                        event_type=CostEventType.BRANCH_TRANSFER,
                        fund_source_id=fund_source.id,
                        amount=Decimal(str(transfer.transfer_cost)),
                        currency="LKR",
                        description="; ".join(description_parts),
                        reference_table="bicycle_transfers",
                        reference_id=transfer_id,
                        notes=f"Transfer completed by {completed_by}. Transfer reason: {transfer.transfer_reason or 'N/A'}",
                        meta_json=transfer.cost_breakdown or {},
                        transaction_date=date.today()
                    )

                    # Resolve completed_by to UUID if it's a username
                    try:
                        completed_by_uuid = UUID(completed_by)
                    except (ValueError, AttributeError):
                        # Try to resolve as username
                        from ..models.user import User
                        user_result = await db.execute(
                            select(User).where(User.username == completed_by)
                        )
                        user = user_result.scalar_one_or_none()
                        completed_by_uuid = user.id if user else UUID('00000000-0000-0000-0000-000000000000')

                    await cost_service.create_cost_entry(
                        data=cost_data,
                        created_by=completed_by_uuid,
                        auto_generate_bill=True
                    )

            except Exception as e:
                # Log the error but don't fail the transfer completion
                import logging
                logging.error(f"Failed to post transfer costs to VehicleCostLedger: {str(e)}")
                # Transfer is still marked as completed

        return transfer

    @staticmethod
    async def reject_transfer(
        db: AsyncSession,
        transfer_id: str,
        rejected_by: str,
        reason: str
    ) -> BicycleTransfer:
        """
        Reject transfer request.
        Updates status to REJECTED and may reverse stock number assignment.

        Args:
            db: Database session
            transfer_id: Transfer ID
            rejected_by: User ID or name of person rejecting
            reason: Rejection reason

        Returns:
            BicycleTransfer object with REJECTED status

        Raises:
            ValueError: If transfer is already completed
        """
        result = await db.execute(
            select(BicycleTransfer).where(BicycleTransfer.id == transfer_id)
        )
        transfer = result.scalar_one()

        # If transfer was approved and stock number was assigned, we should revert it
        # Get the bike to check current branch
        if transfer.status == "IN_TRANSIT":
            result = await db.execute(
                select(Bicycle).where(Bicycle.id == transfer.bicycle_id)
            )
            bike = result.scalar_one()

            # Get the from branch to reassign original stock number
            result = await db.execute(
                select(Office).where(Office.id == transfer.from_branch_id)
            )
            from_branch = result.scalar_one()

            if from_branch.company_id:
                # Reassign stock number back to original branch
                await StockNumberService.assign_stock_number(
                    db,
                    bicycle_id=transfer.bicycle_id,
                    company_id=from_branch.company_id,
                    branch_id=transfer.from_branch_id,
                    reason="TRANSFER_REJECTED",
                    notes=f"Transfer {transfer_id} rejected, reverting to original branch"
                )

        # Reject (will raise ValueError if already completed)
        transfer.reject(rejected_by, reason)

        return transfer

    @staticmethod
    async def cancel_transfer(
        db: AsyncSession,
        transfer_id: str,
        cancelled_by: str,
        reason: str = None
    ) -> BicycleTransfer:
        """
        Cancel a pending transfer.

        Args:
            db: Database session
            transfer_id: Transfer ID
            cancelled_by: User ID or name of person cancelling
            reason: Cancellation reason

        Returns:
            BicycleTransfer object with CANCELLED status

        Raises:
            ValueError: If transfer is not in PENDING status
        """
        result = await db.execute(
            select(BicycleTransfer).where(BicycleTransfer.id == transfer_id)
        )
        transfer = result.scalar_one()

        if transfer.status != "PENDING":
            raise ValueError(f"Can only cancel PENDING transfers, current status: {transfer.status}")

        transfer.status = "CANCELLED"
        transfer.rejected_by = cancelled_by
        transfer.rejected_at = datetime.utcnow()
        transfer.rejection_reason = reason or "Transfer cancelled"

        return transfer

    @staticmethod
    async def get_pending_transfers(
        db: AsyncSession,
        branch_id: str = None
    ) -> list[BicycleTransfer]:
        """
        Get all pending transfers, optionally filtered by branch.

        Args:
            db: Database session
            branch_id: Optional branch ID to filter (from or to)

        Returns:
            List of BicycleTransfer objects in PENDING status
        """
        query = select(BicycleTransfer).where(
            BicycleTransfer.status == "PENDING"
        )

        if branch_id:
            query = query.where(
                (BicycleTransfer.from_branch_id == branch_id) |
                (BicycleTransfer.to_branch_id == branch_id)
            )

        query = query.order_by(BicycleTransfer.requested_at.desc())

        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_transfer_history(
        db: AsyncSession,
        bicycle_id: str
    ) -> list[BicycleTransfer]:
        """
        Get transfer history for a specific bicycle.

        Args:
            db: Database session
            bicycle_id: Bicycle ID

        Returns:
            List of BicycleTransfer objects ordered by date desc
        """
        result = await db.execute(
            select(BicycleTransfer)
            .where(BicycleTransfer.bicycle_id == bicycle_id)
            .order_by(BicycleTransfer.requested_at.desc())
        )
        return list(result.scalars().all())
