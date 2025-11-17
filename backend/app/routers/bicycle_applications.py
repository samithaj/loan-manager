from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Depends, status, Header
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import Optional
import uuid

from ..db import SessionLocal
from ..models.bicycle import Bicycle, BicycleStatus
from ..models.bicycle_application import BicycleApplication, ApplicationStatus
from ..models.reference import Office
from ..models.idempotency import IdempotencyRecord
from ..rbac import require_permission, get_current_user, ROLE_BRANCH_MANAGER
from ..services import bicycle_service, notification_service


router = APIRouter(prefix="/v1", tags=["bicycle-applications"])


# ============================================================================
# Pydantic Models
# ============================================================================

class ApplicationCreateIn(BaseModel):
    """Customer application submission"""
    # Customer information
    full_name: str = Field(..., min_length=2, max_length=200)
    phone: str = Field(..., min_length=8, max_length=20)
    email: Optional[str] = Field(None, max_length=200)
    nip_number: Optional[str] = Field(None, max_length=50)

    # Address
    address_line1: str = Field(..., min_length=5, max_length=200)
    address_line2: Optional[str] = Field(None, max_length=200)
    city: str = Field(..., min_length=2, max_length=100)

    # Employment
    employer_name: Optional[str] = Field(None, max_length=200)
    monthly_income: Optional[float] = Field(None, ge=0)

    # Application details
    bicycle_id: str
    branch_id: str
    tenure_months: int = Field(..., ge=12, le=48)
    down_payment: float = Field(0, ge=0)


class ApplicationOut(BaseModel):
    """Application response for public/customer"""
    id: str
    status: str
    bicycle_id: str
    branch_id: str
    full_name: str
    phone: str
    email: Optional[str] = None
    tenure_months: int
    down_payment: float
    submitted_at: str
    loan_id: Optional[str] = None


class ApplicationDetailOut(BaseModel):
    """Detailed application response for staff"""
    id: str
    # Customer info
    full_name: str
    phone: str
    email: Optional[str] = None
    nip_number: Optional[str] = None
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    employer_name: Optional[str] = None
    monthly_income: Optional[float] = None
    # Application details
    bicycle_id: str
    branch_id: str
    tenure_months: int
    down_payment: float
    status: str
    notes: Optional[str] = None
    loan_id: Optional[str] = None
    # Audit
    submitted_at: str
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None


class ApplicationListResponse(BaseModel):
    """Paginated application list"""
    items: list[ApplicationDetailOut]
    total: int
    offset: int
    limit: int


class ApproveApplicationRequest(BaseModel):
    """Empty request body for approve action"""
    pass


class RejectApplicationRequest(BaseModel):
    """Request body for reject action"""
    notes: str = Field(..., min_length=10, max_length=1000, description="Reason for rejection")


class ApplicationActionResponse(BaseModel):
    """Response for approve/reject actions"""
    success: bool
    message: str
    application_id: str
    loan_id: Optional[str] = None


# ============================================================================
# Public Endpoints (No Authentication Required)
# ============================================================================

@router.post("/bicycle-applications", response_model=ApplicationOut, status_code=201)
async def submit_bicycle_application(
    payload: ApplicationCreateIn,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    """
    Submit a bicycle hire purchase application (PUBLIC - no auth required).

    Customers can submit applications for any available bicycle.
    The bicycle will be marked as RESERVED upon successful submission.
    """
    async with SessionLocal() as session:  # type: AsyncSession
        # Check idempotency
        if idempotency_key:
            idem_stmt = select(IdempotencyRecord).where(
                IdempotencyRecord.idempotency_key == idempotency_key
            )
            idem_record = (await session.execute(idem_stmt)).scalar_one_or_none()
            if idem_record:
                # Return cached response
                import json
                cached_data = json.loads(idem_record.response_body)
                return ApplicationOut(**cached_data)

        # Validate bicycle exists and is available
        bicycle = await session.get(Bicycle, payload.bicycle_id)
        if not bicycle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "BICYCLE_NOT_FOUND", "message": "Bicycle not found"}
            )

        if bicycle.status != BicycleStatus.AVAILABLE.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "BICYCLE_NOT_AVAILABLE", "message": f"Bicycle is not available (status: {bicycle.status})"}
            )

        # Validate branch exists
        branch = await session.get(Office, payload.branch_id)
        if not branch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "BRANCH_NOT_FOUND", "message": "Branch not found"}
            )

        # Validate tenure months
        if payload.tenure_months not in [12, 24, 36, 48]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_TENURE", "message": "Tenure must be 12, 24, 36, or 48 months"}
            )

        # Validate down payment not exceeding hire purchase price
        if payload.down_payment > float(bicycle.hire_purchase_price):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_DOWN_PAYMENT", "message": "Down payment cannot exceed hire purchase price"}
            )

        # Generate application ID
        application_id = bicycle_service.generate_application_id()

        # Create application
        application = BicycleApplication(
            id=application_id,
            full_name=payload.full_name,
            phone=payload.phone,
            email=payload.email,
            nip_number=payload.nip_number,
            address_line1=payload.address_line1,
            address_line2=payload.address_line2,
            city=payload.city,
            employer_name=payload.employer_name,
            monthly_income=payload.monthly_income,
            bicycle_id=payload.bicycle_id,
            branch_id=payload.branch_id,
            tenure_months=payload.tenure_months,
            down_payment=payload.down_payment,
            status=ApplicationStatus.PENDING.value,
        )

        session.add(application)

        # Reserve the bicycle
        try:
            await bicycle_service.reserve_bicycle(session, payload.bicycle_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "RESERVATION_FAILED", "message": str(e)}
            )

        # Commit transaction
        await session.commit()
        await session.refresh(application)

        # Send notifications (async, don't wait)
        try:
            await notification_service.send_application_submitted_email(application, bicycle)
            await notification_service.send_new_application_notification(application, bicycle)
        except Exception as e:
            # Log but don't fail the request
            from loguru import logger
            logger.error(f"Failed to send notification: {e}")

        # Prepare response
        response_data = ApplicationOut(
            id=application.id,
            status=application.status,
            bicycle_id=application.bicycle_id,
            branch_id=application.branch_id,
            full_name=application.full_name,
            phone=application.phone,
            email=application.email,
            tenure_months=application.tenure_months,
            down_payment=float(application.down_payment),
            submitted_at=application.submitted_at.isoformat(),
            loan_id=application.loan_id,
        )

        # Store idempotency record
        if idempotency_key:
            import json
            idem_record = IdempotencyRecord(
                idempotency_key=idempotency_key,
                request_path="/v1/bicycle-applications",
                response_status=201,
                response_body=json.dumps(response_data.model_dump()),
            )
            session.add(idem_record)
            await session.commit()

        return response_data


