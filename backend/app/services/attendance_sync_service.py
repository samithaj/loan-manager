"""
Attendance Sync Service
Automatically creates and manages attendance records for approved leave applications
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID
from datetime import datetime, date, timedelta
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
import secrets

from ..models.hr_leave import LeaveApplication, LeaveStatus
from ..models.hr_attendance import AttendanceRecord, AttendanceStatus


class AttendanceSyncError(Exception):
    """Raised when attendance sync operation fails"""
    pass


class AttendanceSyncService:
    """Service for syncing approved leaves with attendance records"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def sync_approved_leave(
        self, leave_application: LeaveApplication
    ) -> list[AttendanceRecord]:
        """
        Create attendance records for an approved leave application

        Args:
            leave_application: Approved leave application

        Returns:
            List of created attendance records

        Raises:
            AttendanceSyncError: If sync fails
        """
        # Only sync if leave is approved
        if leave_application.status not in [
            LeaveStatus.APPROVED.value,
            LeaveStatus.APPROVED_HO.value,
        ]:
            raise AttendanceSyncError(
                f"Leave application {leave_application.id} is not in approved status"
            )

        # Get all dates in leave period
        dates = self._get_leave_dates(
            leave_application.start_date, leave_application.end_date
        )

        # Determine attendance status
        attendance_status = (
            AttendanceStatus.HALF_DAY.value
            if leave_application.is_half_day
            else AttendanceStatus.ON_LEAVE.value
        )

        created_records = []

        for leave_date in dates:
            # Check if attendance record already exists
            existing = await self._get_attendance_record(
                leave_application.user_id, leave_date
            )

            if existing:
                # Update existing record
                existing.status = attendance_status
                existing.notes = f"Auto-synced from leave application: {leave_application.id}"
                existing.updated_at = datetime.utcnow()
                created_records.append(existing)
                logger.info(
                    f"Updated attendance record for user {leave_application.user_id} on {leave_date}"
                )
            else:
                # Create new attendance record
                record = AttendanceRecord(
                    id=f"ATT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}",
                    user_id=leave_application.user_id,
                    date=leave_date,
                    status=attendance_status,
                    notes=f"Auto-created from leave application: {leave_application.id}",
                    work_hours=0.0 if not leave_application.is_half_day else 4.0,
                )
                self.db.add(record)
                created_records.append(record)
                logger.info(
                    f"Created attendance record for user {leave_application.user_id} on {leave_date}"
                )

        await self.db.flush()

        logger.info(
            f"Synced {len(created_records)} attendance records for leave {leave_application.id}"
        )

        return created_records

    async def remove_leave_attendance(
        self, leave_application: LeaveApplication
    ) -> int:
        """
        Remove or revert attendance records when leave is cancelled

        Args:
            leave_application: Cancelled leave application

        Returns:
            Number of attendance records affected

        Raises:
            AttendanceSyncError: If removal fails
        """
        # Get all dates in leave period
        dates = self._get_leave_dates(
            leave_application.start_date, leave_application.end_date
        )

        affected_count = 0

        for leave_date in dates:
            # Get attendance record
            record = await self._get_attendance_record(
                leave_application.user_id, leave_date
            )

            if record:
                # Check if this record was created by the leave application
                if record.notes and leave_application.id in record.notes:
                    # Check if attendance record is locked (e.g., after payroll cut-off)
                    if await self._is_attendance_locked(record.date):
                        logger.warning(
                            f"Attendance record for {record.date} is locked, cannot revert"
                        )
                        raise AttendanceSyncError(
                            f"Cannot revert attendance for {record.date} - period is locked"
                        )

                    # Revert to ABSENT status
                    record.status = AttendanceStatus.ABSENT.value
                    record.notes = f"Leave cancelled. Previous note: {record.notes}"
                    record.work_hours = 0.0
                    record.updated_at = datetime.utcnow()
                    affected_count += 1

                    logger.info(
                        f"Reverted attendance record for user {leave_application.user_id} on {leave_date}"
                    )

        await self.db.flush()

        logger.info(
            f"Reverted {affected_count} attendance records for cancelled leave {leave_application.id}"
        )

        return affected_count

    async def update_leave_attendance(
        self,
        leave_application: LeaveApplication,
        old_start_date: date,
        old_end_date: date,
    ) -> dict:
        """
        Update attendance records when leave dates are modified

        Args:
            leave_application: Updated leave application
            old_start_date: Previous start date
            old_end_date: Previous end date

        Returns:
            Dict with counts of removed, added, and unchanged records
        """
        # Get old and new date ranges
        old_dates = set(self._get_leave_dates(old_start_date, old_end_date))
        new_dates = set(
            self._get_leave_dates(
                leave_application.start_date, leave_application.end_date
            )
        )

        # Dates to remove (in old but not in new)
        dates_to_remove = old_dates - new_dates

        # Dates to add (in new but not in old)
        dates_to_add = new_dates - old_dates

        # Dates unchanged (in both)
        dates_unchanged = old_dates & new_dates

        removed_count = 0
        added_count = 0

        # Remove attendance for dates no longer in leave
        for leave_date in dates_to_remove:
            record = await self._get_attendance_record(
                leave_application.user_id, leave_date
            )
            if record and record.notes and leave_application.id in record.notes:
                record.status = AttendanceStatus.ABSENT.value
                record.notes = f"Leave modified. Previous note: {record.notes}"
                record.work_hours = 0.0
                removed_count += 1

        # Add attendance for new dates
        attendance_status = (
            AttendanceStatus.HALF_DAY.value
            if leave_application.is_half_day
            else AttendanceStatus.ON_LEAVE.value
        )

        for leave_date in dates_to_add:
            existing = await self._get_attendance_record(
                leave_application.user_id, leave_date
            )

            if existing:
                existing.status = attendance_status
                existing.notes = (
                    f"Auto-synced from updated leave application: {leave_application.id}"
                )
                existing.work_hours = (
                    4.0 if leave_application.is_half_day else 0.0
                )
            else:
                record = AttendanceRecord(
                    id=f"ATT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}",
                    user_id=leave_application.user_id,
                    date=leave_date,
                    status=attendance_status,
                    notes=f"Auto-created from updated leave application: {leave_application.id}",
                    work_hours=4.0 if leave_application.is_half_day else 0.0,
                )
                self.db.add(record)

            added_count += 1

        await self.db.flush()

        logger.info(
            f"Updated attendance for leave {leave_application.id}: "
            f"{removed_count} removed, {added_count} added, {len(dates_unchanged)} unchanged"
        )

        return {
            "removed": removed_count,
            "added": added_count,
            "unchanged": len(dates_unchanged),
        }

    async def bulk_sync_approved_leaves(
        self, start_date: date, end_date: date, user_id: Optional[UUID] = None
    ) -> dict:
        """
        Bulk sync all approved leaves in a date range

        Args:
            start_date: Start date of range
            end_date: End date of range
            user_id: Optional user ID filter

        Returns:
            Dict with sync statistics
        """
        # Build query for approved leaves in date range
        stmt = select(LeaveApplication).where(
            and_(
                LeaveApplication.status.in_(
                    [LeaveStatus.APPROVED.value, LeaveStatus.APPROVED_HO.value]
                ),
                LeaveApplication.start_date <= end_date,
                LeaveApplication.end_date >= start_date,
            )
        )

        if user_id:
            stmt = stmt.where(LeaveApplication.user_id == str(user_id))

        result = await self.db.execute(stmt)
        leave_applications = result.scalars().all()

        total_synced = 0
        total_errors = 0

        for leave_app in leave_applications:
            try:
                records = await self.sync_approved_leave(leave_app)
                total_synced += len(records)
            except AttendanceSyncError as e:
                logger.error(f"Failed to sync leave {leave_app.id}: {e}")
                total_errors += 1

        await self.db.commit()

        logger.info(
            f"Bulk sync completed: {total_synced} records synced, {total_errors} errors"
        )

        return {
            "total_leaves_processed": len(leave_applications),
            "total_records_synced": total_synced,
            "total_errors": total_errors,
        }

    def _get_leave_dates(self, start_date: date, end_date: date) -> list[date]:
        """
        Get all dates in leave period (inclusive)

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            List of dates
        """
        dates = []
        current_date = start_date

        while current_date <= end_date:
            dates.append(current_date)
            current_date += timedelta(days=1)

        return dates

    async def _get_attendance_record(
        self, user_id: UUID, record_date: date
    ) -> Optional[AttendanceRecord]:
        """
        Get attendance record for user on specific date

        Args:
            user_id: User UUID
            record_date: Date to check

        Returns:
            Attendance record if exists, None otherwise
        """
        stmt = select(AttendanceRecord).where(
            and_(
                AttendanceRecord.user_id == str(user_id),
                AttendanceRecord.date == record_date,
            )
        )

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _is_attendance_locked(self, record_date: date) -> bool:
        """
        Check if attendance record for date is locked (e.g., after payroll cutoff)

        Args:
            record_date: Date to check

        Returns:
            True if locked, False otherwise

        Note:
            This is a placeholder implementation.
            In production, you'd check against payroll periods or cutoff dates.
        """
        # Simple implementation: Lock records older than 30 days
        cutoff_date = datetime.now().date() - timedelta(days=30)
        return record_date < cutoff_date

    async def get_sync_status(self, leave_id: str) -> dict:
        """
        Get sync status for a leave application

        Args:
            leave_id: Leave application ID

        Returns:
            Dict with sync status information
        """
        leave_app = await self.db.get(LeaveApplication, leave_id)
        if not leave_app:
            raise AttendanceSyncError(f"Leave application {leave_id} not found")

        dates = self._get_leave_dates(leave_app.start_date, leave_app.end_date)

        synced_count = 0
        not_synced_count = 0
        locked_count = 0

        for leave_date in dates:
            record = await self._get_attendance_record(leave_app.user_id, leave_date)

            if record:
                if record.notes and leave_id in record.notes:
                    synced_count += 1
                    if await self._is_attendance_locked(leave_date):
                        locked_count += 1
                else:
                    not_synced_count += 1
            else:
                not_synced_count += 1

        return {
            "leave_id": leave_id,
            "total_days": len(dates),
            "synced_days": synced_count,
            "not_synced_days": not_synced_count,
            "locked_days": locked_count,
            "can_modify": locked_count == 0,
        }
