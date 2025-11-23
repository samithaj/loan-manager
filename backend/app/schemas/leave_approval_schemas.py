"""
Pydantic schemas for Enhanced Leave Management and Approval API
"""
from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional
from datetime import datetime, date
from uuid import UUID
from ..models.hr_leave import LeaveStatus
from ..models.leave_approval import ApprovalDecision, ApproverRole


# ============================================================================
# Leave Type Schemas
# ============================================================================


class LeaveTypeBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    default_days_per_year: int = Field(..., ge=0)
    requires_approval: bool = True
    requires_documentation: bool = False
    max_consecutive_days: Optional[int] = Field(None, ge=1)
    is_paid: bool = True
    is_active: bool = True
    requires_ho_approval: bool = False
    max_days_per_request: Optional[int] = Field(None, ge=1)
    code: Optional[str] = Field(None, max_length=20)


class LeaveTypeCreate(LeaveTypeBase):
    pass


class LeaveTypeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    default_days_per_year: Optional[int] = Field(None, ge=0)
    requires_approval: Optional[bool] = None
    requires_documentation: Optional[bool] = None
    max_consecutive_days: Optional[int] = Field(None, ge=1)
    is_paid: Optional[bool] = None
    is_active: Optional[bool] = None
    requires_ho_approval: Optional[bool] = None
    max_days_per_request: Optional[int] = Field(None, ge=1)


class LeaveTypeResponse(LeaveTypeBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime


# ============================================================================
# Leave Balance Schemas
# ============================================================================


class LeaveBalanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: UUID
    leave_type_id: str
    year: int
    entitled_days: float
    used_days: float
    pending_days: float
    remaining_days: float
    carried_forward_days: float
    created_at: datetime
    updated_at: datetime


class LeaveBalanceSummary(BaseModel):
    """Summary of all leave balances for a user"""
    user_id: UUID
    year: int
    balances: list[LeaveBalanceResponse]
    total_entitled: float
    total_used: float
    total_pending: float
    total_remaining: float


# ============================================================================
# Leave Application Schemas
# ============================================================================


class LeaveApplicationBase(BaseModel):
    leave_type_id: str
    start_date: date
    end_date: date
    total_days: float = Field(..., gt=0)
    reason: str = Field(..., min_length=1, max_length=1000)
    is_half_day: bool = False
    document_url: Optional[str] = Field(None, max_length=500)

    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, v, info):
        if "start_date" in info.data and v < info.data["start_date"]:
            raise ValueError("end_date must be on or after start_date")
        return v


class LeaveApplicationCreate(LeaveApplicationBase):
    """Create leave application (as Employee)"""
    branch_id: Optional[UUID] = None  # Auto-set from user's branch if not provided


class LeaveApplicationUpdate(BaseModel):
    """Update leave application (only DRAFT status)"""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    total_days: Optional[float] = Field(None, gt=0)
    reason: Optional[str] = Field(None, min_length=1, max_length=1000)
    is_half_day: Optional[bool] = None
    document_url: Optional[str] = Field(None, max_length=500)