# ============================================================================
# Staff Endpoints (Authentication Required)
# ============================================================================

@router.get("/bicycle-applications", response_model=ApplicationListResponse)
async def list_bicycle_applications(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    branch_id: Optional[str] = Query(None, description="Filter by branch"),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user: dict = Depends(require_permission("applications:read"))
):
    """
    List bicycle applications (STAFF ONLY).

    Branch managers can only see applications for their assigned branch.
    Other roles can see all applications.
    """
    async with SessionLocal() as session:  # type: AsyncSession
        # Build query
        stmt = select(BicycleApplication)

        # Apply filters
        filters = []

        if status_filter:
            filters.append(BicycleApplication.status == status_filter.upper())

        # Branch filtering
        if branch_id:
            filters.append(BicycleApplication.branch_id == branch_id)
        elif ROLE_BRANCH_MANAGER in user.get("roles", []):
            # Branch managers can only see their branch's applications
            user_branch_id = user.get("metadata", {}).get("branch_id")
            if user_branch_id:
                filters.append(BicycleApplication.branch_id == user_branch_id)

        if filters:
            stmt = stmt.where(and_(*filters))

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await session.scalar(count_stmt) or 0

        # Apply pagination and ordering
        stmt = stmt.order_by(desc(BicycleApplication.submitted_at)).offset(offset).limit(limit)

        # Execute query
        result = await session.execute(stmt)
        applications = result.scalars().all()

        # Convert to response format
        items = [
            ApplicationDetailOut(
                id=app.id,
                full_name=app.full_name,
                phone=app.phone,
                email=app.email,
                nip_number=app.nip_number,
                address_line1=app.address_line1,
                address_line2=app.address_line2,
                city=app.city,
                employer_name=app.employer_name,
                monthly_income=float(app.monthly_income) if app.monthly_income else None,
                bicycle_id=app.bicycle_id,
                branch_id=app.branch_id,
                tenure_months=app.tenure_months,
                down_payment=float(app.down_payment),
                status=app.status,
                notes=app.notes,
                loan_id=app.loan_id,
                submitted_at=app.submitted_at.isoformat(),
                reviewed_by=str(app.reviewed_by) if app.reviewed_by else None,
                reviewed_at=app.reviewed_at.isoformat() if app.reviewed_at else None,
            )
            for app in applications
        ]

        return ApplicationListResponse(
            items=items,
            total=total,
            offset=offset,
            limit=limit,
        )


