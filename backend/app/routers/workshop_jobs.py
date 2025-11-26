from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_, or_, desc, update
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, date
from typing import Optional, List
import secrets

from ..db import get_db
from ..models.workshop_job import (
    RepairJob, RepairJobPart, RepairJobLabour, RepairJobOverhead,
    RepairJobType, RepairJobStatus
)
from ..models.workshop_part import Part, PartStockBatch, PartStockMovement, StockMovementType
from ..models.workshop_markup import MarkupRule, MarkupTargetType, MarkupType
from ..models.bicycle import Bicycle
from ..models.user import User
from ..rbac import require_permission, get_current_user


router = APIRouter(prefix="/v1/workshop/jobs", tags=["workshop-jobs"])


# ============================================================================
# Pydantic Models
# ============================================================================

class RepairJobCreateIn(BaseModel):
    """Create repair job"""
    bicycle_id: str
    branch_id: str
    job_type: str
    odometer: Optional[int] = None
    customer_complaint: Optional[str] = Field(None, max_length=2000)
    mechanic_id: Optional[str] = None


class RepairJobOut(BaseModel):
    """Repair job response"""
    id: str
    job_number: str
    bicycle_id: str
    bicycle_info: Optional[dict] = None
    branch_id: str
    job_type: str
    status: str
    opened_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    closed_at: Optional[str] = None
    odometer: Optional[int] = None
    customer_complaint: Optional[str] = None
    diagnosis: Optional[str] = None
    work_performed: Optional[str] = None
    mechanic_id: Optional[str] = None
    created_by: Optional[str] = None
    total_parts_cost: float
    total_labour_cost: float
    total_overhead_cost: float
    total_cost: float
    total_parts_price: float
    total_labour_price: float
    total_overhead_price: float
    total_price: float
    notes: Optional[str] = None
    created_at: str
    updated_at: str


class RepairJobListResponse(BaseModel):
    """Paginated repair job list"""
    items: list[RepairJobOut]
    total: int
    offset: int
    limit: int


class JobPartAddIn(BaseModel):
    """Add part to job"""
    part_id: str
    quantity_used: float = Field(..., gt=0)
    notes: Optional[str] = Field(None, max_length=2000)


class JobPartOut(BaseModel):
    """Job part response"""
    id: str
    job_id: str
    part_id: str
    part_name: Optional[str] = None
    batch_id: Optional[str] = None
    quantity_used: float
    unit_cost: float
    total_cost: float
    unit_price_to_customer: Optional[float] = None
    total_price_to_customer: Optional[float] = None
    notes: Optional[str] = None
    created_at: str


class JobLabourAddIn(BaseModel):
    """Add labour to job"""
    labour_code: Optional[str] = Field(None, max_length=50)
    description: str = Field(..., min_length=3, max_length=500)
    mechanic_id: Optional[str] = None
    hours: float = Field(..., gt=0)
    hourly_rate_cost: float = Field(..., gt=0)


class JobLabourOut(BaseModel):
    """Job labour response"""
    id: str
    job_id: str
    labour_code: Optional[str] = None
    description: str
    mechanic_id: Optional[str] = None
    hours: float
    hourly_rate_cost: float
    labour_cost: float
    hourly_rate_customer: Optional[float] = None
    labour_price_to_customer: Optional[float] = None
    notes: Optional[str] = None
    created_at: str


class JobOverheadAddIn(BaseModel):
    """Add overhead to job"""
    description: str = Field(..., min_length=3, max_length=500)
    cost: float = Field(..., gt=0)


class JobOverheadOut(BaseModel):
    """Job overhead response"""
    id: str
    job_id: str
    description: str
    cost: float
    price_to_customer: Optional[float] = None
    notes: Optional[str] = None
    created_at: str


class JobUpdateStatusIn(BaseModel):
    """Update job status"""
    status: str
    diagnosis: Optional[str] = Field(None, max_length=2000)
    work_performed: Optional[str] = Field(None, max_length=2000)
    notes: Optional[str] = Field(None, max_length=2000)


