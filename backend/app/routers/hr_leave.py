from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, date
from typing import Optional
import secrets

from ..db import get_db
from ..models.hr_leave import LeaveType, LeaveBalance, LeaveApplication, LeaveStatus
from ..models.user import User
from ..rbac import require_permission, get_current_user, ROLE_ADMIN, ROLE_BRANCH_MANAGER


router = APIRouter(prefix="/v1/leave", tags=["hr-leave"])


# ============================================================================
# Pydantic Models
# ============================================================================

class LeaveTypeOut(BaseModel):
    """Leave type response"""
    id: str
    name: str
    description: Optional[str] = None
    default_days_per_year: int
    requires_approval: bool
    requires_documentation: bool
    max_consecutive_days: Optional[int] = None
    is_paid: bool
    is_active: bool


class LeaveBalanceOut(BaseModel):
    """Leave balance response"""
    id: str
    user_id: str
    leave_type_id: str
    leave_type_name: Optional[str] = None
    year: int
    entitled_days: float
    used_days: float
    pending_days: float
    remaining_days: float
    carried_forward_days: float


class LeaveApplicationCreateIn(BaseModel):
    """Create leave application"""
    leave_type_id: str
    start_date: date = Field(..., description="Leave start date (YYYY-MM-DD)")
    end_date: date = Field(..., description="Leave end date (YYYY-MM-DD)")
    total_days: float = Field(..., ge=0.5, le=365, description="Total days (supports half-days)")
    reason: str = Field(..., min_length=10, max_length=1000)
    document_url: Optional[str] = Field(None, max_length=500)


class LeaveApplicationOut(BaseModel):
    """Leave application response"""
    id: str
    user_id: str
    leave_type_id: str
    leave_type_name: Optional[str] = None
    start_date: str
    end_date: str
    total_days: float
    reason: str
    status: str
    approver_id: Optional[str] = None
    approved_at: Optional[str] = None
    approver_notes: Optional[str] = None
    document_url: Optional[str] = None
    created_at: str
    updated_at: str


class LeaveApplicationListResponse(BaseModel):
    """Paginated leave application list"""
    items: list[LeaveApplicationOut]
    total: int
    offset: int
    limit: int


class LeaveActionIn(BaseModel):
    """Approve/Reject leave application"""
    notes: Optional[str] = Field(None, max_length=1000)


# ============================================================================
# Helper Functions
# ============================================================================

async def get_db_session():
    """Get database session"""
    async with get_db() as session:
        yield session


async def check_leave_balance(
    session: AsyncSession,
    user_id: str,
    leave_type_id: str,
    total_days: float,
    year: int,
    exclude_application_id: Optional[str] = None
) -> tuple[bool, str]:
    """
    Check if user has sufficient leave balance
    Returns: (is_valid, error_message)
    """
    # Get leave balance for user
    stmt = select(LeaveBalance).where(
        and_(
            LeaveBalance.user_id == user_id,
            LeaveBalance.leave_type_id == leave_type_id,
            LeaveBalance.year == year
        )
    )
    result = await session.execute(stmt)
    balance = result.scalar_one_or_none()

    if not balance:
        return False, f"No leave balance found for leave type {leave_type_id} in year {year}"

    # Calculate pending days excluding current application if updating
    pending_stmt = select(func.sum(LeaveApplication.total_days)).where(
        and_(
            LeaveApplication.user_id == user_id,
            LeaveApplication.leave_type_id == leave_type_id,
            LeaveApplication.status == LeaveStatus.PENDING.value,
            LeaveApplication.id != exclude_application_id if exclude_application_id else True
        )
    )
    pending_result = await session.execute(pending_stmt)
    pending_days = pending_result.scalar() or 0

    available = float(balance.entitled_days) - float(balance.used_days) - float(pending_days)

    if available < total_days:
        return False, f"Insufficient leave balance. Available: {available} days, Requested: {total_days} days"

    return True, ""


# ============================================================================
# Leave Types Endpoints
# ============================================================================

