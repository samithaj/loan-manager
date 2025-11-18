from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, date
from typing import Optional, Dict, Any, List
import secrets

from ..db import get_db
from ..models.workshop_part import Part, PartStockBatch, PartStockMovement, PartCategory, StockMovementType
from ..models.workshop_markup import MarkupRule
from ..models.user import User
from ..rbac import require_permission, get_current_user


router = APIRouter(prefix="/v1/workshop/parts", tags=["workshop-parts"])


# ============================================================================
# Pydantic Models
# ============================================================================

class PartCreateIn(BaseModel):
    """Create new part"""
    part_code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    category: str
    brand: Optional[str] = Field(None, max_length=100)
    unit: str = Field("pcs", max_length=20)
    is_universal: bool = False
    bike_model_compatibility: Optional[Dict[str, Any]] = None
    minimum_stock_level: float = Field(0, ge=0)
    reorder_point: float = Field(0, ge=0)


class PartOut(BaseModel):
    """Part response"""
    id: str
    part_code: str
    name: str
    description: Optional[str] = None
    category: str
    brand: Optional[str] = None
    unit: str
    is_universal: bool
    bike_model_compatibility: Optional[Dict[str, Any]] = None
    minimum_stock_level: float
    reorder_point: float
    is_active: bool
    created_at: str
    updated_at: str


class PartListResponse(BaseModel):
    """Paginated part list"""
    items: list[PartOut]
    total: int
    offset: int
    limit: int


class StockBatchCreateIn(BaseModel):
    """Create stock batch (purchase)"""
    part_id: str
    supplier_id: Optional[str] = None
    branch_id: str
    purchase_date: date
    purchase_price_per_unit: float = Field(..., gt=0)
    quantity_received: float = Field(..., gt=0)
    expiry_date: Optional[date] = None
    invoice_no: Optional[str] = Field(None, max_length=100)
    grn_no: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=2000)


class StockBatchOut(BaseModel):
    """Stock batch response"""
    id: str
    part_id: str
    part_name: Optional[str] = None
    supplier_id: Optional[str] = None
    branch_id: str
    purchase_date: str
    purchase_price_per_unit: float
    quantity_received: float
    quantity_available: float
    expiry_date: Optional[str] = None
    invoice_no: Optional[str] = None
    grn_no: Optional[str] = None
    notes: Optional[str] = None
    created_at: str
    updated_at: str


class StockBatchListResponse(BaseModel):
    """Paginated stock batch list"""
    items: list[StockBatchOut]
    total: int
    offset: int
    limit: int


class StockMovementOut(BaseModel):
    """Stock movement response"""
    id: str
    part_id: str
    part_name: Optional[str] = None
    batch_id: Optional[str] = None
    branch_id: str
    movement_type: str
    quantity: float
    unit_cost: Optional[float] = None
    total_cost: Optional[float] = None
    related_doc_type: Optional[str] = None
    related_doc_id: Optional[str] = None
    notes: Optional[str] = None
    created_by: Optional[str] = None
    created_at: str


class StockMovementListResponse(BaseModel):
    """Paginated stock movement list"""
    items: list[StockMovementOut]
    total: int
    offset: int
    limit: int


class StockAdjustmentIn(BaseModel):
    """Stock adjustment"""
    part_id: str
    branch_id: str
    quantity: float  # Positive or negative
    reason: str = Field(..., min_length=5, max_length=2000)


class StockSummaryOut(BaseModel):
    """Stock summary by part"""
    part_id: str
    part_code: str
    part_name: str
    category: str
    branch_id: str
    total_quantity: float
    average_cost: float
    total_value: float
    below_minimum: bool


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
            PartStockBatch.quantity_available > 0,
            or_(
                PartStockBatch.expiry_date.is_(None),
                PartStockBatch.expiry_date > date.today()
            )
        )
    ).order_by(PartStockBatch.purchase_date)

    result = await session.execute(stmt)
    batches = result.scalars().all()

    for batch in batches:
        if float(batch.quantity_available) >= quantity_needed:
            return batch

    # If no single batch has enough, return the oldest batch
    return batches[0] if batches else None


# ============================================================================
# Parts Endpoints
# ============================================================================

