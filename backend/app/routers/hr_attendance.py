from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Depends, status, Request
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, date, time
from typing import Optional
import secrets

from ..db import get_db
from ..models.hr_attendance import AttendanceRecord, AttendanceStatus, WorkSchedule, UserWorkSchedule
from ..models.user import User
from ..rbac import require_permission, get_current_user, ROLE_ADMIN, ROLE_BRANCH_MANAGER


router = APIRouter(prefix="/v1/attendance", tags=["hr-attendance"])


# ============================================================================
# Pydantic Models
# ============================================================================

class ClockInOut(BaseModel):
    """Clock in/out request"""
    date: Optional[date] = Field(None, description="Date (default: today)")
    location: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = Field(None, max_length=1000)


class AttendanceRecordOut(BaseModel):
    """Attendance record response"""
    id: str
    user_id: str
    date: str
    clock_in: Optional[str] = None
    clock_out: Optional[str] = None
    status: str
    work_hours: Optional[float] = None
    overtime_hours: float
    notes: Optional[str] = None
    location: Optional[str] = None
    created_at: str
    updated_at: str


class AttendanceRecordListResponse(BaseModel):
    """Paginated attendance record list"""
    items: list[AttendanceRecordOut]
    total: int
    offset: int
    limit: int


class AttendanceUpdateIn(BaseModel):
    """Update attendance record (admin)"""
    clock_in: Optional[datetime] = None
    clock_out: Optional[datetime] = None
    status: str
    work_hours: Optional[float] = Field(None, ge=0, le=24)
    overtime_hours: Optional[float] = Field(None, ge=0, le=24)
    notes: Optional[str] = Field(None, max_length=1000)


class WorkScheduleCreateIn(BaseModel):
    """Create work schedule"""
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    monday_start: Optional[time] = None
    monday_end: Optional[time] = None
    tuesday_start: Optional[time] = None
    tuesday_end: Optional[time] = None
    wednesday_start: Optional[time] = None
    wednesday_end: Optional[time] = None
    thursday_start: Optional[time] = None
    thursday_end: Optional[time] = None
    friday_start: Optional[time] = None
    friday_end: Optional[time] = None
    saturday_start: Optional[time] = None
    saturday_end: Optional[time] = None
    sunday_start: Optional[time] = None
    sunday_end: Optional[time] = None
    is_default: bool = False


class WorkScheduleOut(BaseModel):
    """Work schedule response"""
    id: str
    name: str
    description: Optional[str] = None
    monday_start: Optional[str] = None
    monday_end: Optional[str] = None
    tuesday_start: Optional[str] = None
    tuesday_end: Optional[str] = None
    wednesday_start: Optional[str] = None
    wednesday_end: Optional[str] = None
    thursday_start: Optional[str] = None
    thursday_end: Optional[str] = None
    friday_start: Optional[str] = None
    friday_end: Optional[str] = None
    saturday_start: Optional[str] = None
    saturday_end: Optional[str] = None
    sunday_start: Optional[str] = None
    sunday_end: Optional[str] = None
    is_default: bool
    is_active: bool


class UserWorkScheduleAssignIn(BaseModel):
    """Assign work schedule to user"""
    schedule_id: str
    effective_from: date
    effective_to: Optional[date] = None


class UserWorkScheduleOut(BaseModel):
    """User work schedule assignment response"""
    id: str
    user_id: str
    schedule_id: str
    schedule_name: Optional[str] = None
    effective_from: str
    effective_to: Optional[str] = None


# ============================================================================
# Helper Functions
# ============================================================================

async def get_db_session():
    """Get database session"""
    async with get_db() as session:
        yield session


async def get_or_create_attendance_record(
    session: AsyncSession,
    user_id: str,
    record_date: date
) -> AttendanceRecord:
    """Get or create attendance record for user and date"""
    stmt = select(AttendanceRecord).where(
        and_(
            AttendanceRecord.user_id == user_id,
            AttendanceRecord.date == record_date
        )
    )
    result = await session.execute(stmt)
    record = result.scalar_one_or_none()

    if not record:
        record_id = f"ATT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"
        record = AttendanceRecord(
            id=record_id,
            user_id=user_id,
            date=record_date,
            status=AttendanceStatus.ABSENT.value
        )
        session.add(record)
        await session.flush()

    return record


# ============================================================================
# Clock In/Out Endpoints
# ============================================================================