@router.get("/types", response_model=list[LeaveTypeOut])
async def list_leave_types(
    active_only: bool = Query(True, description="Filter active leave types only"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get all leave types

    Permissions: All authenticated users can view leave types
    """
    stmt = select(LeaveType).order_by(LeaveType.name)

    if active_only:
        stmt = stmt.where(LeaveType.is_active == True)

    result = await session.execute(stmt)
    leave_types = result.scalars().all()

    return [LeaveTypeOut(**lt.to_dict()) for lt in leave_types]


# ============================================================================
# Leave Balance Endpoints
# ============================================================================

@router.get("/balances", response_model=list[LeaveBalanceOut])
async def get_my_leave_balances(
    year: Optional[int] = Query(None, description="Filter by year (default: current year)"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get leave balances for current user

    Permissions: All authenticated users can view their own balances
    """
    if year is None:
        year = datetime.now().year

    stmt = select(LeaveBalance, LeaveType).join(
        LeaveType, LeaveBalance.leave_type_id == LeaveType.id
    ).where(
        and_(
            LeaveBalance.user_id == str(current_user.id),
            LeaveBalance.year == year
        )
    ).order_by(LeaveType.name)

    result = await session.execute(stmt)
    rows = result.all()

    balances = []
    for balance, leave_type in rows:
        balance_dict = balance.to_dict()
        balance_dict["leave_type_name"] = leave_type.name
        balances.append(LeaveBalanceOut(**balance_dict))

    return balances


@router.get("/balances/{user_id}", response_model=list[LeaveBalanceOut])
async def get_user_leave_balances(
    user_id: str,
    year: Optional[int] = Query(None, description="Filter by year (default: current year)"),
    current_user: User = Depends(require_permission("leaves:read")),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get leave balances for a specific user (admin/manager only)

    Permissions: leaves:read
    """
    if year is None:
        year = datetime.now().year

    stmt = select(LeaveBalance, LeaveType).join(
        LeaveType, LeaveBalance.leave_type_id == LeaveType.id
    ).where(
        and_(
            LeaveBalance.user_id == user_id,
            LeaveBalance.year == year
        )
    ).order_by(LeaveType.name)

    result = await session.execute(stmt)
    rows = result.all()

    balances = []
    for balance, leave_type in rows:
        balance_dict = balance.to_dict()
        balance_dict["leave_type_name"] = leave_type.name
        balances.append(LeaveBalanceOut(**balance_dict))

    return balances


# ============================================================================
# Leave Application Endpoints
# ============================================================================

@router.post("/applications", response_model=LeaveApplicationOut, status_code=status.HTTP_201_CREATED)
async def create_leave_application(
    data: LeaveApplicationCreateIn,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Submit a leave application

    Permissions: All authenticated users can submit leave applications
    """
    # Validate dates
    if data.start_date > data.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before or equal to end date"
        )

    # Validate leave type exists and is active
    leave_type_stmt = select(LeaveType).where(LeaveType.id == data.leave_type_id)
    leave_type_result = await session.execute(leave_type_stmt)
    leave_type = leave_type_result.scalar_one_or_none()

    if not leave_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Leave type {data.leave_type_id} not found"
        )

    if not leave_type.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Leave type {leave_type.name} is not active"
        )

    # Check if documentation is required
    if leave_type.requires_documentation and not data.document_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Leave type {leave_type.name} requires documentation"
        )

    # Check max consecutive days
    if leave_type.max_consecutive_days and data.total_days > leave_type.max_consecutive_days:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Leave type {leave_type.name} allows maximum {leave_type.max_consecutive_days} consecutive days"
        )

    # Check leave balance
    year = data.start_date.year
    is_valid, error_msg = await check_leave_balance(
        session,
        str(current_user.id),
        data.leave_type_id,
        data.total_days,
        year
    )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    # Create application
    application_id = f"LA-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"

    application = LeaveApplication(
        id=application_id,
        user_id=str(current_user.id),
        leave_type_id=data.leave_type_id,
        start_date=data.start_date,
        end_date=data.end_date,
        total_days=data.total_days,
        reason=data.reason,
        document_url=data.document_url,
        status=LeaveStatus.PENDING.value
    )

    session.add(application)

    # Update pending days in leave balance
    balance_stmt = select(LeaveBalance).where(
        and_(
            LeaveBalance.user_id == str(current_user.id),
            LeaveBalance.leave_type_id == data.leave_type_id,
            LeaveBalance.year == year
        )
    )
    balance_result = await session.execute(balance_stmt)
    balance = balance_result.scalar_one()

    balance.pending_days = float(balance.pending_days) + data.total_days

    await session.commit()
    await session.refresh(application)

    # Get leave type name for response
    app_dict = application.to_dict()
    app_dict["leave_type_name"] = leave_type.name

    return LeaveApplicationOut(**app_dict)


