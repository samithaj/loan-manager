"""
Leave Approval Router - Multi-Level Approval Workflow
Handles enhanced leave approval routing with Branch Manager and Head Office approval
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Depends, status
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, date
from typing import Optional
from uuid import UUID
import secrets

from ..db import get_db
from ..models.hr_leave import LeaveType, LeaveBalance, LeaveApplication, LeaveStatus
from ..models.leave_approval import (
    LeaveApproval,
    LeaveAuditLog,
    LeavePolicy,
    ApprovalDecision,
    ApproverRole,
)
from ..models.user import User
from ..models.branch import Branch
from ..rbac import require_permission, get_current_user, ROLE_ADMIN, ROLE_BRANCH_MANAGER
from ..services.leave_approval_service import LeaveApprovalService, LeaveApprovalError
from ..schemas.leave_approval_schemas import (
    LeaveApplicationCreate,
    LeaveApplicationUpdate,
    LeaveApplicationResponse,
    LeaveApplicationDetailResponse,
    LeaveApplicationListResponse,
    BranchApprovalRequest,
    HeadOfficeApprovalRequest,
    RejectLeaveRequest,
    RequestMoreInfoRequest,
    CancelLeaveRequest,
    LeaveApprovalResponse,
    ApprovalQueueFilters,
    MyLeaveFilters,
    LeaveTimelineResponse,
    LeaveApplicationTimelineResponse,
    LeavePolicyCreate,
    LeavePolicyUpdate,
    LeavePolicyResponse,
    LeaveCalendarFilters,
    LeaveCalendarResponse,
    LeaveCalendarEntry,
    LeaveDashboardStats,
    LeaveBalanceCheckRequest,
    LeaveBalanceCheckResponse,
    LeaveBalanceSummary,
    LeaveBalanceResponse,
)


router = APIRouter(prefix="/v1/leave-approval", tags=["leave-approval"])


# ============================================================================
# Dependency Functions
# ============================================================================


async def get_db_session():
    """Get database session"""
    async with get_db() as session:
        yield session


async def get_leave_service(session: AsyncSession = Depends(get_db_session)) -> LeaveApprovalService:
    """Get leave approval service instance"""
    return LeaveApprovalService(session)


# ============================================================================
# Employee Endpoints - Apply, View, Cancel Leave
# ============================================================================


@router.post("/applications", response_model=LeaveApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_leave_application(
    data: LeaveApplicationCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Create a new leave application (saved as DRAFT)

    Permissions: All authenticated users
    """
    # Validate leave type exists
    leave_type = await session.get(LeaveType, data.leave_type_id)
    if not leave_type or not leave_type.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave type not found or inactive"
        )

    # Set branch from user if not provided
    branch_id = data.branch_id or (UUID(current_user.branch_id) if current_user.branch_id else None)

    # Create application in DRAFT status
    application_id = f"LA-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"

    application = LeaveApplication(
        id=application_id,
        user_id=UUID(str(current_user.id)),
        leave_type_id=data.leave_type_id,
        start_date=data.start_date,
        end_date=data.end_date,
        total_days=data.total_days,
        reason=data.reason,
        is_half_day=data.is_half_day,
        document_url=data.document_url,
        branch_id=str(branch_id) if branch_id else None,
        status=LeaveStatus.DRAFT.value,
    )

    session.add(application)
    await session.commit()
    await session.refresh(application)

    return LeaveApplicationResponse.model_validate(application)


