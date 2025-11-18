"""
Stock Number Service

Handles generation and assignment of stock numbers for bicycles.
Stock number format: {COMPANY_ID}/{BRANCH_ID}/ST/{RUNNING_NUMBER}
Example: MA/WW/ST/2066
"""

from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import secrets

from ..models import (
    StockNumberSequence, StockNumberAssignment,
    Bicycle
)


class StockNumberService:
    """Service for managing stock number sequences and assignments"""

    @staticmethod
    async def generate_stock_number(
        db: AsyncSession,
        company_id: str,
        branch_id: str
    ) -> tuple[int, str]:
        """
        Generate next stock number for company/branch.

        Args:
            db: Database session
            company_id: Company ID (e.g., 'MA', 'IN')
            branch_id: Branch/Office ID

        Returns:
            Tuple of (running_number, full_stock_number)
            Example: (2066, "MA/WW/ST/2066")
        """
        # Get or create sequence
        result = await db.execute(
            select(StockNumberSequence).where(
                StockNumberSequence.company_id == company_id,
                StockNumberSequence.branch_id == branch_id
            )
        )
        sequence = result.scalar_one_or_none()

        if not sequence:
            # Create new sequence
            sequence = StockNumberSequence(
                company_id=company_id,
                branch_id=branch_id,
                current_number=0
            )
            db.add(sequence)
            await db.flush()

        # Increment counter
        next_number = sequence.current_number + 1
        sequence.current_number = next_number
        sequence.last_assigned_at = datetime.utcnow()

        # Format: MA/WW/ST/2066
        full_stock_number = f"{company_id}/{branch_id}/ST/{next_number:04d}"

        return next_number, full_stock_number

    @staticmethod
    async def assign_stock_number(
        db: AsyncSession,
        bicycle_id: str,
        company_id: str,
        branch_id: str,
        reason: str,
        notes: str = None
    ) -> StockNumberAssignment:
        """
        Assign new stock number to bicycle.
        Automatically releases previous assignment if exists.

        Args:
            db: Database session
            bicycle_id: Bicycle ID
            company_id: Company ID
            branch_id: Branch ID
            reason: Assignment reason (PURCHASE, TRANSFER_IN, RETURN_FROM_GARAGE)
            notes: Optional notes

        Returns:
            StockNumberAssignment object
        """
        # Release previous assignment
        await db.execute(
            update(StockNumberAssignment)
            .where(
                StockNumberAssignment.bicycle_id == bicycle_id,
                StockNumberAssignment.released_date.is_(None)
            )
            .values(released_date=datetime.utcnow())
        )

        # Generate new stock number
        running_number, full_stock_number = await StockNumberService.generate_stock_number(
            db, company_id, branch_id
        )

        # Create assignment
        assignment_id = f"SNA-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"
        assignment = StockNumberAssignment(
            id=assignment_id,
            bicycle_id=bicycle_id,
            company_id=company_id,
            branch_id=branch_id,
            running_number=running_number,
            full_stock_number=full_stock_number,
            assigned_date=datetime.utcnow(),
            assignment_reason=reason,
            notes=notes
        )
        db.add(assignment)

        # Update bicycle's cached stock number
        await db.execute(
            update(Bicycle)
            .where(Bicycle.id == bicycle_id)
            .values(
                current_stock_number=full_stock_number,
                current_branch_id=branch_id
            )
        )

        return assignment

    @staticmethod
    async def get_current_assignment(
        db: AsyncSession,
        bicycle_id: str
    ) -> StockNumberAssignment | None:
        """
        Get current active stock number assignment for a bicycle.

        Args:
            db: Database session
            bicycle_id: Bicycle ID

        Returns:
            StockNumberAssignment or None
        """
        result = await db.execute(
            select(StockNumberAssignment)
            .where(
                StockNumberAssignment.bicycle_id == bicycle_id,
                StockNumberAssignment.released_date.is_(None)
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_assignment_history(
        db: AsyncSession,
        bicycle_id: str
    ) -> list[StockNumberAssignment]:
        """
        Get all stock number assignments for a bicycle (full history).

        Args:
            db: Database session
            bicycle_id: Bicycle ID

        Returns:
            List of StockNumberAssignment objects, ordered by date desc
        """
        result = await db.execute(
            select(StockNumberAssignment)
            .where(StockNumberAssignment.bicycle_id == bicycle_id)
            .order_by(StockNumberAssignment.assigned_date.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def release_assignment(
        db: AsyncSession,
        bicycle_id: str
    ) -> bool:
        """
        Manually release current stock number assignment.

        Args:
            db: Database session
            bicycle_id: Bicycle ID

        Returns:
            True if assignment was released, False if no active assignment
        """
        result = await db.execute(
            update(StockNumberAssignment)
            .where(
                StockNumberAssignment.bicycle_id == bicycle_id,
                StockNumberAssignment.released_date.is_(None)
            )
            .values(released_date=datetime.utcnow())
        )

        return result.rowcount > 0
