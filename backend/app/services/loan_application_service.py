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
