"""Journal Entry service - Double-entry bookkeeping implementation"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from typing import Optional
from datetime import datetime, date
import uuid

from ..models.journal_entry import JournalEntry, JournalEntryLine, JournalEntryStatus, JournalEntryType
from ..models.chart_of_accounts import ChartOfAccounts
from ..schemas.accounting_schemas import (
    JournalEntryCreate,
    JournalEntryUpdate,
)


class JournalEntryService:
    """Service for managing journal entries"""

    @staticmethod
    async def get_entry(db: AsyncSession, entry_id: str) -> Optional[JournalEntry]:
        """Get journal entry by ID with lines"""
        result = await db.execute(
            select(JournalEntry)
            .options(selectinload(JournalEntry.lines))
            .where(JournalEntry.id == entry_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_entries(
        db: AsyncSession,
        entry_type: Optional[str] = None,
        status: Optional[str] = None,
        branch_id: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[list[JournalEntry], int]:
        """List journal entries with filters"""
        # Build query conditions
        conditions = []
        if entry_type:
            conditions.append(JournalEntry.entry_type == entry_type)
        if status:
            conditions.append(JournalEntry.status == status)
        if branch_id:
            conditions.append(JournalEntry.branch_id == branch_id)
        if date_from:
            conditions.append(JournalEntry.entry_date >= date_from)
        if date_to:
            conditions.append(JournalEntry.entry_date <= date_to)

        # Get total count
        count_query = select(func.count(JournalEntry.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar_one()

        # Get entries with lines
        query = (
            select(JournalEntry)
            .options(selectinload(JournalEntry.lines))
            .order_by(JournalEntry.entry_date.desc(), JournalEntry.created_at.desc())
        )
        if conditions:
            query = query.where(and_(*conditions))
        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        entries = result.scalars().all()

        return list(entries), total

    @staticmethod
    async def generate_entry_number(db: AsyncSession, entry_date: date) -> str:
        """Generate entry number in format: JE-YYYY-NNNN"""
        year = entry_date.year

        # Get the count of entries for this year
        count_result = await db.execute(
            select(func.count(JournalEntry.id)).where(
                func.extract('year', JournalEntry.entry_date) == year
            )
        )
        count = count_result.scalar_one()

        # Generate number with padding
        entry_number = f"JE-{year}-{count + 1:04d}"
        return entry_number

    @staticmethod
    async def validate_entry(
        db: AsyncSession,
        entry_data: JournalEntryCreate
    ) -> tuple[bool, Optional[str]]:
        """
        Validate journal entry
        Returns: (is_valid, error_message)
        """
        # Check minimum 2 lines
        if len(entry_data.lines) < 2:
            return False, "Journal entry must have at least 2 lines"

        # Check balanced entry
        total_debit = sum(line.debit_amount or 0 for line in entry_data.lines)
        total_credit = sum(line.credit_amount or 0 for line in entry_data.lines)

        if abs(total_debit - total_credit) > 0.01:
            return False, f"Entry is not balanced: debits={total_debit}, credits={total_credit}"

        # Validate all account IDs exist
        account_ids = {line.account_id for line in entry_data.lines}
        result = await db.execute(
            select(func.count(ChartOfAccounts.id)).where(
                ChartOfAccounts.id.in_(account_ids)
            )
        )
        account_count = result.scalar_one()

        if account_count != len(account_ids):
            return False, "One or more account IDs are invalid"

        # Check that accounts are not header accounts
        result = await db.execute(
            select(ChartOfAccounts).where(
                and_(
                    ChartOfAccounts.id.in_(account_ids),
                    ChartOfAccounts.is_header == True
                )
            )
        )
        header_accounts = result.scalars().all()

        if header_accounts:
            header_names = [acc.account_name for acc in header_accounts]
            return False, f"Cannot post to header accounts: {', '.join(header_names)}"

        return True, None

    @staticmethod
    async def create_entry(
        db: AsyncSession,
        entry_data: JournalEntryCreate,
        created_by: str
    ) -> JournalEntry:
        """Create journal entry with validation"""
        # Validate entry
        is_valid, error_message = await JournalEntryService.validate_entry(db, entry_data)
        if not is_valid:
            raise ValueError(error_message)

        # Generate entry number
        entry_number = await JournalEntryService.generate_entry_number(db, entry_data.entry_date)

        # Calculate totals
        total_debit = sum(line.debit_amount or 0 for line in entry_data.lines)
        total_credit = sum(line.credit_amount or 0 for line in entry_data.lines)

        # Create entry
        entry = JournalEntry(
            id=str(uuid.uuid4()),
            entry_number=entry_number,
            entry_date=entry_data.entry_date,
            entry_type=entry_data.entry_type.value,
            description=entry_data.description,
            reference_number=entry_data.reference_number,
            reference_type=entry_data.reference_type,
            reference_id=entry_data.reference_id,
            branch_id=entry_data.branch_id,
            total_debit=total_debit,
            total_credit=total_credit,
            status=JournalEntryStatus.DRAFT.value,
            created_by=created_by
        )
        db.add(entry)

        # Create lines
        for line_data in entry_data.lines:
            line = JournalEntryLine(
                id=str(uuid.uuid4()),
                journal_entry_id=entry.id,
                account_id=line_data.account_id,
                description=line_data.description,
                debit_amount=line_data.debit_amount,
                credit_amount=line_data.credit_amount
            )
            db.add(line)

        await db.commit()
        await db.refresh(entry)

        # Reload with lines
        result = await db.execute(
            select(JournalEntry)
            .options(selectinload(JournalEntry.lines))
            .where(JournalEntry.id == entry.id)
        )
        return result.scalar_one()

    @staticmethod
    async def update_entry(
        db: AsyncSession,
        entry_id: str,
        entry_data: JournalEntryUpdate
    ) -> Optional[JournalEntry]:
        """Update journal entry (DRAFT only)"""
        entry = await JournalEntryService.get_entry(db, entry_id)
        if not entry:
            return None

        # Can only update DRAFT entries
        if entry.status != JournalEntryStatus.DRAFT.value:
            raise ValueError(f"Cannot update entry with status {entry.status}")

        # Update entry fields
        update_data = entry_data.model_dump(exclude_unset=True, exclude={'lines'})
        for field, value in update_data.items():
            if field == 'entry_type' and value is not None:
                setattr(entry, field, value.value)
            elif value is not None:
                setattr(entry, field, value)

        # If lines are updated, recreate them
        if entry_data.lines is not None:
            # Validate new lines
            temp_create_data = JournalEntryCreate(
                entry_date=entry.entry_date,
                entry_type=JournalEntryType(entry.entry_type),
                description=entry.description,
                lines=entry_data.lines,
                branch_id=entry.branch_id
            )
            is_valid, error_message = await JournalEntryService.validate_entry(db, temp_create_data)
            if not is_valid:
                raise ValueError(error_message)

            # Delete existing lines
            for line in entry.lines:
                await db.delete(line)

            # Create new lines
            total_debit = 0
            total_credit = 0
            for line_data in entry_data.lines:
                line = JournalEntryLine(
                    id=str(uuid.uuid4()),
                    journal_entry_id=entry.id,
                    account_id=line_data.account_id,
                    description=line_data.description,
                    debit_amount=line_data.debit_amount,
                    credit_amount=line_data.credit_amount
                )
                db.add(line)
                total_debit += line_data.debit_amount or 0
                total_credit += line_data.credit_amount or 0

            entry.total_debit = total_debit
            entry.total_credit = total_credit

        await db.commit()
        await db.refresh(entry)

        # Reload with lines
        result = await db.execute(
            select(JournalEntry)
            .options(selectinload(JournalEntry.lines))
            .where(JournalEntry.id == entry.id)
        )
        return result.scalar_one()

    @staticmethod
    async def delete_entry(db: AsyncSession, entry_id: str) -> bool:
        """Delete journal entry (DRAFT only)"""
        entry = await JournalEntryService.get_entry(db, entry_id)
        if not entry:
            return False

        # Can only delete DRAFT entries
        if entry.status != JournalEntryStatus.DRAFT.value:
            raise ValueError(f"Cannot delete entry with status {entry.status}")

        # Delete lines first
        for line in entry.lines:
            await db.delete(line)

        # Delete entry
        await db.delete(entry)
        await db.commit()
        return True

    @staticmethod
    async def post_entry(
        db: AsyncSession,
        entry_id: str,
        posted_by: str
    ) -> Optional[JournalEntry]:
        """Post journal entry to ledger"""
        entry = await JournalEntryService.get_entry(db, entry_id)
        if not entry:
            return None

        # Can only post DRAFT entries
        if entry.status != JournalEntryStatus.DRAFT.value:
            raise ValueError(f"Cannot post entry with status {entry.status}")

        # Validate entry is balanced
        if not entry.is_balanced():
            raise ValueError("Cannot post unbalanced entry")

        # Post the entry
        entry.post(posted_by)
        await db.commit()
        await db.refresh(entry)

        return entry

    @staticmethod
    async def void_entry(
        db: AsyncSession,
        entry_id: str,
        voided_by: str,
        void_reason: str
    ) -> Optional[JournalEntry]:
        """Void a posted journal entry"""
        entry = await JournalEntryService.get_entry(db, entry_id)
        if not entry:
            return None

        # Can only void POSTED entries
        if entry.status != JournalEntryStatus.POSTED.value:
            raise ValueError(f"Cannot void entry with status {entry.status}")

        # Void the entry
        entry.void(voided_by, void_reason)
        await db.commit()
        await db.refresh(entry)

        return entry