@router.get("/applications", response_model=LeaveApplicationListResponse)
async def list_leave_applications(
    status: Optional[str] = Query(None, description="Filter by status"),
    user_id: Optional[str] = Query(None, description="Filter by user ID (admin only)"),
    start_date: Optional[date] = Query(None, description="Filter by start date (from)"),
    end_date: Optional[date] = Query(None, description="Filter by end date (to)"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    List leave applications

    Permissions:
    - All users can view their own applications
    - Admin/managers with leaves:read can view all applications
    """
    # Build base query
    stmt = select(LeaveApplication, LeaveType).join(
        LeaveType, LeaveApplication.leave_type_id == LeaveType.id
    )

    # Filter by user
    if user_id:
        # Check permission to view other users' applications
        if user_id != str(current_user.id):
            try:
                # This will raise exception if user doesn't have permission
                await require_permission("leaves:read")(current_user)
            except HTTPException:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only view your own leave applications"
                )
        stmt = stmt.where(LeaveApplication.user_id == user_id)
    else:
        # Default to current user's applications if no user_id provided
        stmt = stmt.where(LeaveApplication.user_id == str(current_user.id))

    # Additional filters
    if status:
        stmt = stmt.where(LeaveApplication.status == status)

    if start_date:
        stmt = stmt.where(LeaveApplication.start_date >= start_date)

    if end_date:
        stmt = stmt.where(LeaveApplication.end_date <= end_date)

    # Get total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    count_result = await session.execute(count_stmt)
    total = count_result.scalar() or 0

    # Get paginated results
    stmt = stmt.order_by(desc(LeaveApplication.created_at)).offset(offset).limit(limit)
    result = await session.execute(stmt)
    rows = result.all()

    items = []
    for application, leave_type in rows:
        app_dict = application.to_dict()
        app_dict["leave_type_name"] = leave_type.name
        items.append(LeaveApplicationOut(**app_dict))

    return LeaveApplicationListResponse(
        items=items,
        total=total,
        offset=offset,
        limit=limit
    )


@router.get("/applications/{application_id}", response_model=LeaveApplicationOut)
async def get_leave_application(
    application_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get a specific leave application

    Permissions:
    - Users can view their own applications
    - Admin/managers with leaves:read can view all applications
    """
    stmt = select(LeaveApplication, LeaveType).join(
        LeaveType, LeaveApplication.leave_type_id == LeaveType.id
    ).where(LeaveApplication.id == application_id)

    result = await session.execute(stmt)
    row = result.one_or_none()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Leave application {application_id} not found"
        )

    application, leave_type = row

    # Check permission
    if application.user_id != str(current_user.id):
        try:
            await require_permission("leaves:read")(current_user)
        except HTTPException:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own leave applications"
            )

    app_dict = application.to_dict()
    app_dict["leave_type_name"] = leave_type.name

    return LeaveApplicationOut(**app_dict)