# ============================================================================
# Helper Functions
# ============================================================================

async def get_db_session():
    """Get database session"""
    async with get_db() as session:
        yield session


async def get_oldest_available_batch(
    session: AsyncSession,
    part_id: str,
    branch_id: str,
    quantity_needed: float
) -> Optional[PartStockBatch]:
    """Get oldest batch with available stock (FIFO)"""
    stmt = select(PartStockBatch).where(
        and_(
            PartStockBatch.part_id == part_id,
            PartStockBatch.branch_id == branch_id,
            PartStockBatch.quantity_available >= quantity_needed,
            or_(
                PartStockBatch.expiry_date.is_(None),
                PartStockBatch.expiry_date > date.today()
            )
        )
    ).order_by(PartStockBatch.purchase_date)

    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_applicable_markup_rule(
    session: AsyncSession,
    target_type: str,
    target_value: str,
    branch_id: str
) -> Optional[MarkupRule]:
    """Get applicable markup rule based on priority and effective dates"""
    today = date.today()

    stmt = select(MarkupRule).where(
        and_(
            MarkupRule.target_type == target_type,
            or_(
                MarkupRule.target_value == target_value,
                MarkupRule.target_value == "DEFAULT"
            ),
            MarkupRule.is_active == True,
            MarkupRule.effective_from <= today,
            or_(
                MarkupRule.effective_to.is_(None),
                MarkupRule.effective_to >= today
            )
        )
    ).order_by(desc(MarkupRule.priority))

    result = await session.execute(stmt)
    rules = result.scalars().all()

    # Filter by branch and return highest priority
    for rule in rules:
        if not rule.applies_to_branches or branch_id in rule.applies_to_branches:
            return rule

    return None


async def recalculate_job_totals(
    session: AsyncSession,
    job_id: str
):
    """Recalculate job totals from parts, labour, overhead"""
    # Get all parts
    parts_stmt = select(func.sum(RepairJobPart.total_cost), func.sum(RepairJobPart.total_price_to_customer)).where(
        RepairJobPart.job_id == job_id
    )
    parts_result = await session.execute(parts_stmt)
    parts_row = parts_result.one()
    total_parts_cost = float(parts_row[0] or 0)
    total_parts_price = float(parts_row[1] or 0)

    # Get all labour
    labour_stmt = select(func.sum(RepairJobLabour.labour_cost), func.sum(RepairJobLabour.labour_price_to_customer)).where(
        RepairJobLabour.job_id == job_id
    )
    labour_result = await session.execute(labour_stmt)
    labour_row = labour_result.one()
    total_labour_cost = float(labour_row[0] or 0)
    total_labour_price = float(labour_row[1] or 0)

    # Get all overheads
    overhead_stmt = select(func.sum(RepairJobOverhead.cost), func.sum(RepairJobOverhead.price_to_customer)).where(
        RepairJobOverhead.job_id == job_id
    )
    overhead_result = await session.execute(overhead_stmt)
    overhead_row = overhead_result.one()
    total_overhead_cost = float(overhead_row[0] or 0)
    total_overhead_price = float(overhead_row[1] or 0)

    # Update job
    update_stmt = update(RepairJob).where(RepairJob.id == job_id).values(
        total_parts_cost=total_parts_cost,
        total_labour_cost=total_labour_cost,
        total_overhead_cost=total_overhead_cost,
        total_cost=total_parts_cost + total_labour_cost + total_overhead_cost,
        total_parts_price=total_parts_price,
        total_labour_price=total_labour_price,
        total_overhead_price=total_overhead_price,
        total_price=total_parts_price + total_labour_price + total_overhead_price
    )

    await session.execute(update_stmt)


# ============================================================================
# Repair Job Endpoints
# ============================================================================

