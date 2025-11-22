"""
Leave Approval Service
Handles multi-level approval routing, decisions, and workflow logic
"""
from __future__ import annotations

from typing import Optional, Sequence, Tuple
from uuid import UUID, uuid4
from datetime import datetime, date
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from ..models.hr_leave import LeaveApplication, LeaveType, LeaveStatus, LeaveBalance
from ..models.leave_approval import (
    LeaveApproval,
    LeaveAuditLog,
    LeavePolicy,
    ApprovalDecision,
    ApproverRole,
)
from ..models.user import User
from ..models.branch import Branch


class LeaveApprovalError(Exception):
    """Raised when leave approval operation fails"""
    pass


class LeaveApprovalService:
    """Service for managing leave approval workflows"""

    # Valid state transitions
    ALLOWED_TRANSITIONS = {
        LeaveStatus.DRAFT: [LeaveStatus.PENDING, LeaveStatus.CANCELLED],
        LeaveStatus.PENDING: [
            LeaveStatus.APPROVED_BRANCH,
            LeaveStatus.APPROVED_HO,
            LeaveStatus.APPROVED,
            LeaveStatus.REJECTED,
            LeaveStatus.NEEDS_INFO,
            LeaveStatus.CANCELLED,
        ],
        LeaveStatus.NEEDS_INFO: [LeaveStatus.PENDING, LeaveStatus.CANCELLED],
        LeaveStatus.APPROVED_BRANCH: [
            LeaveStatus.APPROVED_HO,
            LeaveStatus.APPROVED,
            LeaveStatus.REJECTED,
            LeaveStatus.CANCELLED,
        ],
        LeaveStatus.APPROVED_HO: [LeaveStatus.CANCELLED],  # Rarely cancelled after HO approval
        LeaveStatus.APPROVED: [LeaveStatus.CANCELLED],  # Rarely cancelled after approval
        LeaveStatus.REJECTED: [],  # Terminal state
        LeaveStatus.CANCELLED: [],  # Terminal state
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    async def submit_leave_request(
        self, leave_id: str, submitted_by: UUID
    ) -> LeaveApplication:
        """
        Submit leave request for approval (DRAFT -> PENDING)
        Automatically routes to appropriate approvers
        """
        leave = await self._get_leave(leave_id)
        if not leave:
            raise LeaveApprovalError("Leave request not found")

        # Validate transition
        self._validate_transition(leave.status, LeaveStatus.PENDING.value)

        # Update status
        old_status = leave.status
        leave.status = LeaveStatus.PENDING.value

        # Create audit log
        await self._create_audit_log(
            leave_id=leave_id,
            actor_id=submitted_by,
            action="SUBMITTED",
            old_status=old_status,
            new_status=LeaveStatus.PENDING.value,
        )

        await self.db.commit()
        await self.db.refresh(leave)

        logger.info(f"Leave request {leave_id} submitted for approval")
        return leave

    async def approve_by_branch_manager(
        self,
        leave_id: str,
        approver_id: UUID,
        notes: Optional[str] = None,
    ) -> LeaveApplication:
        """
        Approve leave request as Branch Manager
        Routes to HO if required, otherwise marks as fully approved
        """
        leave = await self._get_leave(leave_id)
        if not leave:
            raise LeaveApprovalError("Leave request not found")

        # Get leave type to check if HO approval needed
        leave_type = await self.db.get(LeaveType, leave.leave_type_id)
        if not leave_type:
            raise LeaveApprovalError("Leave type not found")

        # Get policy (if exists)
        policy = await self._get_policy(leave.branch_id, leave.leave_type_id)

        # Determine next status
        requires_ho = leave_type.requires_ho_approval or (policy and policy.requires_ho_approval)

        if requires_ho:
            new_status = LeaveStatus.APPROVED_BRANCH.value
        else:
            new_status = LeaveStatus.APPROVED.value

        # Validate transition
        self._validate_transition(leave.status, new_status)

        # Update leave
        old_status = leave.status
        leave.status = new_status
        leave.branch_approver_id = str(approver_id)
        leave.branch_approved_at = datetime.utcnow()

        if new_status == LeaveStatus.APPROVED.value:
            leave.approver_id = str(approver_id)
            leave.approved_at = datetime.utcnow()

        # Create approval record
        approval = LeaveApproval(
            leave_request_id=leave_id,
            approver_id=approver_id,
            approver_role=ApproverRole.BRANCH_MANAGER,
            decision=ApprovalDecision.APPROVED,
            notes=notes,
        )
        self.db.add(approval)

        # Create audit log
        await self._create_audit_log(
            leave_id=leave_id,
            actor_id=approver_id,
            action="APPROVED_BRANCH",
            old_status=old_status,
            new_status=new_status,
            payload={"notes": notes} if notes else {},
        )

        await self.db.commit()
        await self.db.refresh(leave)

        logger.info(f"Leave request {leave_id} approved by branch manager")
        return leave

    async def approve_by_head_manager(
        self,
        leave_id: str,
        approver_id: UUID,
        notes: Optional[str] = None,
    ) -> LeaveApplication:
        """
        Approve leave request as Head Office Manager (final approval)
        """
        leave = await self._get_leave(leave_id)
        if not leave:
            raise LeaveApprovalError("Leave request not found")

        new_status = LeaveStatus.APPROVED_HO.value

        # Validate transition
        self._validate_transition(leave.status, new_status)

        # Update leave
        old_status = leave.status
        leave.status = new_status
        leave.ho_approver_id = str(approver_id)
        leave.ho_approved_at = datetime.utcnow()
        leave.approver_id = str(approver_id)
        leave.approved_at = datetime.utcnow()

        # Create approval record
        approval = LeaveApproval(
            leave_request_id=leave_id,
            approver_id=approver_id,
            approver_role=ApproverRole.HEAD_MANAGER,
            decision=ApprovalDecision.APPROVED,
            notes=notes,
        )
        self.db.add(approval)

        # Create audit log
        await self._create_audit_log(
            leave_id=leave_id,
            actor_id=approver_id,
            action="APPROVED_HO",
            old_status=old_status,
            new_status=new_status,
            payload={"notes": notes} if notes else {},
        )

        await self.db.commit()
        await self.db.refresh(leave)

        logger.info(f"Leave request {leave_id} approved by head office")
        return leave

    async def reject_leave(
        self,
        leave_id: str,
        approver_id: UUID,
        approver_role: ApproverRole,
        notes: str,
    ) -> LeaveApplication:
        """
        Reject leave request
        """
        leave = await self._get_leave(leave_id)
        if not leave:
            raise LeaveApprovalError("Leave request not found")

        new_status = LeaveStatus.REJECTED.value

        # Validate transition
        self._validate_transition(leave.status, new_status)

        # Update leave
        old_status = leave.status
        leave.status = new_status
        leave.approver_id = str(approver_id)
        leave.approved_at = datetime.utcnow()
        leave.approver_notes = notes

        # Create approval record
        approval = LeaveApproval(
            leave_request_id=leave_id,
            approver_id=approver_id,
            approver_role=approver_role,
            decision=ApprovalDecision.REJECTED,
            notes=notes,
        )
        self.db.add(approval)

        # Create audit log
        await self._create_audit_log(
            leave_id=leave_id,
            actor_id=approver_id,
            action="REJECTED",
            old_status=old_status,
            new_status=new_status,
            payload={"notes": notes},
        )

        await self.db.commit()
        await self.db.refresh(leave)

        logger.info(f"Leave request {leave_id} rejected")
        return leave

    async def request_more_info(
        self,
        leave_id: str,
        approver_id: UUID,
        approver_role: ApproverRole,
        notes: str,
    ) -> LeaveApplication:
        """
        Request more information from employee
        """
        leave = await self._get_leave(leave_id)
        if not leave:
            raise LeaveApprovalError("Leave request not found")

        new_status = LeaveStatus.NEEDS_INFO.value

        # Validate transition
        self._validate_transition(leave.status, new_status)

        # Update leave
        old_status = leave.status
        leave.status = new_status
        leave.approver_notes = notes

        # Create approval record
        approval = LeaveApproval(
            leave_request_id=leave_id,
            approver_id=approver_id,
            approver_role=approver_role,
            decision=ApprovalDecision.NEEDS_INFO,
            notes=notes,
        )
        self.db.add(approval)

        # Create audit log
        await self._create_audit_log(
            leave_id=leave_id,
            actor_id=approver_id,
            action="NEEDS_INFO",
            old_status=old_status,
            new_status=new_status,
            payload={"notes": notes},
        )

        await self.db.commit()
        await self.db.refresh(leave)

        logger.info(f"More information requested for leave {leave_id}")
        return leave

    async def cancel_leave(
        self, leave_id: str, cancelled_by: UUID, reason: str
    ) -> LeaveApplication:
        """
        Cancel leave request (by employee or admin)
        """
        leave = await self._get_leave(leave_id)
        if not leave:
            raise LeaveApprovalError("Leave request not found")

        new_status = LeaveStatus.CANCELLED.value

        # Validate transition
        self._validate_transition(leave.status, new_status)

        # Update leave
        old_status = leave.status
        leave.status = new_status
        leave.cancelled_at = datetime.utcnow()

        # Create audit log
        await self._create_audit_log(
            leave_id=leave_id,
            actor_id=cancelled_by,
            action="CANCELLED",
            old_status=old_status,
            new_status=new_status,
            payload={"reason": reason},
        )

        await self.db.commit()
        await self.db.refresh(leave)

        logger.info(f"Leave request {leave_id} cancelled")
        return leave

    async def get_approval_queue(
        self,
        approver_id: UUID,
        approver_role: ApproverRole,
        branch_id: Optional[UUID] = None,
        status_filter: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[Sequence[LeaveApplication], int]:
        """
        Get approval queue for a manager
        """
        stmt = select(LeaveApplication)

        # Filter by status based on role
        if approver_role == ApproverRole.BRANCH_MANAGER:
            # Branch managers see PENDING leaves in their branch
            if status_filter:
                stmt = stmt.where(LeaveApplication.status == status_filter)
            else:
                stmt = stmt.where(LeaveApplication.status == LeaveStatus.PENDING.value)

            if branch_id:
                stmt = stmt.where(LeaveApplication.branch_id == str(branch_id))

        elif approver_role == ApproverRole.HEAD_MANAGER:
            # Head managers see APPROVED_BRANCH leaves needing HO approval
            if status_filter:
                stmt = stmt.where(LeaveApplication.status == status_filter)
            else:
                stmt = stmt.where(
                    or_(
                        LeaveApplication.status == LeaveStatus.APPROVED_BRANCH.value,
                        LeaveApplication.status == LeaveStatus.PENDING.value,  # Can also approve directly
                    )
                )

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await self.db.scalar(count_stmt) or 0

        # Apply pagination
        stmt = stmt.order_by(LeaveApplication.created_at.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        # Execute query
        result = await self.db.execute(stmt)
        items = result.scalars().all()

        return items, total

    async def get_leave_timeline(self, leave_id: str) -> list[LeaveAuditLog]:
        """Get complete timeline of leave request"""
        stmt = (
            select(LeaveAuditLog)
            .where(LeaveAuditLog.leave_request_id == leave_id)
            .order_by(LeaveAuditLog.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _get_leave(self, leave_id: str) -> Optional[LeaveApplication]:
        """Get leave application by ID"""
        return await self.db.get(LeaveApplication, leave_id)

    async def _get_policy(
        self, branch_id: Optional[str], leave_type_id: str
    ) -> Optional[LeavePolicy]:
        """Get leave policy for branch and leave type"""
        # First try branch-specific policy
        if branch_id:
            stmt = select(LeavePolicy).where(
                and_(
                    LeavePolicy.branch_id == UUID(branch_id),
                    LeavePolicy.leave_type_id == leave_type_id,
                    LeavePolicy.is_active == True,
                )
            )
            result = await self.db.execute(stmt)
            policy = result.scalar_one_or_none()
            if policy:
                return policy

        # Fall back to global policy
        stmt = select(LeavePolicy).where(
            and_(
                LeavePolicy.branch_id.is_(None),
                LeavePolicy.leave_type_id == leave_type_id,
                LeavePolicy.is_active == True,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    def _validate_transition(self, current_status: str, new_status: str) -> None:
        """Validate if status transition is allowed"""
        current = LeaveStatus(current_status)
        new = LeaveStatus(new_status)

        allowed = self.ALLOWED_TRANSITIONS.get(current, [])
        if new not in allowed:
            raise LeaveApprovalError(
                f"Invalid transition from {current.value} to {new.value}"
            )

    async def _create_audit_log(
        self,
        leave_id: str,
        actor_id: UUID,
        action: str,
        old_status: Optional[str] = None,
        new_status: Optional[str] = None,
        payload: Optional[dict] = None,
    ) -> None:
        """Create an audit log entry"""
        audit = LeaveAuditLog(
            leave_request_id=leave_id,
            actor_id=actor_id,
            action=action,
            old_status=old_status,
            new_status=new_status,
            payload_json=payload or {},
        )
        self.db.add(audit)
        await self.db.flush()
