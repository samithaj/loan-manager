"""
Bill Number Generator Service
Generates unique bill numbers in format: <BRANCH_CODE>-<FUND_CODE>-<YYYYMMDD>-<SEQ>
Example: BD-PC-20251122-0041
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Tuple
from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from ..models.bill_number_sequence import BillNumberSequence
from ..models.branch import Branch
from ..models.fund_source import FundSource


class BillNumberService:
    """Service for generating unique bill numbers"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_bill_number(
        self,
        branch_id: UUID,
        fund_source_id: UUID,
        transaction_date: date | None = None,
    ) -> str:
        """
        Generate a unique bill number for a transaction

        Args:
            branch_id: Branch where transaction occurs
            fund_source_id: Fund source for the transaction
            transaction_date: Date of transaction (defaults to today)

        Returns:
            Bill number string (e.g., "BD-PC-20251122-0041")
        """
        if transaction_date is None:
            transaction_date = date.today()

        # Get branch code
        branch = await self.db.get(Branch, branch_id)
        if not branch:
            raise ValueError(f"Branch {branch_id} not found")

        # Get fund source code
        fund_source = await self.db.get(FundSource, fund_source_id)
        if not fund_source:
            raise ValueError(f"Fund source {fund_source_id} not found")

        # Get or create sequence record
        sequence_number = await self._get_next_sequence(
            branch_id, fund_source_id, transaction_date
        )

        # Format date as YYYYMMDD
        date_str = transaction_date.strftime("%Y%m%d")

        # Build bill number
        bill_no = f"{branch.code}-{fund_source.code}-{date_str}-{sequence_number:04d}"

        logger.info(f"Generated bill number: {bill_no}")
        return bill_no

    async def _get_next_sequence(
        self, branch_id: UUID, fund_source_id: UUID, sequence_date: date
    ) -> int:
        """
        Get next sequence number for branch + fund + date combination
        Uses row-level locking to prevent duplicates
        """
        # Try to find existing sequence record
        stmt = (
            select(BillNumberSequence)
            .where(
                BillNumberSequence.branch_id == branch_id,
                BillNumberSequence.fund_source_id == fund_source_id,
                BillNumberSequence.sequence_date == sequence_date,
            )
            .with_for_update()  # Row-level lock
        )

        result = await self.db.execute(stmt)
        sequence_record = result.scalar_one_or_none()

        if sequence_record:
            # Increment existing sequence
            new_sequence = sequence_record.current_sequence + 1
            sequence_record.current_sequence = new_sequence
            sequence_record.last_generated_at = date.today()
        else:
            # Create new sequence record
            new_sequence = 1
            sequence_record = BillNumberSequence(
                branch_id=branch_id,
                fund_source_id=fund_source_id,
                sequence_date=sequence_date,
                current_sequence=new_sequence,
                last_generated_at=date.today(),
            )
            self.db.add(sequence_record)

        await self.db.flush()

        return new_sequence

    async def validate_bill_number(self, bill_no: str) -> Tuple[bool, str]:
        """
        Validate bill number format and components

        Returns:
            (is_valid, error_message)
        """
        try:
            parts = bill_no.split("-")
            if len(parts) != 4:
                return False, "Bill number must have 4 parts separated by '-'"

            branch_code, fund_code, date_str, seq_str = parts

            # Validate branch code
            stmt = select(Branch).where(Branch.code == branch_code)
            result = await self.db.execute(stmt)
            if not result.scalar_one_or_none():
                return False, f"Invalid branch code: {branch_code}"

            # Validate fund code
            stmt = select(FundSource).where(FundSource.code == fund_code)
            result = await self.db.execute(stmt)
            if not result.scalar_one_or_none():
                return False, f"Invalid fund code: {fund_code}"

            # Validate date format
            try:
                datetime.strptime(date_str, "%Y%m%d")
            except ValueError:
                return False, f"Invalid date format: {date_str}"

            # Validate sequence
            try:
                seq_num = int(seq_str)
                if seq_num <= 0 or seq_num > 9999:
                    return False, "Sequence must be between 1 and 9999"
            except ValueError:
                return False, f"Invalid sequence number: {seq_str}"

            return True, ""

        except Exception as e:
            return False, f"Invalid bill number format: {str(e)}"

    async def parse_bill_number(self, bill_no: str) -> dict:
        """
        Parse bill number into components

        Returns:
            Dictionary with branch_code, fund_code, date, sequence
        """
        parts = bill_no.split("-")
        if len(parts) != 4:
            raise ValueError("Invalid bill number format")

        branch_code, fund_code, date_str, seq_str = parts

        return {
            "branch_code": branch_code,
            "fund_code": fund_code,
            "date": datetime.strptime(date_str, "%Y%m%d").date(),
            "sequence": int(seq_str),
            "original": bill_no,
        }