@router.post("/", response_model=RepairJobOut, status_code=status.HTTP_201_CREATED)
async def create_repair_job(
    data: RepairJobCreateIn,
    current_user: User = Depends(require_permission("bicycles:write")),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Create new repair job

    Permissions: bicycles:write
    """
    # Verify bicycle exists
    bike_stmt = select(Bicycle).where(Bicycle.id == data.bicycle_id)
    bike_result = await session.execute(bike_stmt)
    bicycle = bike_result.scalar_one_or_none()

    if not bicycle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bicycle {data.bicycle_id} not found"
        )

    # Generate job number
    job_number = f"WO-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    job_id = f"JOB-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"

    job = RepairJob(
        id=job_id,
        job_number=job_number,
        bicycle_id=data.bicycle_id,
        branch_id=data.branch_id,
        job_type=data.job_type,
        status=RepairJobStatus.OPEN.value,
        odometer=data.odometer,
        customer_complaint=data.customer_complaint,
        mechanic_id=data.mechanic_id,
        created_by=str(current_user.id)
    )

    session.add(job)
    await session.commit()
    await session.refresh(job)

    job_dict = job.to_dict()
    job_dict["bicycle_info"] = {
        "title": bicycle.title,
        "license_plate": bicycle.license_plate
    }

    return RepairJobOut(**job_dict)


@router.get("/", response_model=RepairJobListResponse)
async def list_repair_jobs(
    bicycle_id: Optional[str] = Query(None),
    branch_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    job_type: Optional[str] = Query(None),
    mechanic_id: Optional[str] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    List repair jobs

    Permissions: All authenticated users
    """
    stmt = select(RepairJob, Bicycle).join(
        Bicycle, RepairJob.bicycle_id == Bicycle.id
    )

    if bicycle_id:
        stmt = stmt.where(RepairJob.bicycle_id == bicycle_id)

    if branch_id:
        stmt = stmt.where(RepairJob.branch_id == branch_id)

    if status:
        stmt = stmt.where(RepairJob.status == status)

    if job_type:
        stmt = stmt.where(RepairJob.job_type == job_type)

    if mechanic_id:
        stmt = stmt.where(RepairJob.mechanic_id == mechanic_id)

    # Get total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    count_result = await session.execute(count_stmt)
    total = count_result.scalar() or 0

    # Get paginated results
    stmt = stmt.order_by(desc(RepairJob.opened_at)).offset(offset).limit(limit)
    result = await session.execute(stmt)
    rows = result.all()

    items = []
    for job, bicycle in rows:
        job_dict = job.to_dict()
        job_dict["bicycle_info"] = {
            "title": bicycle.title,
            "license_plate": bicycle.license_plate
        }
        items.append(RepairJobOut(**job_dict))

    return RepairJobListResponse(
        items=items,
        total=total,
        offset=offset,
        limit=limit
    )


@router.get("/{job_id}", response_model=RepairJobOut)
async def get_repair_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get repair job details

    Permissions: All authenticated users
    """
    stmt = select(RepairJob, Bicycle).join(
        Bicycle, RepairJob.bicycle_id == Bicycle.id
    ).where(RepairJob.id == job_id)

    result = await session.execute(stmt)
    row = result.one_or_none()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repair job {job_id} not found"
        )

    job, bicycle = row
    job_dict = job.to_dict()
    job_dict["bicycle_info"] = {
        "title": bicycle.title,
        "license_plate": bicycle.license_plate
    }

    return RepairJobOut(**job_dict)


@router.post("/{job_id}/status", response_model=RepairJobOut)
async def update_job_status(
    job_id: str,
    data: JobUpdateStatusIn,
    current_user: User = Depends(require_permission("bicycles:write")),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Update job status and details

    Permissions: bicycles:write
    """
    stmt = select(RepairJob, Bicycle).join(
        Bicycle, RepairJob.bicycle_id == Bicycle.id
    ).where(RepairJob.id == job_id)

    result = await session.execute(stmt)
    row = result.one_or_none()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repair job {job_id} not found"
        )

    job, bicycle = row

    # Update status and timestamps
    job.status = data.status

    if data.status == RepairJobStatus.IN_PROGRESS.value and not job.started_at:
        job.started_at = datetime.utcnow()

    if data.status == RepairJobStatus.COMPLETED.value and not job.completed_at:
        job.completed_at = datetime.utcnow()

        # Update bicycle repair cost if this is a pre-sale overhaul
        if job.job_type == RepairJobType.FULL_OVERHAUL_BEFORE_SALE.value:
            bicycle.total_repair_cost = float(bicycle.total_repair_cost or 0) + float(job.total_cost)

    if data.status == RepairJobStatus.INVOICED.value and not job.closed_at:
        job.closed_at = datetime.utcnow()

    if data.diagnosis:
        job.diagnosis = data.diagnosis

    if data.work_performed:
        job.work_performed = data.work_performed

    if data.notes:
        job.notes = data.notes

    await session.commit()
    await session.refresh(job)

    job_dict = job.to_dict()
    job_dict["bicycle_info"] = {
        "title": bicycle.title,
        "license_plate": bicycle.license_plate
    }

    return RepairJobOut(**job_dict)