@router.post("/applications/{application_id}/approve", response_model=LeaveApplicationOut)
async def approve_leave_application(
    application_id: str,
    data: LeaveActionIn,
    current_user: User = Depends(require_permission("leaves:approve")),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Approve a leave application

    Permissions: leaves:approve (admin, branch_manager)
    """
    # Get application
    stmt = select(LeaveApplication, LeaveType).join(
        LeaveType, LeaveApplication.leave_type_id == LeaveType.id
    ).where(LeaveApplication.id == application_id)

    result = await session.execute(stmt)
    row = result.one_or_none()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Leave application {application_id} not found"
        )

    application, leave_type = row

    # Check if can approve
    if not application.can_approve():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve application in {application.status} status"
        )

    # Update application
    application.status = LeaveStatus.APPROVED.value
    application.approver_id = str(current_user.id)
    application.approved_at = datetime.utcnow()
    application.approver_notes = data.notes

    # Update leave balance: move pending to used
    year = application.start_date.year
    balance_stmt = select(LeaveBalance).where(
        and_(
            LeaveBalance.user_id == application.user_id,
            LeaveBalance.leave_type_id == application.leave_type_id,
            LeaveBalance.year == year
        )
    )
    balance_result = await session.execute(balance_stmt)
    balance = balance_result.scalar_one()

    balance.pending_days = float(balance.pending_days) - application.total_days
    balance.used_days = float(balance.used_days) + application.total_days

    await session.commit()
    await session.refresh(application)

    app_dict = application.to_dict()
    app_dict["leave_type_name"] = leave_type.name

    return LeaveApplicationOut(**app_dict)


@router.post("/applications/{application_id}/reject", response_model=LeaveApplicationOut)
async def reject_leave_application(
    application_id: str,
    data: LeaveActionIn,
    current_user: User = Depends(require_permission("leaves:approve")),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Reject a leave application

    Permissions: leaves:approve (admin, branch_manager)
    """
    # Get application
    stmt = select(LeaveApplication, LeaveType).join(
        LeaveType, LeaveApplication.leave_type_id == LeaveType.id
    ).where(LeaveApplication.id == application_id)

    result = await session.execute(stmt)
    row = result.one_or_none()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Leave application {application_id} not found"
        )

    application, leave_type = row

    # Check if can reject
    if not application.can_reject():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reject application in {application.status} status"
        )

    # Update application
    application.status = LeaveStatus.REJECTED.value
    application.approver_id = str(current_user.id)
    application.approved_at = datetime.utcnow()
    application.approver_notes = data.notes or "Rejected"

    # Update leave balance: remove from pending
    year = application.start_date.year
    balance_stmt = select(LeaveBalance).where(
        and_(
            LeaveBalance.user_id == application.user_id,
            LeaveBalance.leave_type_id == application.leave_type_id,
            LeaveBalance.year == year
        )
    )
    balance_result = await session.execute(balance_stmt)
    balance = balance_result.scalar_one()

    balance.pending_days = float(balance.pending_days) - application.total_days

    await session.commit()
    await session.refresh(application)

    app_dict = application.to_dict()
    app_dict["leave_type_name"] = leave_type.name

    return LeaveApplicationOut(**app_dict)


@router.post("/applications/{application_id}/cancel", response_model=LeaveApplicationOut)
async def cancel_leave_application(
    application_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Cancel a leave application (user can cancel their own pending/approved applications)

    Permissions: Users can cancel their own applications
    """
    # Get application
    stmt = select(LeaveApplication, LeaveType).join(
        LeaveType, LeaveApplication.leave_type_id == LeaveType.id
    ).where(LeaveApplication.id == application_id)

    result = await session.execute(stmt)
    row = result.one_or_none()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Leave application {application_id} not found"
        )

    application, leave_type = row

    # Check ownership
    if application.user_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only cancel your own leave applications"
        )

    # Check if can cancel
    if not application.can_cancel():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel application in {application.status} status"
        )

    # Update application
    previous_status = application.status
    application.status = LeaveStatus.CANCELLED.value

    # Update leave balance
    year = application.start_date.year
    balance_stmt = select(LeaveBalance).where(
        and_(
            LeaveBalance.user_id == application.user_id,
            LeaveBalance.leave_type_id == application.leave_type_id,
            LeaveBalance.year == year
        )
    )
    balance_result = await session.execute(balance_stmt)
    balance = balance_result.scalar_one()

    if previous_status == LeaveStatus.PENDING.value:
        # Remove from pending
        balance.pending_days = float(balance.pending_days) - application.total_days
    elif previous_status == LeaveStatus.APPROVED.value:
        # Return to available (remove from used)
        balance.used_days = float(balance.used_days) - application.total_days

    await session.commit()
    await session.refresh(application)

    app_dict = application.to_dict()
    app_dict["leave_type_name"] = leave_type.name

    return LeaveApplicationOut(**app_dict)