@router.post("/", response_model=PartOut, status_code=status.HTTP_201_CREATED)
async def create_part(
    data: PartCreateIn,
    current_user: User = Depends(require_permission("bicycles:write")),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Create a new part

    Permissions: bicycles:write (inventory_manager, branch_manager, admin)
    """
    # Check if part code already exists
    stmt = select(Part).where(Part.part_code == data.part_code)
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Part code {data.part_code} already exists"
        )

    part_id = f"PART-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"

    part = Part(
        id=part_id,
        part_code=data.part_code,
        name=data.name,
        description=data.description,
        category=data.category,
        brand=data.brand,
        unit=data.unit,
        is_universal=data.is_universal,
        bike_model_compatibility=data.bike_model_compatibility,
        minimum_stock_level=data.minimum_stock_level,
        reorder_point=data.reorder_point
    )

    session.add(part)
    await session.commit()
    await session.refresh(part)

    return PartOut(**part.to_dict())


@router.get("/", response_model=PartListResponse)
async def list_parts(
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None, description="Search by code or name"),
    active_only: bool = Query(True),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    List parts with filters

    Permissions: All authenticated users can view parts
    """
    stmt = select(Part)

    if active_only:
        stmt = stmt.where(Part.is_active == True)

    if category:
        stmt = stmt.where(Part.category == category)

    if search:
        search_term = f"%{search}%"
        stmt = stmt.where(
            or_(
                Part.part_code.ilike(search_term),
                Part.name.ilike(search_term),
                Part.brand.ilike(search_term)
            )
        )

    # Get total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    count_result = await session.execute(count_stmt)
    total = count_result.scalar() or 0

    # Get paginated results
    stmt = stmt.order_by(Part.part_code).offset(offset).limit(limit)
    result = await session.execute(stmt)
    parts = result.scalars().all()

    items = [PartOut(**part.to_dict()) for part in parts]

    return PartListResponse(
        items=items,
        total=total,
        offset=offset,
        limit=limit
    )


@router.get("/{part_id}", response_model=PartOut)
async def get_part(
    part_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get a specific part

    Permissions: All authenticated users can view parts
    """
    stmt = select(Part).where(Part.id == part_id)
    result = await session.execute(stmt)
    part = result.scalar_one_or_none()

    if not part:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Part {part_id} not found"
        )

    return PartOut(**part.to_dict())


# ============================================================================
# Stock Batch Endpoints
# ============================================================================

@router.post("/batches", response_model=StockBatchOut, status_code=status.HTTP_201_CREATED)
async def create_stock_batch(
    data: StockBatchCreateIn,
    current_user: User = Depends(require_permission("bicycles:write")),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Create stock batch (record purchase)

    Permissions: bicycles:write
    """
    # Verify part exists
    part_stmt = select(Part).where(Part.id == data.part_id)
    part_result = await session.execute(part_stmt)
    part = part_result.scalar_one_or_none()

    if not part:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Part {data.part_id} not found"
        )

    batch_id = f"BATCH-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"

    batch = PartStockBatch(
        id=batch_id,
        part_id=data.part_id,
        supplier_id=data.supplier_id,
        branch_id=data.branch_id,
        purchase_date=data.purchase_date,
        purchase_price_per_unit=data.purchase_price_per_unit,
        quantity_received=data.quantity_received,
        quantity_available=data.quantity_received,  # Initially all available
        expiry_date=data.expiry_date,
        invoice_no=data.invoice_no,
        grn_no=data.grn_no,
        notes=data.notes
    )

    session.add(batch)

    # Create stock movement record
    movement_id = f"MOV-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"
    movement = PartStockMovement(
        id=movement_id,
        part_id=data.part_id,
        batch_id=batch_id,
        branch_id=data.branch_id,
        movement_type=StockMovementType.PURCHASE.value,
        quantity=data.quantity_received,
        unit_cost=data.purchase_price_per_unit,
        total_cost=data.quantity_received * data.purchase_price_per_unit,
        related_doc_type="PURCHASE_ORDER",
        related_doc_id=data.invoice_no,
        notes=data.notes,
        created_by=str(current_user.id)
    )

    session.add(movement)

    await session.commit()
    await session.refresh(batch)

    batch_dict = batch.to_dict()
    batch_dict["part_name"] = part.name

    return StockBatchOut(**batch_dict)


@router.get("/batches", response_model=StockBatchListResponse)
async def list_stock_batches(
    part_id: Optional[str] = Query(None),
    branch_id: Optional[str] = Query(None),
    available_only: bool = Query(False),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    List stock batches

    Permissions: All authenticated users can view stock
    """
    stmt = select(PartStockBatch, Part).join(
        Part, PartStockBatch.part_id == Part.id
    )

    if part_id:
        stmt = stmt.where(PartStockBatch.part_id == part_id)

    if branch_id:
        stmt = stmt.where(PartStockBatch.branch_id == branch_id)

    if available_only:
        stmt = stmt.where(PartStockBatch.quantity_available > 0)

    # Get total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    count_result = await session.execute(count_stmt)
    total = count_result.scalar() or 0

    # Get paginated results
    stmt = stmt.order_by(desc(PartStockBatch.purchase_date)).offset(offset).limit(limit)
    result = await session.execute(stmt)
    rows = result.all()

    items = []
    for batch, part in rows:
        batch_dict = batch.to_dict()
        batch_dict["part_name"] = part.name
        items.append(StockBatchOut(**batch_dict))

    return StockBatchListResponse(
        items=items,
        total=total,
        offset=offset,
        limit=limit
    )


# ============================================================================
# Stock Movement Endpoints
# ============================================================================

@router.get("/movements", response_model=StockMovementListResponse)
async def list_stock_movements(
    part_id: Optional[str] = Query(None),
    branch_id: Optional[str] = Query(None),
    movement_type: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    List stock movements (audit trail)

    Permissions: All authenticated users can view movements
    """
    stmt = select(PartStockMovement, Part).join(
        Part, PartStockMovement.part_id == Part.id
    )

    if part_id:
        stmt = stmt.where(PartStockMovement.part_id == part_id)

    if branch_id:
        stmt = stmt.where(PartStockMovement.branch_id == branch_id)

    if movement_type:
        stmt = stmt.where(PartStockMovement.movement_type == movement_type)

    if date_from:
        stmt = stmt.where(PartStockMovement.created_at >= datetime.combine(date_from, datetime.min.time()))

    if date_to:
        stmt = stmt.where(PartStockMovement.created_at <= datetime.combine(date_to, datetime.max.time()))

    # Get total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    count_result = await session.execute(count_stmt)
    total = count_result.scalar() or 0

    # Get paginated results
    stmt = stmt.order_by(desc(PartStockMovement.created_at)).offset(offset).limit(limit)
    result = await session.execute(stmt)
    rows = result.all()

    items = []
    for movement, part in rows:
        movement_dict = movement.to_dict()
        movement_dict["part_name"] = part.name
        items.append(StockMovementOut(**movement_dict))

    return StockMovementListResponse(
        items=items,
        total=total,
        offset=offset,
        limit=limit
    )


# ============================================================================
# Stock Summary & Reporting Endpoints
# ============================================================================

@router.get("/summary", response_model=list[StockSummaryOut])
async def get_stock_summary(
    branch_id: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    below_minimum_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get stock summary by part and branch

    Permissions: All authenticated users can view summary
    """
    # Build query to aggregate stock
    from sqlalchemy import case

    stmt = select(
        Part.id,
        Part.part_code,
        Part.name,
        Part.category,
        Part.minimum_stock_level,
        PartStockBatch.branch_id,
        func.sum(PartStockBatch.quantity_available).label("total_quantity"),
        func.avg(PartStockBatch.purchase_price_per_unit).label("average_cost")
    ).join(
        PartStockBatch, Part.id == PartStockBatch.part_id
    ).where(
        Part.is_active == True
    ).group_by(
        Part.id,
        Part.part_code,
        Part.name,
        Part.category,
        Part.minimum_stock_level,
        PartStockBatch.branch_id
    )

    if branch_id:
        stmt = stmt.where(PartStockBatch.branch_id == branch_id)

    if category:
        stmt = stmt.where(Part.category == category)

    result = await session.execute(stmt)
    rows = result.all()

    summaries = []
    for row in rows:
        total_quantity = float(row.total_quantity or 0)
        average_cost = float(row.average_cost or 0)
        minimum_stock = float(row.minimum_stock_level or 0)
        total_value = total_quantity * average_cost
        below_minimum = total_quantity < minimum_stock

        if below_minimum_only and not below_minimum:
            continue

        summaries.append(StockSummaryOut(
            part_id=row.id,
            part_code=row.part_code,
            part_name=row.name,
            category=row.category,
            branch_id=row.branch_id,
            total_quantity=total_quantity,
            average_cost=average_cost,
            total_value=total_value,
            below_minimum=below_minimum
        ))

    return summaries


# ============================================================================
# Stock Adjustment Endpoints
# ============================================================================

@router.post("/adjust", status_code=status.HTTP_200_OK)
async def adjust_stock(
    data: StockAdjustmentIn,
    current_user: User = Depends(require_permission("bicycles:write")),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Adjust stock quantity (manual adjustment)

    Permissions: bicycles:write
    """
    # Find most recent batch for this part and branch
    batch_stmt = select(PartStockBatch).where(
        and_(
            PartStockBatch.part_id == data.part_id,
            PartStockBatch.branch_id == data.branch_id
        )
    ).order_by(desc(PartStockBatch.purchase_date)).limit(1)

    batch_result = await session.execute(batch_stmt)
    batch = batch_result.scalar_one_or_none()

    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No stock batches found for part {data.part_id} in branch {data.branch_id}"
        )

    # Update batch quantity
    new_available = float(batch.quantity_available) + data.quantity

    if new_available < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Adjustment would result in negative stock. Available: {batch.quantity_available}, Adjustment: {data.quantity}"
        )

    batch.quantity_available = new_available

    # Create movement record
    movement_id = f"MOV-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"
    movement = PartStockMovement(
        id=movement_id,
        part_id=data.part_id,
        batch_id=batch.id,
        branch_id=data.branch_id,
        movement_type=StockMovementType.ADJUSTMENT.value,
        quantity=data.quantity,
        unit_cost=float(batch.purchase_price_per_unit),
        total_cost=data.quantity * float(batch.purchase_price_per_unit),
        notes=data.reason,
        created_by=str(current_user.id)
    )

    session.add(movement)
    await session.commit()

    return {"message": "Stock adjusted successfully", "new_quantity": new_available}