# ============================================================================
# Job Parts Endpoints
# ============================================================================

@router.post("/{job_id}/parts", response_model=JobPartOut, status_code=status.HTTP_201_CREATED)
async def add_part_to_job(
    job_id: str,
    data: JobPartAddIn,
    current_user: User = Depends(require_permission("bicycles:write")),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Add part to repair job (FIFO batch selection)

    Permissions: bicycles:write
    """
    # Get job
    job_stmt = select(RepairJob).where(RepairJob.id == job_id)
    job_result = await session.execute(job_stmt)
    job = job_result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repair job {job_id} not found"
        )

    if not job.can_edit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot add parts to job in {job.status} status"
        )

    # Get part
    part_stmt = select(Part).where(Part.id == data.part_id)
    part_result = await session.execute(part_stmt)
    part = part_result.scalar_one_or_none()

    if not part:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Part {data.part_id} not found"
        )

    # Get batch (FIFO)
    batch = await get_oldest_available_batch(
        session, data.part_id, job.branch_id, data.quantity_used
    )

    if not batch:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient stock for part {part.part_code} in branch {job.branch_id}"
        )

    # Calculate costs
    unit_cost = float(batch.purchase_price_per_unit)
    total_cost = unit_cost * data.quantity_used

    # Get markup rule for parts
    markup_rule = await get_applicable_markup_rule(
        session,
        MarkupTargetType.PART_CATEGORY.value,
        part.category,
        job.branch_id
    )

    if not markup_rule:
        # Try default parts markup
        markup_rule = await get_applicable_markup_rule(
            session,
            MarkupTargetType.PART_CATEGORY.value,
            "DEFAULT",
            job.branch_id
        )

    if markup_rule:
        unit_price = markup_rule.calculate_markup(unit_cost)
        total_price = unit_price * data.quantity_used
    else:
        unit_price = unit_cost
        total_price = total_cost

    # Create job part record
    job_part_id = f"JP-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"

    job_part = RepairJobPart(
        id=job_part_id,
        job_id=job_id,
        part_id=data.part_id,
        batch_id=batch.id,
        quantity_used=data.quantity_used,
        unit_cost=unit_cost,
        total_cost=total_cost,
        unit_price_to_customer=unit_price,
        total_price_to_customer=total_price,
        notes=data.notes
    )

    session.add(job_part)

    # Update batch quantity
    batch.quantity_available = float(batch.quantity_available) - data.quantity_used

    # Create stock movement
    movement_id = f"MOV-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"
    movement = PartStockMovement(
        id=movement_id,
        part_id=data.part_id,
        batch_id=batch.id,
        branch_id=job.branch_id,
        movement_type=StockMovementType.REPAIR_USAGE.value,
        quantity=-data.quantity_used,
        unit_cost=unit_cost,
        total_cost=-total_cost,
        related_doc_type="WORK_ORDER",
        related_doc_id=job.job_number,
        notes=f"Used in repair job {job.job_number}",
        created_by=str(current_user.id)
    )

    session.add(movement)

    # Recalculate job totals
    await recalculate_job_totals(session, job_id)

    await session.commit()
    await session.refresh(job_part)

    job_part_dict = job_part.to_dict()
    job_part_dict["part_name"] = part.name

    return JobPartOut(**job_part_dict)


@router.get("/{job_id}/parts", response_model=list[JobPartOut])
async def list_job_parts(
    job_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    List parts used in job

    Permissions: All authenticated users
    """
    stmt = select(RepairJobPart, Part).join(
        Part, RepairJobPart.part_id == Part.id
    ).where(RepairJobPart.job_id == job_id)

    result = await session.execute(stmt)
    rows = result.all()

    items = []
    for job_part, part in rows:
        job_part_dict = job_part.to_dict()
        job_part_dict["part_name"] = part.name
        items.append(JobPartOut(**job_part_dict))

    return items


# ============================================================================
# Job Labour Endpoints
# ============================================================================

@router.post("/{job_id}/labour", response_model=JobLabourOut, status_code=status.HTTP_201_CREATED)
async def add_labour_to_job(
    job_id: str,
    data: JobLabourAddIn,
    current_user: User = Depends(require_permission("bicycles:write")),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Add labour to repair job

    Permissions: bicycles:write
    """
    # Get job
    job_stmt = select(RepairJob).where(RepairJob.id == job_id)
    job_result = await session.execute(job_stmt)
    job = job_result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repair job {job_id} not found"
        )

    if not job.can_edit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot add labour to job in {job.status} status"
        )

    # Calculate costs
    labour_cost = data.hours * data.hourly_rate_cost

    # Get markup rule for labour
    markup_rule = await get_applicable_markup_rule(
        session,
        MarkupTargetType.LABOUR.value,
        "DEFAULT",
        job.branch_id
    )

    if markup_rule:
        hourly_rate_customer = markup_rule.calculate_markup(data.hourly_rate_cost)
        labour_price = hourly_rate_customer * data.hours
    else:
        hourly_rate_customer = data.hourly_rate_cost
        labour_price = labour_cost

    # Create job labour record
    labour_id = f"JL-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"

    job_labour = RepairJobLabour(
        id=labour_id,
        job_id=job_id,
        labour_code=data.labour_code,
        description=data.description,
        mechanic_id=data.mechanic_id,
        hours=data.hours,
        hourly_rate_cost=data.hourly_rate_cost,
        labour_cost=labour_cost,
        hourly_rate_customer=hourly_rate_customer,
        labour_price_to_customer=labour_price
    )

    session.add(job_labour)

    # Recalculate job totals
    await recalculate_job_totals(session, job_id)

    await session.commit()
    await session.refresh(job_labour)

    return JobLabourOut(**job_labour.to_dict())


@router.get("/{job_id}/labour", response_model=list[JobLabourOut])
async def list_job_labour(
    job_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    List labour for job

    Permissions: All authenticated users
    """
    stmt = select(RepairJobLabour).where(RepairJobLabour.job_id == job_id)
    result = await session.execute(stmt)
    labour_records = result.scalars().all()

    return [JobLabourOut(**labour.to_dict()) for labour in labour_records]


# ============================================================================
# Job Overhead Endpoints
# ============================================================================

@router.post("/{job_id}/overhead", response_model=JobOverheadOut, status_code=status.HTTP_201_CREATED)
async def add_overhead_to_job(
    job_id: str,
    data: JobOverheadAddIn,
    current_user: User = Depends(require_permission("bicycles:write")),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Add overhead to repair job

    Permissions: bicycles:write
    """
    # Get job
    job_stmt = select(RepairJob).where(RepairJob.id == job_id)
    job_result = await session.execute(job_stmt)
    job = job_result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repair job {job_id} not found"
        )

    if not job.can_edit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot add overhead to job in {job.status} status"
        )

    # Get markup rule for overhead
    markup_rule = await get_applicable_markup_rule(
        session,
        MarkupTargetType.OVERHEAD.value,
        "DEFAULT",
        job.branch_id
    )

    if markup_rule:
        price_to_customer = markup_rule.calculate_markup(data.cost)
    else:
        price_to_customer = data.cost

    # Create job overhead record
    overhead_id = f"JO-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"

    job_overhead = RepairJobOverhead(
        id=overhead_id,
        job_id=job_id,
        description=data.description,
        cost=data.cost,
        price_to_customer=price_to_customer
    )

    session.add(job_overhead)

    # Recalculate job totals
    await recalculate_job_totals(session, job_id)

    await session.commit()
    await session.refresh(job_overhead)

    return JobOverheadOut(**job_overhead.to_dict())


@router.get("/{job_id}/overhead", response_model=list[JobOverheadOut])
async def list_job_overhead(
    job_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    List overhead for job

    Permissions: All authenticated users
    """
    stmt = select(RepairJobOverhead).where(RepairJobOverhead.job_id == job_id)
    result = await session.execute(stmt)
    overhead_records = result.scalars().all()

    return [JobOverheadOut(**overhead.to_dict()) for overhead in overhead_records]


# ============================================================================
# Parts Return Endpoint
# ============================================================================

class PartReturnIn(BaseModel):
    """Return part from job"""
    job_part_id: str = Field(..., description="ID of the job part to return")
    return_quantity: float = Field(..., gt=0, description="Quantity to return")
    return_reason: str = Field(..., min_length=5, max_length=500, description="Reason for return")
    notes: Optional[str] = Field(None, max_length=1000)


class PartReturnOut(BaseModel):
    """Part return response"""
    id: str
    part_id: str
    batch_id: str
    job_id: str
    returned_quantity: float
    return_reason: str
    movement_id: str
    created_at: str


@router.post("/jobs/{job_id}/parts/return", response_model=PartReturnOut)
async def return_job_part(
    job_id: str,
    data: PartReturnIn,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Return part from repair job back to inventory

    Creates a RETURN stock movement and updates batch quantity.

    Permissions: All authenticated users
    """
    from datetime import datetime
    import secrets

    # Get the job part
    stmt = select(RepairJobPart).where(RepairJobPart.id == data.job_part_id)
    result = await session.execute(stmt)
    job_part = result.scalar_one_or_none()

    if not job_part:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job part {data.job_part_id} not found"
        )

    if job_part.job_id != job_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job part does not belong to this job"
        )

    # Validate return quantity
    if data.return_quantity > job_part.quantity_used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot return {data.return_quantity} - only {job_part.quantity_used} was used"
        )

    # Get the batch
    stmt = select(PartStockBatch).where(PartStockBatch.id == job_part.batch_id)
    result = await session.execute(stmt)
    batch = result.scalar_one_or_none()

    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock batch not found"
        )

    # Create RETURN movement
    movement_id = f"MOV-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"
    movement = PartStockMovement(
        id=movement_id,
        part_id=job_part.part_id,
        batch_id=job_part.batch_id,
        branch_id=batch.branch_id,
        movement_type="RETURN",
        quantity=data.return_quantity,
        unit_cost=job_part.unit_cost,
        total_cost=data.return_quantity * job_part.unit_cost,
        related_doc_type="REPAIR_JOB",
        related_doc_id=job_id,
        notes=f"{data.return_reason}. {data.notes or ''}",
        created_by=current_user.get("username", "unknown"),
    )
    session.add(movement)

    # Update batch quantity
    batch.quantity_available = float(batch.quantity_available) + data.return_quantity

    # Update job part quantity (reduce)
    job_part.quantity_used = float(job_part.quantity_used) - data.return_quantity
    job_part.total_cost = job_part.quantity_used * float(job_part.unit_cost)

    # Recalculate job totals
    await recalculate_job_totals(session, job_id)

    await session.commit()
    await session.refresh(movement)

    return PartReturnOut(
        id=movement.id,
        part_id=movement.part_id,
        batch_id=movement.batch_id,
        job_id=job_id,
        returned_quantity=data.return_quantity,
        return_reason=data.return_reason,
        movement_id=movement.id,
        created_at=movement.created_at.isoformat() if movement.created_at else datetime.utcnow().isoformat()
    )