@router.put("/applications/{leave_id}", response_model=LeaveApplicationResponse)
async def update_leave_application(
    leave_id: str,
    data: LeaveApplicationUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Update a leave application (only DRAFT status)

    Permissions: Own applications only
    """
    application = await session.get(LeaveApplication, leave_id)
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave application not found")

    # Check ownership
    if str(application.user_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    # Only DRAFT can be updated
    if application.status != LeaveStatus.DRAFT.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only DRAFT applications can be updated"
        )

    # Update fields
    if data.start_date is not None:
        application.start_date = data.start_date
    if data.end_date is not None:
        application.end_date = data.end_date
    if data.total_days is not None:
        application.total_days = data.total_days
    if data.reason is not None:
        application.reason = data.reason
    if data.is_half_day is not None:
        application.is_half_day = data.is_half_day
    if data.document_url is not None:
        application.document_url = data.document_url

    await session.commit()
    await session.refresh(application)

    return LeaveApplicationResponse.model_validate(application)


@router.post("/applications/{leave_id}/submit", response_model=LeaveApplicationResponse)
async def submit_leave_application(
    leave_id: str,
    current_user: User = Depends(get_current_user),
    service: LeaveApprovalService = Depends(get_leave_service),
):
    """
    Submit leave application for approval (DRAFT/NEEDS_INFO → PENDING)

    Permissions: Own applications only
    """
    # Get application to check ownership
    application = await service._get_leave(leave_id)
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave application not found")

    if str(application.user_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    try:
        result = await service.submit_leave_request(leave_id, UUID(str(current_user.id)))
        return LeaveApplicationResponse.model_validate(result)
    except LeaveApprovalError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/applications/my", response_model=LeaveApplicationListResponse)
async def get_my_leave_applications(
    filters: MyLeaveFilters = Depends(),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get current user's leave applications

    Permissions: All authenticated users
    """
    stmt = select(LeaveApplication).where(LeaveApplication.user_id == str(current_user.id))

    # Apply filters
    if filters.status:
        stmt = stmt.where(LeaveApplication.status == filters.status)
    if filters.leave_type_id:
        stmt = stmt.where(LeaveApplication.leave_type_id == filters.leave_type_id)
    if filters.from_date:
        stmt = stmt.where(LeaveApplication.start_date >= filters.from_date)
    if filters.to_date:
        stmt = stmt.where(LeaveApplication.end_date <= filters.to_date)
    if filters.year:
        stmt = stmt.where(func.extract('year', LeaveApplication.start_date) == filters.year)

    # Get total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = await session.scalar(count_stmt) or 0

    # Apply pagination
    stmt = stmt.order_by(desc(LeaveApplication.created_at))
    stmt = stmt.offset((filters.page - 1) * filters.page_size).limit(filters.page_size)

    result = await session.execute(stmt)
    items = result.scalars().all()

    return LeaveApplicationListResponse(
        items=[LeaveApplicationResponse.model_validate(item) for item in items],
        total=total,
        page=filters.page,
        page_size=filters.page_size,
        total_pages=(total + filters.page_size - 1) // filters.page_size,
    )


@router.get("/applications/{leave_id}", response_model=LeaveApplicationDetailResponse)
async def get_leave_application_detail(
    leave_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get detailed leave application with related data

    Permissions: Own applications or leaves:read permission
    """
    application = await session.get(LeaveApplication, leave_id)
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave application not found")

    # Check permission
    if str(application.user_id) != str(current_user.id):
        # Check if user has leaves:read permission (manager/admin)
        try:
            await require_permission("leaves:read")(current_user)
        except HTTPException:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    # Build detailed response
    response_data = LeaveApplicationResponse.model_validate(application).model_dump()

    # Add related data
    leave_type = await session.get(LeaveType, application.leave_type_id)
    if leave_type:
        response_data["leave_type_name"] = leave_type.name
        response_data["leave_type_code"] = leave_type.code

    # Add employee info
    employee = await session.get(User, application.user_id)
    if employee:
        response_data["employee_name"] = employee.full_name
        response_data["employee_email"] = employee.email

    # Add branch info
    if application.branch_id:
        branch = await session.get(Branch, application.branch_id)
        if branch:
            response_data["branch_name"] = branch.name

    # Add action permissions
    response_data["can_submit"] = application.status in [LeaveStatus.DRAFT.value, LeaveStatus.NEEDS_INFO.value]
    response_data["can_cancel"] = application.status in [
        LeaveStatus.DRAFT.value,
        LeaveStatus.PENDING.value,
        LeaveStatus.APPROVED_BRANCH.value,
        LeaveStatus.APPROVED.value,
    ]

    return LeaveApplicationDetailResponse(**response_data)


@router.post("/applications/{leave_id}/cancel", response_model=LeaveApplicationResponse)
async def cancel_leave_application(
    leave_id: str,
    data: CancelLeaveRequest,
    current_user: User = Depends(get_current_user),
    service: LeaveApprovalService = Depends(get_leave_service),
):
    """
    Cancel leave application

    Permissions: Own applications or admin
    """
    application = await service._get_leave(leave_id)
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave application not found")

    # Check permission
    if str(application.user_id) != str(current_user.id):
        try:
            await require_permission("leaves:admin")(current_user)
        except HTTPException:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    try:
        result = await service.cancel_leave(leave_id, UUID(str(current_user.id)), data.reason)
        return LeaveApplicationResponse.model_validate(result)
    except LeaveApprovalError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============================================================================
# Branch Manager Endpoints - Approval Queue and Actions
# ============================================================================


@router.get("/queue/branch", response_model=LeaveApplicationListResponse)
async def get_branch_manager_queue(
    filters: ApprovalQueueFilters = Depends(),
    current_user: User = Depends(require_permission("leaves:approve")),
    service: LeaveApprovalService = Depends(get_leave_service),
):
    """
    Get approval queue for branch managers

    Permissions: leaves:approve (branch_manager)
    """
    # Get branch from user
    branch_id = UUID(current_user.branch_id) if current_user.branch_id else filters.branch_id

    items, total = await service.get_approval_queue(
        approver_id=UUID(str(current_user.id)),
        approver_role=ApproverRole.BRANCH_MANAGER,
        branch_id=branch_id,
        status_filter=filters.status,
        page=filters.page,
        page_size=filters.page_size,
    )

    return LeaveApplicationListResponse(
        items=[LeaveApplicationResponse.model_validate(item) for item in items],
        total=total,
        page=filters.page,
        page_size=filters.page_size,
        total_pages=(total + filters.page_size - 1) // filters.page_size,
    )


@router.post("/applications/{leave_id}/approve-branch", response_model=LeaveApplicationResponse)
async def approve_as_branch_manager(
    leave_id: str,
    data: BranchApprovalRequest,
    current_user: User = Depends(require_permission("leaves:approve")),
    service: LeaveApprovalService = Depends(get_leave_service),
):
    """
    Approve leave as Branch Manager
    Routes to HO if required, otherwise marks as fully approved

    Permissions: leaves:approve (branch_manager)
    """
    try:
        result = await service.approve_by_branch_manager(
            leave_id=leave_id,
            approver_id=UUID(str(current_user.id)),
            notes=data.notes,
        )
        return LeaveApplicationResponse.model_validate(result)
    except LeaveApprovalError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============================================================================
# Head Office Manager Endpoints - HO Approval Queue
# ============================================================================


@router.get("/queue/head-office", response_model=LeaveApplicationListResponse)
async def get_head_office_queue(
    filters: ApprovalQueueFilters = Depends(),
    current_user: User = Depends(require_permission("leaves:approve_ho")),
    service: LeaveApprovalService = Depends(get_leave_service),
):
    """
    Get approval queue for Head Office managers

    Permissions: leaves:approve_ho (head_manager)
    """
    items, total = await service.get_approval_queue(
        approver_id=UUID(str(current_user.id)),
        approver_role=ApproverRole.HEAD_MANAGER,
        branch_id=filters.branch_id,
        status_filter=filters.status,
        page=filters.page,
        page_size=filters.page_size,
    )

    return LeaveApplicationListResponse(
        items=[LeaveApplicationResponse.model_validate(item) for item in items],
        total=total,
        page=filters.page,
        page_size=filters.page_size,
        total_pages=(total + filters.page_size - 1) // filters.page_size,
    )


@router.post("/applications/{leave_id}/approve-ho", response_model=LeaveApplicationResponse)
async def approve_as_head_office(
    leave_id: str,
    data: HeadOfficeApprovalRequest,
    current_user: User = Depends(require_permission("leaves:approve_ho")),
    service: LeaveApprovalService = Depends(get_leave_service),
):
    """
    Approve leave as Head Office Manager (final approval)

    Permissions: leaves:approve_ho (head_manager)
    """
    try:
        result = await service.approve_by_head_manager(
            leave_id=leave_id,
            approver_id=UUID(str(current_user.id)),
            notes=data.notes,
        )
        return LeaveApplicationResponse.model_validate(result)
    except LeaveApprovalError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============================================================================
# Common Manager Actions - Reject and Request Info
# ============================================================================


@router.post("/applications/{leave_id}/reject", response_model=LeaveApplicationResponse)
async def reject_leave_application(
    leave_id: str,
    data: RejectLeaveRequest,
    current_user: User = Depends(require_permission("leaves:approve")),
    service: LeaveApprovalService = Depends(get_leave_service),
):
    """
    Reject leave application

    Permissions: leaves:approve (branch_manager or head_manager)
    """
    # Determine approver role based on permissions
    approver_role = ApproverRole.BRANCH_MANAGER
    try:
        await require_permission("leaves:approve_ho")(current_user)
        approver_role = ApproverRole.HEAD_MANAGER
    except HTTPException:
        pass

    try:
        result = await service.reject_leave(
            leave_id=leave_id,
            approver_id=UUID(str(current_user.id)),
            approver_role=approver_role,
            notes=data.notes,
        )
        return LeaveApplicationResponse.model_validate(result)
    except LeaveApprovalError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/applications/{leave_id}/request-info", response_model=LeaveApplicationResponse)
async def request_more_information(
    leave_id: str,
    data: RequestMoreInfoRequest,
    current_user: User = Depends(require_permission("leaves:approve")),
    service: LeaveApprovalService = Depends(get_leave_service),
):
    """
    Request more information from employee

    Permissions: leaves:approve (branch_manager or head_manager)
    """
    # Determine approver role
    approver_role = ApproverRole.BRANCH_MANAGER
    try:
        await require_permission("leaves:approve_ho")(current_user)
        approver_role = ApproverRole.HEAD_MANAGER
    except HTTPException:
        pass

    try:
        result = await service.request_more_info(
            leave_id=leave_id,
            approver_id=UUID(str(current_user.id)),
            approver_role=approver_role,
            notes=data.notes,
        )
        return LeaveApplicationResponse.model_validate(result)
    except LeaveApprovalError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============================================================================
# Timeline and Audit Endpoints
# ============================================================================


@router.get("/applications/{leave_id}/timeline", response_model=LeaveApplicationTimelineResponse)
async def get_leave_timeline(
    leave_id: str,
    current_user: User = Depends(get_current_user),
    service: LeaveApprovalService = Depends(get_leave_service),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get complete timeline/audit trail for leave application

    Permissions: Own applications or leaves:read
    """
    application = await service._get_leave(leave_id)
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave application not found")

    # Check permission
    if str(application.user_id) != str(current_user.id):
        try:
            await require_permission("leaves:read")(current_user)
        except HTTPException:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    audit_logs = await service.get_leave_timeline(leave_id)

    # Enrich with actor names
    timeline = []
    for log in audit_logs:
        actor = await session.get(User, log.actor_id)
        timeline.append(
            LeaveTimelineResponse(
                id=log.id,
                action=log.action,
                actor_id=log.actor_id,
                actor_name=actor.full_name if actor else "Unknown",
                old_status=log.old_status,
                new_status=log.new_status,
                notes=log.payload_json.get("notes") if log.payload_json else None,
                created_at=log.created_at,
            )
        )

    return LeaveApplicationTimelineResponse(leave_id=leave_id, timeline=timeline)


# ============================================================================
# Dashboard and Statistics Endpoints
# ============================================================================


@router.get("/dashboard/stats", response_model=LeaveDashboardStats)
async def get_dashboard_statistics(
    current_user: User = Depends(require_permission("leaves:approve")),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get dashboard statistics for managers

    Permissions: leaves:approve
    """
    # Determine role and build appropriate query
    is_ho_manager = False
    try:
        await require_permission("leaves:approve_ho")(current_user)
        is_ho_manager = True
    except HTTPException:
        pass

    now = datetime.utcnow()
    this_month_start = datetime(now.year, now.month, 1)

    # Pending approvals count
    pending_stmt = select(func.count()).select_from(LeaveApplication)
    if is_ho_manager:
        pending_stmt = pending_stmt.where(
            or_(
                LeaveApplication.status == LeaveStatus.APPROVED_BRANCH.value,
                LeaveApplication.status == LeaveStatus.PENDING.value,
            )
        )
    else:
        pending_stmt = pending_stmt.where(LeaveApplication.status == LeaveStatus.PENDING.value)
        if current_user.branch_id:
            pending_stmt = pending_stmt.where(LeaveApplication.branch_id == current_user.branch_id)

    pending_count = await session.scalar(pending_stmt) or 0

    # Approved this month
    approved_stmt = select(func.count()).select_from(LeaveApplication).where(
        and_(
            LeaveApplication.status.in_([LeaveStatus.APPROVED.value, LeaveStatus.APPROVED_HO.value]),
            LeaveApplication.approved_at >= this_month_start,
        )
    )
    if not is_ho_manager and current_user.branch_id:
        approved_stmt = approved_stmt.where(LeaveApplication.branch_id == current_user.branch_id)

    approved_count = await session.scalar(approved_stmt) or 0

    # Rejected this month
    rejected_stmt = select(func.count()).select_from(LeaveApplication).where(
        and_(
            LeaveApplication.status == LeaveStatus.REJECTED.value,
            LeaveApplication.approved_at >= this_month_start,
        )
    )
    if not is_ho_manager and current_user.branch_id:
        rejected_stmt = rejected_stmt.where(LeaveApplication.branch_id == current_user.branch_id)

    rejected_count = await session.scalar(rejected_stmt) or 0

    # Needs info count
    needs_info_stmt = select(func.count()).select_from(LeaveApplication).where(
        LeaveApplication.status == LeaveStatus.NEEDS_INFO.value
    )
    if not is_ho_manager and current_user.branch_id:
        needs_info_stmt = needs_info_stmt.where(LeaveApplication.branch_id == current_user.branch_id)

    needs_info_count = await session.scalar(needs_info_stmt) or 0

    return LeaveDashboardStats(
        pending_approvals=pending_count,
        approved_this_month=approved_count,
        rejected_this_month=rejected_count,
        needs_info_count=needs_info_count,
        avg_approval_time_hours=None,  # TODO: Calculate from audit logs
        overdue_approvals=0,  # TODO: Implement SLA tracking
        upcoming_leaves_count=0,  # TODO: Count approved leaves starting in next 7 days
    )


# ============================================================================
# Leave Balance Endpoints
# ============================================================================


@router.get("/balances/my", response_model=LeaveBalanceSummary)
async def get_my_leave_balances(
    year: Optional[int] = Query(None, description="Year (default: current year)"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get leave balances for current user

    Permissions: All authenticated users
    """
    if year is None:
        year = datetime.now().year

    stmt = select(LeaveBalance).where(
        and_(
            LeaveBalance.user_id == str(current_user.id),
            LeaveBalance.year == year,
        )
    )

    result = await session.execute(stmt)
    balances = result.scalars().all()

    balance_responses = [LeaveBalanceResponse.model_validate(b) for b in balances]

    total_entitled = sum(b.entitled_days for b in balance_responses)
    total_used = sum(b.used_days for b in balance_responses)
    total_pending = sum(b.pending_days for b in balance_responses)
    total_remaining = sum(b.remaining_days for b in balance_responses)

    return LeaveBalanceSummary(
        user_id=UUID(str(current_user.id)),
        year=year,
        balances=balance_responses,
        total_entitled=total_entitled,
        total_used=total_used,
        total_pending=total_pending,
        total_remaining=total_remaining,
    )


@router.post("/balances/check", response_model=LeaveBalanceCheckResponse)
async def check_leave_balance(
    data: LeaveBalanceCheckRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Check if user has sufficient leave balance

    Permissions: Check own balance or leaves:read
    """
    # Check permission if not own balance
    if str(data.user_id) != str(current_user.id):
        try:
            await require_permission("leaves:read")(current_user)
        except HTTPException:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    year = data.year or datetime.now().year

    # Get balance
    stmt = select(LeaveBalance).where(
        and_(
            LeaveBalance.user_id == str(data.user_id),
            LeaveBalance.leave_type_id == data.leave_type_id,
            LeaveBalance.year == year,
        )
    )

    result = await session.execute(stmt)
    balance = result.scalar_one_or_none()

    if not balance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No leave balance found for user {data.user_id} and leave type {data.leave_type_id} in {year}",
        )

    available_days = float(balance.remaining_days)
    has_sufficient = available_days >= data.total_days
    shortfall = max(0, data.total_days - available_days)

    leave_type = await session.get(LeaveType, data.leave_type_id)

    return LeaveBalanceCheckResponse(
        has_sufficient_balance=has_sufficient,
        available_days=available_days,
        requested_days=data.total_days,
        shortfall=shortfall,
        leave_type=leave_type.name if leave_type else "Unknown",
        year=year,
    )


# ============================================================================
# Leave Policy Endpoints (Admin)
# ============================================================================


@router.post("/policies", response_model=LeavePolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_leave_policy(
    data: LeavePolicyCreate,
    current_user: User = Depends(require_permission("leaves:admin")),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Create leave policy

    Permissions: leaves:admin
    """
    policy = LeavePolicy(**data.model_dump())
    session.add(policy)
    await session.commit()
    await session.refresh(policy)

    return LeavePolicyResponse.model_validate(policy)


@router.put("/policies/{policy_id}", response_model=LeavePolicyResponse)
async def update_leave_policy(
    policy_id: UUID,
    data: LeavePolicyUpdate,
    current_user: User = Depends(require_permission("leaves:admin")),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Update leave policy

    Permissions: leaves:admin
    """
    policy = await session.get(LeavePolicy, policy_id)
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")

    # Update fields
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(policy, field, value)

    await session.commit()
    await session.refresh(policy)

    return LeavePolicyResponse.model_validate(policy)


@router.get("/policies", response_model=list[LeavePolicyResponse])
async def list_leave_policies(
    branch_id: Optional[UUID] = Query(None),
    leave_type_id: Optional[str] = Query(None),
    active_only: bool = Query(True),
    current_user: User = Depends(require_permission("leaves:read")),
    session: AsyncSession = Depends(get_db_session),
):
    """
    List leave policies

    Permissions: leaves:read
    """
    stmt = select(LeavePolicy)

    if branch_id:
        stmt = stmt.where(LeavePolicy.branch_id == branch_id)
    if leave_type_id:
        stmt = stmt.where(LeavePolicy.leave_type_id == leave_type_id)
    if active_only:
        stmt = stmt.where(LeavePolicy.is_active == True)

    stmt = stmt.order_by(desc(LeavePolicy.created_at))

    result = await session.execute(stmt)
    policies = result.scalars().all()

    return [LeavePolicyResponse.model_validate(p) for p in policies]