@router.get("/bicycle-applications/{application_id}", response_model=ApplicationDetailOut)
async def get_bicycle_application(
    application_id: str,
    user: dict = Depends(require_permission("applications:read"))
):
    """
    Get detailed information about a specific application (STAFF ONLY).

    Branch managers can only access applications for their assigned branch.
    """
    async with SessionLocal() as session:  # type: AsyncSession
        application = await session.get(BicycleApplication, application_id)

        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "APPLICATION_NOT_FOUND", "message": "Application not found"}
            )

        # Check branch access for branch managers
        if ROLE_BRANCH_MANAGER in user.get("roles", []):
            user_branch_id = user.get("metadata", {}).get("branch_id")
            if user_branch_id and application.branch_id != user_branch_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"code": "ACCESS_DENIED", "message": f"You can only access applications for branch {user_branch_id}"}
                )

        return ApplicationDetailOut(
            id=application.id,
            full_name=application.full_name,
            phone=application.phone,
            email=application.email,
            nip_number=application.nip_number,
            address_line1=application.address_line1,
            address_line2=application.address_line2,
            city=application.city,
            employer_name=application.employer_name,
            monthly_income=float(application.monthly_income) if application.monthly_income else None,
            bicycle_id=application.bicycle_id,
            branch_id=application.branch_id,
            tenure_months=application.tenure_months,
            down_payment=float(application.down_payment),
            status=application.status,
            notes=application.notes,
            loan_id=application.loan_id,
            submitted_at=application.submitted_at.isoformat(),
            reviewed_by=str(application.reviewed_by) if application.reviewed_by else None,
            reviewed_at=application.reviewed_at.isoformat() if application.reviewed_at else None,
        )


@router.post("/bicycle-applications/{application_id}/approve", response_model=ApplicationActionResponse)
async def approve_bicycle_application(
    application_id: str,
    payload: ApproveApplicationRequest,
    user: dict = Depends(require_permission("applications:approve"))
):
    """
    Approve a bicycle application and create a loan (STAFF ONLY).

    This action:
    1. Creates or updates client record
    2. Creates a loan
    3. Updates application status to CONVERTED_TO_LOAN
    4. Marks bicycle as SOLD
    5. Sends notification to customer
    """
    async with SessionLocal() as session:  # type: AsyncSession
        application = await session.get(BicycleApplication, application_id)

        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "APPLICATION_NOT_FOUND", "message": "Application not found"}
            )

        # Check branch access for branch managers
        if ROLE_BRANCH_MANAGER in user.get("roles", []):
            user_branch_id = user.get("metadata", {}).get("branch_id")
            if user_branch_id and application.branch_id != user_branch_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"code": "ACCESS_DENIED", "message": f"You can only approve applications for branch {user_branch_id}"}
                )

        # Get user ID from JWT sub
        user_id = user.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "INVALID_TOKEN", "message": "User ID not found in token"}
            )

        # Convert to UUID
        try:
            user_uuid = uuid.UUID(user_id)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "INVALID_USER_ID", "message": "Invalid user ID format"}
            )

        # Approve application and create loan
        try:
            loan = await bicycle_service.approve_application_and_create_loan(
                session, application, user_uuid
            )
            await session.commit()
        except ValueError as e:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "APPROVAL_FAILED", "message": str(e)}
            )

        # Send notification
        try:
            bicycle = await session.get(Bicycle, application.bicycle_id)
            await notification_service.send_application_approved_email(
                application, bicycle, loan.id
            )
        except Exception as e:
            from loguru import logger
            logger.error(f"Failed to send approval notification: {e}")

        return ApplicationActionResponse(
            success=True,
            message="Application approved and loan created successfully",
            application_id=application.id,
            loan_id=loan.id,
        )


@router.post("/bicycle-applications/{application_id}/reject", response_model=ApplicationActionResponse)
async def reject_bicycle_application(
    application_id: str,
    payload: RejectApplicationRequest,
    user: dict = Depends(require_permission("applications:approve"))
):
    """
    Reject a bicycle application (STAFF ONLY).

    This action:
    1. Updates application status to REJECTED
    2. Records rejection notes
    3. Releases bicycle reservation (if reserved)
    4. Sends notification to customer
    """
    async with SessionLocal() as session:  # type: AsyncSession
        application = await session.get(BicycleApplication, application_id)

        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "APPLICATION_NOT_FOUND", "message": "Application not found"}
            )

        # Check branch access for branch managers
        if ROLE_BRANCH_MANAGER in user.get("roles", []):
            user_branch_id = user.get("metadata", {}).get("branch_id")
            if user_branch_id and application.branch_id != user_branch_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"code": "ACCESS_DENIED", "message": f"You can only reject applications for branch {user_branch_id}"}
                )

        # Get user ID
        user_id = user.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "INVALID_TOKEN", "message": "User ID not found in token"}
            )

        try:
            user_uuid = uuid.UUID(user_id)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "INVALID_USER_ID", "message": "Invalid user ID format"}
            )

        # Reject application
        try:
            await bicycle_service.reject_application_and_release_bicycle(
                session, application, payload.notes, user_uuid
            )
            await session.commit()
        except ValueError as e:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "REJECTION_FAILED", "message": str(e)}
            )

        # Send notification
        try:
            bicycle = await session.get(Bicycle, application.bicycle_id)
            await notification_service.send_application_rejected_email(application, bicycle)
        except Exception as e:
            from loguru import logger
            logger.error(f"Failed to send rejection notification: {e}")

        return ApplicationActionResponse(
            success=True,
            message="Application rejected successfully",
            application_id=application.id,
            loan_id=None,
        )