@router.post("/clock-in", response_model=AttendanceRecordOut)
async def clock_in(
    data: ClockInOut,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Clock in for attendance

    Permissions: All authenticated users can clock in
    """
    record_date = data.date or date.today()

    # Prevent clocking in for future dates
    if record_date > date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot clock in for future dates"
        )

    # Get or create attendance record
    record = await get_or_create_attendance_record(session, str(current_user.id), record_date)

    # Check if already clocked in
    if record.clock_in:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Already clocked in at {record.clock_in.isoformat()}"
        )

    # Update record
    record.clock_in = datetime.utcnow()
    record.status = AttendanceStatus.PRESENT.value
    record.location = data.location
    record.notes = data.notes
    record.ip_address = request.client.host if request.client else None

    await session.commit()
    await session.refresh(record)

    return AttendanceRecordOut(**record.to_dict())


@router.post("/clock-out", response_model=AttendanceRecordOut)
async def clock_out(
    data: ClockInOut,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Clock out for attendance

    Permissions: All authenticated users can clock out
    """
    record_date = data.date or date.today()

    # Get attendance record
    stmt = select(AttendanceRecord).where(
        and_(
            AttendanceRecord.user_id == str(current_user.id),
            AttendanceRecord.date == record_date
        )
    )
    result = await session.execute(stmt)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No attendance record found for {record_date}"
        )

    if not record.clock_in:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must clock in before clocking out"
        )

    if record.clock_out:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Already clocked out at {record.clock_out.isoformat()}"
        )

    # Update record
    record.clock_out = datetime.utcnow()
    record.work_hours = record.calculate_work_hours()

    if data.notes:
        record.notes = (record.notes or "") + "\n" + data.notes

    await session.commit()
    await session.refresh(record)

    return AttendanceRecordOut(**record.to_dict())


# ============================================================================
# Attendance Record Endpoints
# ============================================================================

@router.get("/records", response_model=AttendanceRecordListResponse)
async def list_attendance_records(
    user_id: Optional[str] = Query(None, description="Filter by user ID (admin only)"),
    date_from: Optional[date] = Query(None, description="Filter from date"),
    date_to: Optional[date] = Query(None, description="Filter to date"),
    status: Optional[str] = Query(None, description="Filter by status"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    List attendance records

    Permissions:
    - Users can view their own records
    - Admin/managers with attendance:read can view all records
    """
    # Build base query
    stmt = select(AttendanceRecord)

    # Filter by user
    if user_id:
        # Check permission to view other users' records
        if user_id != str(current_user.id):
            try:
                await require_permission("attendance:read")(current_user)
            except HTTPException:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only view your own attendance records"
                )
        stmt = stmt.where(AttendanceRecord.user_id == user_id)
    else:
        # Default to current user's records if no user_id provided
        stmt = stmt.where(AttendanceRecord.user_id == str(current_user.id))

    # Additional filters
    if date_from:
        stmt = stmt.where(AttendanceRecord.date >= date_from)

    if date_to:
        stmt = stmt.where(AttendanceRecord.date <= date_to)

    if status:
        stmt = stmt.where(AttendanceRecord.status == status)

    # Get total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    count_result = await session.execute(count_stmt)
    total = count_result.scalar() or 0

    # Get paginated results
    stmt = stmt.order_by(desc(AttendanceRecord.date)).offset(offset).limit(limit)
    result = await session.execute(stmt)
    records = result.scalars().all()

    items = [AttendanceRecordOut(**record.to_dict()) for record in records]

    return AttendanceRecordListResponse(
        items=items,
        total=total,
        offset=offset,
        limit=limit
    )


@router.get("/records/{record_id}", response_model=AttendanceRecordOut)
async def get_attendance_record(
    record_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get a specific attendance record

    Permissions:
    - Users can view their own records
    - Admin/managers with attendance:read can view all records
    """
    stmt = select(AttendanceRecord).where(AttendanceRecord.id == record_id)
    result = await session.execute(stmt)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attendance record {record_id} not found"
        )

    # Check permission
    if record.user_id != str(current_user.id):
        try:
            await require_permission("attendance:read")(current_user)
        except HTTPException:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own attendance records"
            )

    return AttendanceRecordOut(**record.to_dict())


