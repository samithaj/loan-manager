"""Petty Cash service - Float and voucher management"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import Optional
from datetime import datetime, date
from decimal import Decimal
import uuid

from ..models.petty_cash import PettyCashFloat, PettyCashVoucher, VoucherType, VoucherStatus
from ..models.journal_entry import JournalEntry, JournalEntryLine, JournalEntryType
from ..schemas.petty_cash_schemas import (
    PettyCashFloatCreate,
    PettyCashFloatUpdate,
    PettyCashVoucherCreate,
    PettyCashVoucherUpdate,
)


class PettyCashService:
    """Service for managing petty cash floats and vouchers"""

    # ============= PettyCashFloat Methods =============

    @staticmethod
    async def get_float(db: AsyncSession, float_id: str) -> Optional[PettyCashFloat]:
        """Get petty cash float by ID"""
        result = await db.execute(
            select(PettyCashFloat).where(PettyCashFloat.id == float_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_floats(
        db: AsyncSession,
        branch_id: Optional[str] = None,
        custodian_id: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[list[PettyCashFloat], int]:
        """List petty cash floats with filters"""
        # Build query conditions
        conditions = []
        if branch_id:
            conditions.append(PettyCashFloat.branch_id == branch_id)
        if custodian_id:
            conditions.append(PettyCashFloat.custodian_id == custodian_id)
        if is_active is not None:
            conditions.append(PettyCashFloat.is_active == is_active)

        # Get total count
        count_query = select(func.count(PettyCashFloat.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar_one()

        # Get floats
        query = select(PettyCashFloat).order_by(
            PettyCashFloat.is_active.desc(),
            PettyCashFloat.created_at.desc()
        )
        if conditions:
            query = query.where(and_(*conditions))
        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        floats = result.scalars().all()

        return list(floats), total

    @staticmethod
    async def create_float(
        db: AsyncSession,
        float_data: PettyCashFloatCreate,
        created_by: str
    ) -> PettyCashFloat:
        """Create petty cash float"""
        float_obj = PettyCashFloat(
            id=str(uuid.uuid4()),
            **float_data.model_dump(),
            current_balance=float_data.opening_balance,
            created_by=created_by
        )
        db.add(float_obj)
        await db.commit()
        await db.refresh(float_obj)
        return float_obj

    @staticmethod
    async def update_float(
        db: AsyncSession,
        float_id: str,
        float_data: PettyCashFloatUpdate
    ) -> Optional[PettyCashFloat]:
        """Update petty cash float"""
        float_obj = await PettyCashService.get_float(db, float_id)
        if not float_obj:
            return None

        # Update fields
        update_data = float_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(float_obj, field, value)

        await db.commit()
        await db.refresh(float_obj)
        return float_obj

    @staticmethod
    async def reconcile_float(
        db: AsyncSession,
        float_id: str,
        actual_balance: Decimal,
        reconciled_by: str,
        reconciliation_notes: Optional[str] = None
    ) -> Optional[PettyCashFloat]:
        """Reconcile petty cash float"""
        float_obj = await PettyCashService.get_float(db, float_id)
        if not float_obj:
            return None

        float_obj.reconciled_balance = actual_balance
        float_obj.reconciled_at = datetime.utcnow()
        float_obj.reconciled_by = reconciled_by
        float_obj.reconciliation_notes = reconciliation_notes

        await db.commit()
        await db.refresh(float_obj)
        return float_obj

    # ============= PettyCashVoucher Methods =============

    @staticmethod
    async def get_voucher(db: AsyncSession, voucher_id: str) -> Optional[PettyCashVoucher]:
        """Get petty cash voucher by ID"""
        result = await db.execute(
            select(PettyCashVoucher).where(PettyCashVoucher.id == voucher_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_vouchers(
        db: AsyncSession,
        float_id: Optional[str] = None,
        branch_id: Optional[str] = None,
        voucher_type: Optional[str] = None,
        status: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[list[PettyCashVoucher], int]:
        """List petty cash vouchers with filters"""
        # Build query conditions
        conditions = []
        if float_id:
            conditions.append(PettyCashVoucher.petty_cash_float_id == float_id)
        if branch_id:
            conditions.append(PettyCashVoucher.branch_id == branch_id)
        if voucher_type:
            conditions.append(PettyCashVoucher.voucher_type == voucher_type)
        if status:
            conditions.append(PettyCashVoucher.status == status)
        if date_from:
            conditions.append(PettyCashVoucher.voucher_date >= date_from)
        if date_to:
            conditions.append(PettyCashVoucher.voucher_date <= date_to)

        # Get total count
        count_query = select(func.count(PettyCashVoucher.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar_one()

        # Get vouchers
        query = select(PettyCashVoucher).order_by(
            PettyCashVoucher.voucher_date.desc(),
            PettyCashVoucher.created_at.desc()
        )
        if conditions:
            query = query.where(and_(*conditions))
        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        vouchers = result.scalars().all()

        return list(vouchers), total

    @staticmethod
    async def generate_voucher_number(
        db: AsyncSession,
        branch_id: str,
        voucher_date: date
    ) -> str:
        """Generate voucher number in format: PCV-BRANCH-YYYY-NNNN"""
        year = voucher_date.year

        # Get the count of vouchers for this branch and year
        count_result = await db.execute(
            select(func.count(PettyCashVoucher.id)).where(
                and_(
                    PettyCashVoucher.branch_id == branch_id,
                    func.extract('year', PettyCashVoucher.voucher_date) == year
                )
            )
        )
        count = count_result.scalar_one()

        # Get branch code (use last 4 chars of branch_id for now)
        branch_code = branch_id[-4:].upper()

        # Generate number with padding
        voucher_number = f"PCV-{branch_code}-{year}-{count + 1:04d}"
        return voucher_number

    @staticmethod
    async def create_voucher(
        db: AsyncSession,
        voucher_data: PettyCashVoucherCreate,
        created_by: str
    ) -> PettyCashVoucher:
        """Create petty cash voucher with number generation"""
        # Generate voucher number
        voucher_number = await PettyCashService.generate_voucher_number(
            db, voucher_data.branch_id, voucher_data.voucher_date
        )

        # Verify float exists and is active
        float_obj = await PettyCashService.get_float(db, voucher_data.petty_cash_float_id)
        if not float_obj:
            raise ValueError("Petty cash float not found")
        if not float_obj.is_active:
            raise ValueError("Petty cash float is not active")

        voucher = PettyCashVoucher(
            id=str(uuid.uuid4()),
            voucher_number=voucher_number,
            **voucher_data.model_dump(),
            status=VoucherStatus.DRAFT.value,
            created_by=created_by
        )
        db.add(voucher)
        await db.commit()
        await db.refresh(voucher)
        return voucher

    @staticmethod
    async def update_voucher(
        db: AsyncSession,
        voucher_id: str,
        voucher_data: PettyCashVoucherUpdate
    ) -> Optional[PettyCashVoucher]:
        """Update petty cash voucher (DRAFT only)"""
        voucher = await PettyCashService.get_voucher(db, voucher_id)
        if not voucher:
            return None

        # Can only update DRAFT vouchers
        if voucher.status != VoucherStatus.DRAFT.value:
            raise ValueError(f"Cannot update voucher with status {voucher.status}")

        # Update fields
        update_data = voucher_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == 'voucher_type' and value is not None:
                setattr(voucher, field, value.value)
            elif value is not None:
                setattr(voucher, field, value)

        await db.commit()
        await db.refresh(voucher)
        return voucher

    @staticmethod
    async def delete_voucher(db: AsyncSession, voucher_id: str) -> bool:
        """Delete petty cash voucher (DRAFT only)"""
        voucher = await PettyCashService.get_voucher(db, voucher_id)
        if not voucher:
            return False

        # Can only delete DRAFT vouchers
        if voucher.status != VoucherStatus.DRAFT.value:
            raise ValueError(f"Cannot delete voucher with status {voucher.status}")

        await db.delete(voucher)
        await db.commit()
        return True

    @staticmethod
    async def approve_voucher(
        db: AsyncSession,
        voucher_id: str,
        approved_by: str
    ) -> Optional[PettyCashVoucher]:
        """Approve petty cash voucher"""
        voucher = await PettyCashService.get_voucher(db, voucher_id)
        if not voucher:
            return None

        # Can only approve DRAFT vouchers
        if voucher.status != VoucherStatus.DRAFT.value:
            raise ValueError(f"Cannot approve voucher with status {voucher.status}")

        # Approve the voucher
        voucher.approve(approved_by)
        await db.commit()
        await db.refresh(voucher)

        return voucher

    @staticmethod
    async def reject_voucher(
        db: AsyncSession,
        voucher_id: str,
        rejected_by: str,
        rejection_reason: str
    ) -> Optional[PettyCashVoucher]:
        """Reject petty cash voucher"""
        voucher = await PettyCashService.get_voucher(db, voucher_id)
        if not voucher:
            return None

        # Can only reject DRAFT vouchers
        if voucher.status != VoucherStatus.DRAFT.value:
            raise ValueError(f"Cannot reject voucher with status {voucher.status}")

        # Reject the voucher
        voucher.reject(rejected_by, rejection_reason)
        await db.commit()
        await db.refresh(voucher)

        return voucher

    @staticmethod
    async def post_voucher_to_journal(
        db: AsyncSession,
        voucher_id: str,
        petty_cash_account_id: str,
        expense_account_id: str,
        posted_by: str
    ) -> Optional[JournalEntry]:
        """
        Post approved voucher to journal
        Creates a journal entry for the voucher and updates float balance
        """
        voucher = await PettyCashService.get_voucher(db, voucher_id)
        if not voucher:
            return None

        # Can only post APPROVED vouchers
        if voucher.status != VoucherStatus.APPROVED.value:
            raise ValueError(f"Cannot post voucher with status {voucher.status}")

        # Check if already posted
        if voucher.journal_entry_id:
            raise ValueError("Voucher has already been posted to journal")

        # Create journal entry
        from .journal_entry_service import JournalEntryService

        entry_number = await JournalEntryService.generate_entry_number(db, voucher.voucher_date)

        # Determine debit/credit based on voucher type
        if voucher.voucher_type == VoucherType.DISBURSEMENT.value:
            # Disbursement: Debit expense, Credit petty cash
            debit_account = expense_account_id
            credit_account = petty_cash_account_id
        else:
            # Receipt: Debit petty cash, Credit expense/revenue account
            debit_account = petty_cash_account_id
            credit_account = expense_account_id

        entry = JournalEntry(
            id=str(uuid.uuid4()),
            entry_number=entry_number,
            entry_date=voucher.voucher_date,
            entry_type=JournalEntryType.PETTY_CASH.value,
            description=f"Petty Cash Voucher: {voucher.voucher_number} - {voucher.description}",
            reference_number=voucher.voucher_number,
            reference_type="PETTY_CASH_VOUCHER",
            reference_id=voucher.id,
            branch_id=voucher.branch_id,
            total_debit=voucher.amount,
            total_credit=voucher.amount,
            status="POSTED",
            created_by=posted_by,
            posted_at=datetime.utcnow(),
            posted_by=posted_by
        )
        db.add(entry)

        # Create journal entry lines
        debit_line = JournalEntryLine(
            id=str(uuid.uuid4()),
            journal_entry_id=entry.id,
            account_id=debit_account,
            description=voucher.description,
            debit_amount=voucher.amount,
            credit_amount=None
        )
        db.add(debit_line)

        credit_line = JournalEntryLine(
            id=str(uuid.uuid4()),
            journal_entry_id=entry.id,
            account_id=credit_account,
            description=voucher.description,
            debit_amount=None,
            credit_amount=voucher.amount
        )
        db.add(credit_line)

        # Update voucher with journal entry reference
        voucher.post_to_journal(entry.id)

        # Update float balance
        float_obj = await PettyCashService.get_float(db, voucher.petty_cash_float_id)
        if float_obj:
            if voucher.voucher_type == VoucherType.DISBURSEMENT.value:
                float_obj.current_balance -= voucher.amount
            else:
                float_obj.current_balance += voucher.amount

        await db.commit()
        await db.refresh(entry)

        return entry