class LeaveApplicationResponse(LeaveApplicationBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: UUID
    status: str
    approver_id: Optional[UUID]
    approved_at: Optional[datetime]
    approver_notes: Optional[str]
    branch_id: Optional[UUID]
    branch_approver_id: Optional[UUID]
    branch_approved_at: Optional[datetime]
    ho_approver_id: Optional[UUID]
    ho_approved_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class LeaveApplicationDetailResponse(LeaveApplicationResponse):
    """Detailed leave application with related data"""
    leave_type_name: Optional[str] = None
    leave_type_code: Optional[str] = None
    employee_name: Optional[str] = None
    employee_email: Optional[str] = None
    branch_name: Optional[str] = None
    approver_name: Optional[str] = None
    branch_approver_name: Optional[str] = None
    ho_approver_name: Optional[str] = None
    can_submit: bool = False
    can_cancel: bool = False
    can_approve: bool = False
    can_reject: bool = False


class LeaveApplicationListResponse(BaseModel):
    """Paginated list of leave applications"""
    items: list[LeaveApplicationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================================================
# Approval Decision Schemas
# ============================================================================


class ApprovalDecisionRequest(BaseModel):
    """Request to approve/reject/request info"""
    decision: ApprovalDecision
    notes: Optional[str] = Field(None, max_length=1000)

    @field_validator("notes")
    @classmethod
    def validate_notes_for_rejection(cls, v, info):
        if "decision" in info.data:
            if info.data["decision"] in [ApprovalDecision.REJECTED, ApprovalDecision.NEEDS_INFO]:
                if not v or len(v.strip()) == 0:
                    raise ValueError("Notes are required for REJECTED and NEEDS_INFO decisions")
        return v


class BranchApprovalRequest(BaseModel):
    """Branch manager approval request"""
    notes: Optional[str] = Field(None, max_length=1000)


class HeadOfficeApprovalRequest(BaseModel):
    """Head office manager approval request"""
    notes: Optional[str] = Field(None, max_length=1000)


class RejectLeaveRequest(BaseModel):
    """Reject leave request"""
    notes: str = Field(..., min_length=1, max_length=1000)


class RequestMoreInfoRequest(BaseModel):
    """Request more information"""
    notes: str = Field(..., min_length=1, max_length=1000)


class CancelLeaveRequest(BaseModel):
    """Cancel leave request"""
    reason: str = Field(..., min_length=1, max_length=500)


class LeaveApprovalResponse(BaseModel):
    """Approval record response"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    leave_request_id: str
    approver_id: UUID
    approver_role: ApproverRole
    decision: ApprovalDecision
    notes: Optional[str]
    created_at: datetime


# ============================================================================
# Queue and Filter Schemas
# ============================================================================


class ApprovalQueueFilters(BaseModel):
    """Filters for approval queue"""
    status: Optional[str] = None
    leave_type_id: Optional[str] = None
    branch_id: Optional[UUID] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    employee_name: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class MyLeaveFilters(BaseModel):
    """Filters for employee's own leave requests"""
    status: Optional[str] = None
    leave_type_id: Optional[str] = None
    year: Optional[int] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class LeaveCalendarFilters(BaseModel):
    """Filters for leave calendar view"""
    branch_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    year: int
    month: int = Field(..., ge=1, le=12)
    status: Optional[list[str]] = Field(default_factory=lambda: ["APPROVED", "APPROVED_HO"])


# ============================================================================
# Timeline and Audit Schemas
# ============================================================================


class LeaveAuditLogResponse(BaseModel):
    """Audit log entry response"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    leave_request_id: str
    actor_id: UUID
    action: str
    old_status: Optional[str]
    new_status: Optional[str]
    payload_json: Optional[dict]
    created_at: datetime


class LeaveTimelineResponse(BaseModel):
    """Timeline entry with actor details"""
    id: UUID
    action: str
    actor_id: UUID
    actor_name: Optional[str]
    old_status: Optional[str]
    new_status: Optional[str]
    notes: Optional[str]
    created_at: datetime


class LeaveApplicationTimelineResponse(BaseModel):
    """Complete timeline for a leave application"""
    leave_id: str
    timeline: list[LeaveTimelineResponse]


# ============================================================================
# Leave Policy Schemas
# ============================================================================


class LeavePolicyBase(BaseModel):
    leave_type_id: str
    branch_id: Optional[UUID] = None  # None = global policy
    requires_branch_approval: bool = True
    requires_ho_approval: bool = False
    auto_approve_days_threshold: Optional[int] = Field(None, ge=0)
    branch_approval_sla_hours: Optional[int] = Field(None, ge=1)
    ho_approval_sla_hours: Optional[int] = Field(None, ge=1)
    min_notice_days: int = Field(default=1, ge=0)
    max_days_per_request: Optional[int] = Field(None, ge=1)
    allow_half_day: bool = True
    is_active: bool = True


class LeavePolicyCreate(LeavePolicyBase):
    pass


class LeavePolicyUpdate(BaseModel):
    requires_branch_approval: Optional[bool] = None
    requires_ho_approval: Optional[bool] = None
    auto_approve_days_threshold: Optional[int] = Field(None, ge=0)
    branch_approval_sla_hours: Optional[int] = Field(None, ge=1)
    ho_approval_sla_hours: Optional[int] = Field(None, ge=1)
    min_notice_days: Optional[int] = Field(None, ge=0)
    max_days_per_request: Optional[int] = Field(None, ge=1)
    allow_half_day: Optional[bool] = None
    is_active: Optional[bool] = None


class LeavePolicyResponse(LeavePolicyBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Calendar and Dashboard Schemas
# ============================================================================


class LeaveCalendarEntry(BaseModel):
    """Single calendar entry for a leave"""
    leave_id: str
    user_id: UUID
    employee_name: str
    leave_type: str
    leave_type_code: Optional[str]
    start_date: date
    end_date: date
    total_days: float
    status: str
    is_half_day: bool


class LeaveCalendarResponse(BaseModel):
    """Calendar view of leaves for a month"""
    year: int
    month: int
    branch_id: Optional[UUID]
    entries: list[LeaveCalendarEntry]
    total_leaves: int
    total_employees_on_leave: int


class LeaveDashboardStats(BaseModel):
    """Dashboard statistics for manager"""
    pending_approvals: int
    approved_this_month: int
    rejected_this_month: int
    needs_info_count: int
    avg_approval_time_hours: Optional[float]
    overdue_approvals: int  # Past SLA
    upcoming_leaves_count: int  # Next 7 days


# ============================================================================
# Bulk Operations Schemas
# ============================================================================


class BulkApprovalRequest(BaseModel):
    """Bulk approve multiple leave requests"""
    leave_ids: list[str] = Field(..., min_length=1, max_length=50)
    notes: Optional[str] = Field(None, max_length=1000)


class BulkApprovalResponse(BaseModel):
    """Response for bulk approval"""
    successful: list[str]
    failed: list[dict]  # [{leave_id: str, error: str}]
    total_processed: int
    total_successful: int
    total_failed: int


# ============================================================================
# Validation and Business Logic Schemas
# ============================================================================


class LeaveBalanceCheckRequest(BaseModel):
    """Check if user has sufficient leave balance"""
    user_id: UUID
    leave_type_id: str
    total_days: float
    year: Optional[int] = None


class LeaveBalanceCheckResponse(BaseModel):
    """Leave balance check result"""
    has_sufficient_balance: bool
    available_days: float
    requested_days: float
    shortfall: float
    leave_type: str
    year: int


class LeaveOverlapCheckRequest(BaseModel):
    """Check for overlapping leave requests"""
    user_id: UUID
    start_date: date
    end_date: date
    exclude_leave_id: Optional[str] = None


class LeaveOverlapCheckResponse(BaseModel):
    """Leave overlap check result"""
    has_overlap: bool
    overlapping_leaves: list[dict]  # [{leave_id, start_date, end_date, status}]
