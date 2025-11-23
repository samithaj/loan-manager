"""Audit service for logging changes"""

from datetime import datetime
from typing import Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc

from ..models.audit_log import AuditLog, AuditAction


class AuditService:
    """Service for managing audit logs"""

    @staticmethod
    async def log_action(
        db: AsyncSession,
        entity_type: str,
        entity_id: str,
        action: str,
        username: str,
        user_id: Optional[str] = None,
        user_role: Optional[str] = None,
        old_values: Optional[dict[str, Any]] = None,
        new_values: Optional[dict[str, Any]] = None,
        changes_summary: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> AuditLog:
        """
        Log an audit action

        Args:
            db: Database session
            entity_type: Type of entity (e.g., "JournalEntry", "PettyCashVoucher")
            entity_id: ID of the entity
            action: Action performed (CREATE, UPDATE, DELETE, etc.)
            username: Username who performed the action
            user_id: Optional user ID
            user_role: Optional user role at time of action
            old_values: Previous values (for UPDATE/DELETE)
            new_values: New values (for CREATE/UPDATE)
            changes_summary: Human-readable summary of changes
            ip_address: IP address of the request
            user_agent: User agent string
            metadata: Additional metadata

        Returns:
            Created AuditLog entry
        """
        audit_log = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            username=username,
            user_id=user_id,
            user_role=user_role,
            old_values=old_values,
            new_values=new_values,
            changes_summary=changes_summary,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata,
            timestamp=datetime.utcnow(),
        )

        db.add(audit_log)
        await db.commit()
        await db.refresh(audit_log)

        return audit_log

    @staticmethod
    async def get_entity_history(
        db: AsyncSession,
        entity_type: str,
        entity_id: str,
        limit: int = 100,
    ) -> list[AuditLog]:
        """
        Get audit history for a specific entity

        Args:
            db: Database session
            entity_type: Type of entity
            entity_id: ID of the entity
            limit: Maximum number of records to return

        Returns:
            List of audit log entries
        """
        result = await db.execute(
            select(AuditLog)
            .where(
                and_(
                    AuditLog.entity_type == entity_type,
                    AuditLog.entity_id == entity_id,
                )
            )
            .order_by(desc(AuditLog.timestamp))
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_user_activity(
        db: AsyncSession,
        username: Optional[str] = None,
        user_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 100,
    ) -> list[AuditLog]:
        """
        Get audit logs for a specific user

        Args:
            db: Database session
            username: Username to filter by
            user_id: User ID to filter by
            date_from: Start date filter
            date_to: End date filter
            limit: Maximum number of records to return

        Returns:
            List of audit log entries
        """
        conditions = []

        if username:
            conditions.append(AuditLog.username == username)
        if user_id:
            conditions.append(AuditLog.user_id == user_id)
        if date_from:
            conditions.append(AuditLog.timestamp >= date_from)
        if date_to:
            conditions.append(AuditLog.timestamp <= date_to)

        query = select(AuditLog)
        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(desc(AuditLog.timestamp)).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_recent_activity(
        db: AsyncSession,
        entity_type: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 100,
    ) -> list[AuditLog]:
        """
        Get recent audit activity

        Args:
            db: Database session
            entity_type: Filter by entity type
            action: Filter by action type
            limit: Maximum number of records to return

        Returns:
            List of recent audit log entries
        """
        conditions = []

        if entity_type:
            conditions.append(AuditLog.entity_type == entity_type)
        if action:
            conditions.append(AuditLog.action == action)

        query = select(AuditLog)
        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(desc(AuditLog.timestamp)).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def search_audit_logs(
        db: AsyncSession,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        action: Optional[str] = None,
        username: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[AuditLog], int]:
        """
        Search audit logs with multiple filters

        Args:
            db: Database session
            entity_type: Filter by entity type
            entity_id: Filter by entity ID
            action: Filter by action
            username: Filter by username
            date_from: Start date filter
            date_to: End date filter
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            Tuple of (audit logs, total count)
        """
        conditions = []

        if entity_type:
            conditions.append(AuditLog.entity_type == entity_type)
        if entity_id:
            conditions.append(AuditLog.entity_id == entity_id)
        if action:
            conditions.append(AuditLog.action == action)
        if username:
            conditions.append(AuditLog.username == username)
        if date_from:
            conditions.append(AuditLog.timestamp >= date_from)
        if date_to:
            conditions.append(AuditLog.timestamp <= date_to)

        # Build query
        query = select(AuditLog)
        if conditions:
            query = query.where(and_(*conditions))

        # Get total count
        from sqlalchemy import func
        count_query = select(func.count()).select_from(AuditLog)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await db.execute(count_query)
        total_count = count_result.scalar() or 0

        # Get paginated results
        query = query.order_by(desc(AuditLog.timestamp)).limit(limit).offset(offset)
        result = await db.execute(query)
        logs = list(result.scalars().all())

        return logs, total_count

    @staticmethod
    def generate_changes_summary(old_values: dict[str, Any], new_values: dict[str, Any]) -> str:
        """
        Generate a human-readable summary of changes

        Args:
            old_values: Previous values
            new_values: New values

        Returns:
            Human-readable summary string
        """
        if not old_values:
            return f"Created with {len(new_values)} fields"

        changes = []
        for key, new_val in new_values.items():
            old_val = old_values.get(key)
            if old_val != new_val:
                changes.append(f"{key}: {old_val} → {new_val}")

        if not changes:
            return "No changes detected"

        return "; ".join(changes)
