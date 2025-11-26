"""
Loan Application Service with state machine logic
"""
from __future__ import annotations

from typing import Optional, Sequence
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from ..models.loan_application import LoanApplication, ApplicationStatus
from ..models.loan_application_customer import LoanApplicationCustomer
from ..models.loan_application_vehicle import LoanApplicationVehicle
from ..models.loan_application_decision import LoanApplicationDecision, DecisionType
from ..models.loan_application_audit import LoanApplicationAudit
from ..models.loan_approval_threshold import LoanApprovalThreshold
from ..models.branch import Branch
from decimal import Decimal
from ..schemas.loan_application_schemas import (
    LoanApplicationCreate,
    LoanApplicationUpdate,
    CustomerUpdate,
    VehicleUpdate,
    DecisionCreate,
    LoanApplicationFilters,
)


class StateTransitionError(Exception):
    """Raised when an invalid state transition is attempted"""
    pass


class LoanApplicationService:
    """Service for managing loan applications with state machine logic"""

    # Valid state transitions
    ALLOWED_TRANSITIONS = {
        ApplicationStatus.DRAFT: [ApplicationStatus.SUBMITTED, ApplicationStatus.CANCELLED],
        ApplicationStatus.SUBMITTED: [ApplicationStatus.UNDER_REVIEW, ApplicationStatus.CANCELLED],
        ApplicationStatus.UNDER_REVIEW: [
            ApplicationStatus.NEEDS_MORE_INFO,
            ApplicationStatus.APPROVED,
            ApplicationStatus.REJECTED,
            ApplicationStatus.CANCELLED,
        ],
        ApplicationStatus.NEEDS_MORE_INFO: [ApplicationStatus.SUBMITTED, ApplicationStatus.CANCELLED],
        ApplicationStatus.APPROVED: [],  # Terminal state
        ApplicationStatus.REJECTED: [],  # Terminal state
        ApplicationStatus.CANCELLED: [],  # Terminal state
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _generate_application_number(self) -> str:
        """Generate unique application number (LA-YYYY-NNNN)"""
        year = datetime.utcnow().year
        prefix = f"LA-{year}-"

        # Get the last application number for this year
        stmt = select(func.max(LoanApplication.application_no)).where(
            LoanApplication.application_no.like(f"{prefix}%")
        )
        result = await self.db.execute(stmt)
        last_no = result.scalar()

        if last_no:
            # Extract sequence number and increment
            seq = int(last_no.split("-")[-1]) + 1
        else:
            seq = 1

        return f"{prefix}{seq:04d}"

    async def _create_audit_log(
        self,
        application_id: UUID,
        actor_user_id: Optional[UUID],
        action: str,
        from_status: Optional[str] = None,
        to_status: Optional[str] = None,
        payload: Optional[dict] = None,
    ) -> None:
        """Create an audit log entry"""
        audit = LoanApplicationAudit(
            application_id=application_id,
            actor_user_id=actor_user_id,
            action=action,
            from_status=from_status,
            to_status=to_status,
            payload_json=payload or {},
        )
        self.db.add(audit)

    def _validate_transition(self, current_status: ApplicationStatus, new_status: ApplicationStatus) -> None:
        """Validate if status transition is allowed"""
        allowed = self.ALLOWED_TRANSITIONS.get(current_status, [])
        if new_status not in allowed:
            raise StateTransitionError(
                f"Invalid transition from {current_status.value} to {new_status.value}"
            )

    async def create_application(
        self, data: LoanApplicationCreate, lmo_user_id: UUID
    ) -> LoanApplication:
        """Create a new loan application in DRAFT status"""
        # Generate application number
        app_no = await self._generate_application_number()

        # Create application
        application = LoanApplication(
            application_no=app_no,
            lmo_user_id=lmo_user_id,
            branch_id=data.branch_id,
            requested_amount=data.requested_amount,
            tenure_months=data.tenure_months,
            lmo_notes=data.lmo_notes,
            status=ApplicationStatus.DRAFT,
        )
        self.db.add(application)
        await self.db.flush()  # Get ID without committing

        # Create customer
        customer = LoanApplicationCustomer(
            application_id=application.id,
            **data.customer.model_dump()
        )
        self.db.add(customer)

        # Create vehicle
        vehicle = LoanApplicationVehicle(
            application_id=application.id,
            **data.vehicle.model_dump()
        )
        self.db.add(vehicle)

        # Create audit log
        await self._create_audit_log(
            application.id,
            lmo_user_id,
            "CREATED",
            to_status=ApplicationStatus.DRAFT.value,
            payload={"application_no": app_no},
        )

        await self.db.commit()
        await self.db.refresh(application)

        logger.info(f"Created loan application {app_no} by user {lmo_user_id}")
        return application

    async def get_application(self, application_id: UUID, load_relations: bool = True) -> Optional[LoanApplication]:
        """Get application by ID with optional eager loading"""
        stmt = select(LoanApplication).where(LoanApplication.id == application_id)

        if load_relations:
            stmt = stmt.options(
                selectinload(LoanApplication.customer),
                selectinload(LoanApplication.vehicle),
                selectinload(LoanApplication.branch),
                selectinload(LoanApplication.documents),
                selectinload(LoanApplication.decisions),
            )

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_applications(
        self,
        filters: LoanApplicationFilters,
        page: int = 1,
        page_size: int = 20,
        user_branch_id: Optional[UUID] = None,  # For branch filtering
    ) -> tuple[Sequence[LoanApplication], int]:
        """List applications with filters and pagination"""
        stmt = select(LoanApplication).options(
            selectinload(LoanApplication.customer),
            selectinload(LoanApplication.vehicle),
            selectinload(LoanApplication.branch),
        )

        # Apply filters
        if filters.status:
            stmt = stmt.where(LoanApplication.status == filters.status)

        if filters.branch_id:
            stmt = stmt.where(LoanApplication.branch_id == filters.branch_id)
        elif user_branch_id:  # User's branch filter (for branch-scoped access)
            stmt = stmt.where(LoanApplication.branch_id == user_branch_id)

        if filters.application_no:
            stmt = stmt.where(LoanApplication.application_no.ilike(f"%{filters.application_no}%"))

        if filters.nic:
            # Join with customer table
            stmt = stmt.join(LoanApplication.customer).where(
                LoanApplicationCustomer.nic.ilike(f"%{filters.nic}%")
            )

        if filters.chassis_no:
            # Join with vehicle table
            stmt = stmt.join(LoanApplication.vehicle).where(
                LoanApplicationVehicle.chassis_no.ilike(f"%{filters.chassis_no}%")
            )

        if filters.from_date:
            stmt = stmt.where(LoanApplication.created_at >= filters.from_date)

        if filters.to_date:
            stmt = stmt.where(LoanApplication.created_at <= filters.to_date)

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await self.db.scalar(count_stmt) or 0

        # Apply pagination
        stmt = stmt.order_by(LoanApplication.created_at.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        # Execute query
        result = await self.db.execute(stmt)
        items = result.scalars().all()

        return items, total

    async def update_application(
        self,
        application_id: UUID,
        data: LoanApplicationUpdate,
        actor_user_id: UUID,
    ) -> LoanApplication:
        """Update draft application details"""
        application = await self.get_application(application_id, load_relations=False)
        if not application:
            raise ValueError("Application not found")

        # Only allow updates in DRAFT or NEEDS_MORE_INFO status
        if application.status not in [ApplicationStatus.DRAFT, ApplicationStatus.NEEDS_MORE_INFO]:
            raise StateTransitionError(
                f"Cannot update application in {application.status.value} status"
            )

        # Update application fields
        if data.requested_amount is not None:
            application.requested_amount = data.requested_amount
        if data.tenure_months is not None:
            application.tenure_months = data.tenure_months
        if data.lmo_notes is not None:
            application.lmo_notes = data.lmo_notes

        # Update customer if provided
        if data.customer:
            customer = await self.db.get(LoanApplicationCustomer, application_id)
            if customer:
                for field, value in data.customer.model_dump(exclude_unset=True).items():
                    setattr(customer, field, value)

        # Update vehicle if provided
        if data.vehicle:
            vehicle = await self.db.get(LoanApplicationVehicle, application_id)
            if vehicle:
                for field, value in data.vehicle.model_dump(exclude_unset=True).items():
                    setattr(vehicle, field, value)

        # Create audit log
        await self._create_audit_log(
            application.id,
            actor_user_id,
            "UPDATED",
            payload=data.model_dump(exclude_unset=True),
        )

        await self.db.commit()
        await self.db.refresh(application)

        logger.info(f"Updated application {application.application_no}")
        return application

    async def submit_application(
        self, application_id: UUID, actor_user_id: UUID
    ) -> LoanApplication:
        """Submit application for review (DRAFT/NEEDS_MORE_INFO -> SUBMITTED)"""
        application = await self.get_application(application_id, load_relations=False)
        if not application:
            raise ValueError("Application not found")

        # Validate transition
        self._validate_transition(application.status, ApplicationStatus.SUBMITTED)

        old_status = application.status
        application.status = ApplicationStatus.SUBMITTED
        application.submitted_at = datetime.utcnow()

        # Create audit log
        await self._create_audit_log(
            application.id,
            actor_user_id,
            "SUBMITTED",
            from_status=old_status.value,
            to_status=ApplicationStatus.SUBMITTED.value,
        )

        await self.db.commit()
        await self.db.refresh(application)

        logger.info(f"Submitted application {application.application_no}")
        return application

    async def start_review(
        self, application_id: UUID, officer_user_id: UUID
    ) -> LoanApplication:
        """Start reviewing application (SUBMITTED -> UNDER_REVIEW)"""
        application = await self.get_application(application_id, load_relations=False)
        if not application:
            raise ValueError("Application not found")

        # Validate transition
        self._validate_transition(application.status, ApplicationStatus.UNDER_REVIEW)

        old_status = application.status
        application.status = ApplicationStatus.UNDER_REVIEW
        application.reviewed_at = datetime.utcnow()

        # Create audit log
        await self._create_audit_log(
            application.id,
            officer_user_id,
            "REVIEW_STARTED",
            from_status=old_status.value,
            to_status=ApplicationStatus.UNDER_REVIEW.value,
        )

        await self.db.commit()
        await self.db.refresh(application)

        logger.info(f"Started review of application {application.application_no}")
        return application

    async def make_decision(
        self,
        application_id: UUID,
        decision_data: DecisionCreate,
        officer_user_id: UUID,
    ) -> LoanApplication:
        """Make a decision on the application"""
        application = await self.get_application(application_id, load_relations=False)
        if not application:
            raise ValueError("Application not found")

        # Map decision type to status
        status_map = {
            DecisionType.APPROVED: ApplicationStatus.APPROVED,
            DecisionType.REJECTED: ApplicationStatus.REJECTED,
            DecisionType.NEEDS_MORE_INFO: ApplicationStatus.NEEDS_MORE_INFO,
        }
        new_status = status_map[decision_data.decision]

        # Validate transition
        self._validate_transition(application.status, new_status)

        old_status = application.status
        application.status = new_status
        application.decided_at = datetime.utcnow()

        # Create decision record
        decision = LoanApplicationDecision(
            application_id=application.id,
            officer_user_id=officer_user_id,
            decision=decision_data.decision,
            notes=decision_data.notes,
        )
        self.db.add(decision)

        # Create audit log
        await self._create_audit_log(
            application.id,
            officer_user_id,
            f"DECISION_{decision_data.decision.value}",
            from_status=old_status.value,
            to_status=new_status.value,
            payload={"notes": decision_data.notes},
        )

        await self.db.commit()
        await self.db.refresh(application)

        logger.info(
            f"Decision {decision_data.decision.value} made on application {application.application_no}"
        )
        return application

    async def cancel_application(
        self, application_id: UUID, actor_user_id: UUID, reason: str
    ) -> LoanApplication:
        """Cancel application"""
        application = await self.get_application(application_id, load_relations=False)
        if not application:
            raise ValueError("Application not found")

        # Validate transition
        self._validate_transition(application.status, ApplicationStatus.CANCELLED)

        old_status = application.status
        application.status = ApplicationStatus.CANCELLED

        # Create audit log
        await self._create_audit_log(
            application.id,
            actor_user_id,
            "CANCELLED",
            from_status=old_status.value,
            to_status=ApplicationStatus.CANCELLED.value,
            payload={"reason": reason},
        )

        await self.db.commit()
        await self.db.refresh(application)

        logger.info(f"Cancelled application {application.application_no}")
        return application

    async def get_timeline(self, application_id: UUID) -> list[LoanApplicationAudit]:
        """Get complete timeline of application events"""
        stmt = (
            select(LoanApplicationAudit)
            .where(LoanApplicationAudit.application_id == application_id)
            .order_by(LoanApplicationAudit.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ========================================================================
    # Multi-Level Approval Methods
    # ========================================================================

    async def _get_company_id_from_branch(self, branch_id: UUID) -> str:
        """Helper to get company_id from branch_id"""
        branch = await self.db.get(Branch, branch_id)
        if not branch:
            raise ValueError(f"Branch {branch_id} not found")
        return branch.company_id

    async def determine_required_approval_level(
        self,
        company_id: str,
        loan_amount: Decimal
    ) -> int:
        """
        Determine the highest approval level required for a given loan amount.

        Args:
            company_id: Company identifier
            loan_amount: Requested loan amount

        Returns:
            The highest approval level required (0 = initial review only)
        """
        stmt = (
            select(func.max(LoanApprovalThreshold.approval_level))
            .where(
                LoanApprovalThreshold.company_id == company_id,
                LoanApprovalThreshold.is_active == True,
                LoanApprovalThreshold.min_amount <= loan_amount,
                or_(
                    LoanApprovalThreshold.max_amount.is_(None),
                    LoanApprovalThreshold.max_amount > loan_amount
                )
            )
        )

        result = await self.db.execute(stmt)
        max_level = result.scalar_one_or_none()

        return max_level if max_level is not None else 0

    async def get_next_approval_threshold(
        self,
        company_id: str,
        loan_amount: Decimal,
        current_level: int
    ) -> Optional[LoanApprovalThreshold]:
        """
        Get the next approval threshold for a loan application.

        Args:
            company_id: Company identifier
            loan_amount: Requested loan amount
            current_level: Current approval level

        Returns:
            Next LoanApprovalThreshold or None if no more approvals needed
        """
        next_level = current_level + 1

        stmt = (
            select(LoanApprovalThreshold)
            .where(
                LoanApprovalThreshold.company_id == company_id,
                LoanApprovalThreshold.is_active == True,
                LoanApprovalThreshold.approval_level == next_level,
                LoanApprovalThreshold.min_amount <= loan_amount,
                or_(
                    LoanApprovalThreshold.max_amount.is_(None),
                    LoanApprovalThreshold.max_amount > loan_amount
                )
            )
            .order_by(LoanApprovalThreshold.approval_level)
            .limit(1)
        )

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def record_approval_decision(
        self,
        application_id: UUID,
        officer_user_id: UUID,
        decision_type: DecisionType,
        approval_level: int,
        notes: str,
        threshold_id: Optional[UUID] = None
    ) -> LoanApplicationDecision:
        """
        Record an approval decision at a specific approval level.

        Args:
            application_id: Application UUID
            officer_user_id: Approving officer's user ID
            decision_type: APPROVED, REJECTED, or NEEDS_MORE_INFO
            approval_level: The approval level this decision belongs to
            notes: Decision notes
            threshold_id: Optional threshold that triggered this level

        Returns:
            Created LoanApplicationDecision
        """
        decision = LoanApplicationDecision(
            application_id=application_id,
            officer_user_id=officer_user_id,
            decision=decision_type,
            notes=notes,
            approval_level=approval_level,
            threshold_id=threshold_id,
            is_auto_routed=False
        )

        self.db.add(decision)
        await self.db.flush()

        return decision

    async def advance_approval_level(
        self,
        application: LoanApplication,
        officer_user_id: UUID,
        notes: str
    ) -> tuple[LoanApplication, Optional[LoanApprovalThreshold]]:
        """
        Advance application to next approval level after approval.

        Args:
            application: LoanApplication instance
            officer_user_id: Approving officer
            notes: Approval notes

        Returns:
            Tuple of (updated application, next threshold or None)
        """
        # Get company ID
        company_id = await self._get_company_id_from_branch(application.branch_id)

        # Get next threshold
        next_threshold = await self.get_next_approval_threshold(
            company_id,
            Decimal(str(application.requested_amount)),
            application.current_approval_level
        )

        # Record approval decision at current level
        await self.record_approval_decision(
            application.id,
            officer_user_id,
            DecisionType.APPROVED,
            application.current_approval_level,
            notes,
            threshold_id=next_threshold.id if next_threshold else None
        )

        # Update approval progress
        progress = application.approval_progress or []
        progress.append({
            "level": application.current_approval_level,
            "status": "APPROVED",
            "by": str(officer_user_id),
            "at": datetime.utcnow().isoformat(),
            "notes": notes
        })
        application.approval_progress = progress

        # If there's a next level, advance to it
        if next_threshold:
            application.current_approval_level += 1

            # Create audit log for level advancement
            await self._create_audit_log(
                application.id,
                officer_user_id,
                f"APPROVED_LEVEL_{application.current_approval_level - 1}_ADVANCE_TO_{application.current_approval_level}",
                from_status=application.status.value,
                to_status=application.status.value,  # Status stays UNDER_REVIEW
                payload={
                    "previous_level": application.current_approval_level - 1,
                    "new_level": application.current_approval_level,
                    "next_approver_role": next_threshold.approver_role,
                    "notes": notes
                }
            )

            logger.info(
                f"Application {application.application_no} advanced to level {application.current_approval_level}"
            )
        else:
            # No more levels - final approval
            application.status = ApplicationStatus.APPROVED
            application.decided_at = datetime.utcnow()

            # Create audit log for final approval
            await self._create_audit_log(
                application.id,
                officer_user_id,
                "FINAL_APPROVAL",
                from_status=ApplicationStatus.UNDER_REVIEW.value,
                to_status=ApplicationStatus.APPROVED.value,
                payload={"final_level": application.current_approval_level, "notes": notes}
            )

            logger.info(
                f"Application {application.application_no} FULLY APPROVED at level {application.current_approval_level}"
            )

        await self.db.flush()
        return application, next_threshold

    async def reject_at_level(
        self,
        application: LoanApplication,
        officer_user_id: UUID,
        notes: str
    ) -> LoanApplication:
        """
        Reject application at current approval level.

        Args:
            application: LoanApplication instance
            officer_user_id: Rejecting officer
            notes: Rejection notes

        Returns:
            Updated application
        """
        # Record rejection decision
        await self.record_approval_decision(
            application.id,
            officer_user_id,
            DecisionType.REJECTED,
            application.current_approval_level,
            notes
        )

        # Update approval progress
        progress = application.approval_progress or []
        progress.append({
            "level": application.current_approval_level,
            "status": "REJECTED",
            "by": str(officer_user_id),
            "at": datetime.utcnow().isoformat(),
            "notes": notes
        })
        application.approval_progress = progress

        # Change status to REJECTED
        application.status = ApplicationStatus.REJECTED
        application.decided_at = datetime.utcnow()

        # Create audit log
        await self._create_audit_log(
            application.id,
            officer_user_id,
            f"REJECTED_AT_LEVEL_{application.current_approval_level}",
            from_status=ApplicationStatus.UNDER_REVIEW.value,
            to_status=ApplicationStatus.REJECTED.value,
            payload={"level": application.current_approval_level, "notes": notes}
        )

        logger.info(
            f"Application {application.application_no} REJECTED at level {application.current_approval_level}"
        )

        await self.db.flush()
        return application

    async def check_approval_permissions(
        self,
        application: LoanApplication,
        user_permissions: list[str]
    ) -> tuple[bool, Optional[str]]:
        """
        Check if user has permission to approve at current level.

        Args:
            application: LoanApplication instance
            user_permissions: List of user's permissions

        Returns:
            Tuple of (has_permission, required_permission)
        """
        # Get company ID
        company_id = await self._get_company_id_from_branch(application.branch_id)

        # Get current threshold
        stmt = (
            select(LoanApprovalThreshold)
            .where(
                LoanApprovalThreshold.company_id == company_id,
                LoanApprovalThreshold.is_active == True,
                LoanApprovalThreshold.approval_level == application.current_approval_level,
                LoanApprovalThreshold.min_amount <= application.requested_amount,
                or_(
                    LoanApprovalThreshold.max_amount.is_(None),
                    LoanApprovalThreshold.max_amount > application.requested_amount
                )
            )
        )

        result = await self.db.execute(stmt)
        threshold = result.scalar_one_or_none()

        if not threshold:
            return False, None

        # Check if user has required permission
        has_permission = threshold.approver_permission in user_permissions

        return has_permission, threshold.approver_permission