@router.put("/records/{record_id}", response_model=AttendanceRecordOut)
async def update_attendance_record(
    record_id: str,
    data: AttendanceUpdateIn,
    current_user: User = Depends(require_permission("attendance:write")),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Update an attendance record (admin/manager only)

    Permissions: attendance:write
    """
    stmt = select(AttendanceRecord).where(AttendanceRecord.id == record_id)
    result = await session.execute(stmt)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attendance record {record_id} not found"
        )

    # Update fields
    if data.clock_in is not None:
        record.clock_in = data.clock_in

    if data.clock_out is not None:
        record.clock_out = data.clock_out

    record.status = data.status

    if data.work_hours is not None:
        record.work_hours = data.work_hours
    elif record.clock_in and record.clock_out:
        record.work_hours = record.calculate_work_hours()

    if data.overtime_hours is not None:
        record.overtime_hours = data.overtime_hours

    if data.notes is not None:
        record.notes = data.notes

    await session.commit()
    await session.refresh(record)

    return AttendanceRecordOut(**record.to_dict())


# ============================================================================
# Work Schedule Endpoints
# ============================================================================

@router.post("/schedules", response_model=WorkScheduleOut, status_code=status.HTTP_201_CREATED)
async def create_work_schedule(
    data: WorkScheduleCreateIn,
    current_user: User = Depends(require_permission("attendance:write")),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Create a work schedule

    Permissions: attendance:write (admin, branch_manager)
    """
    schedule_id = f"SCH-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"

    schedule = WorkSchedule(
        id=schedule_id,
        name=data.name,
        description=data.description,
        monday_start=data.monday_start,
        monday_end=data.monday_end,
        tuesday_start=data.tuesday_start,
        tuesday_end=data.tuesday_end,
        wednesday_start=data.wednesday_start,
        wednesday_end=data.wednesday_end,
        thursday_start=data.thursday_start,
        thursday_end=data.thursday_end,
        friday_start=data.friday_start,
        friday_end=data.friday_end,
        saturday_start=data.saturday_start,
        saturday_end=data.saturday_end,
        sunday_start=data.sunday_start,
        sunday_end=data.sunday_end,
        is_default=data.is_default,
        is_active=True
    )

    session.add(schedule)
    await session.commit()
    await session.refresh(schedule)

    return WorkScheduleOut(**schedule.to_dict())


@router.get("/schedules", response_model=list[WorkScheduleOut])
async def list_work_schedules(
    active_only: bool = Query(True, description="Filter active schedules only"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    List work schedules

    Permissions: All authenticated users can view schedules
    """
    stmt = select(WorkSchedule).order_by(WorkSchedule.name)

    if active_only:
        stmt = stmt.where(WorkSchedule.is_active == True)

    result = await session.execute(stmt)
    schedules = result.scalars().all()

    return [WorkScheduleOut(**schedule.to_dict()) for schedule in schedules]


@router.get("/schedules/{schedule_id}", response_model=WorkScheduleOut)
async def get_work_schedule(
    schedule_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get a specific work schedule

    Permissions: All authenticated users can view schedules
    """
    stmt = select(WorkSchedule).where(WorkSchedule.id == schedule_id)
    result = await session.execute(stmt)
    schedule = result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Work schedule {schedule_id} not found"
        )

    return WorkScheduleOut(**schedule.to_dict())


# ============================================================================
# User Schedule Assignment Endpoints
# ============================================================================

@router.post("/schedules/assign/{user_id}", response_model=UserWorkScheduleOut, status_code=status.HTTP_201_CREATED)
async def assign_work_schedule_to_user(
    user_id: str,
    data: UserWorkScheduleAssignIn,
    current_user: User = Depends(require_permission("attendance:write")),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Assign work schedule to user

    Permissions: attendance:write (admin, branch_manager)
    """
    # Verify schedule exists
    schedule_stmt = select(WorkSchedule).where(WorkSchedule.id == data.schedule_id)
    schedule_result = await session.execute(schedule_stmt)
    schedule = schedule_result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Work schedule {data.schedule_id} not found"
        )

    # Create assignment
    assignment_id = f"USA-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"

    assignment = UserWorkSchedule(
        id=assignment_id,
        user_id=user_id,
        schedule_id=data.schedule_id,
        effective_from=data.effective_from,
        effective_to=data.effective_to
    )

    session.add(assignment)
    await session.commit()
    await session.refresh(assignment)

    assign_dict = assignment.to_dict()
    assign_dict["schedule_name"] = schedule.name

    return UserWorkScheduleOut(**assign_dict)


@router.get("/schedules/assigned/{user_id}", response_model=list[UserWorkScheduleOut])
async def get_user_work_schedules(
    user_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get work schedules assigned to user

    Permissions:
    - Users can view their own assignments
    - Admin/managers can view all assignments
    """
    # Check permission
    if user_id != str(current_user.id):
        try:
            await require_permission("attendance:read")(current_user)
        except HTTPException:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own work schedules"
            )

    stmt = select(UserWorkSchedule, WorkSchedule).join(
        WorkSchedule, UserWorkSchedule.schedule_id == WorkSchedule.id
    ).where(
        UserWorkSchedule.user_id == user_id
    ).order_by(desc(UserWorkSchedule.effective_from))

    result = await session.execute(stmt)
    rows = result.all()

    assignments = []
    for assignment, schedule in rows:
        assign_dict = assignment.to_dict()
        assign_dict["schedule_name"] = schedule.name
        assignments.append(UserWorkScheduleOut(**assign_dict))

    return assignments
