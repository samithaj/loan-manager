"""
Bike Lifecycle Router

API endpoints for managing second-hand bike lifecycle:
- Procurement (purchase/acquisition)
- Inventory management
- Cost summary calculation
- Stock number history
"""

from fastapi import APIRouter, HTTPException, Query, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import date, datetime

from ..db import SessionLocal
from ..models import Bicycle, StockNumberAssignment
from ..services.bike_lifecycle_service import BikeLifecycleService
from ..services.stock_number_service import StockNumberService
from ..rbac import require_permission, get_current_user, require_branch_access


router = APIRouter(prefix="/v1/bikes", tags=["bike-lifecycle"])


# ============================================================================
# Pydantic Models
# ============================================================================

class BikeProcurementRequest(BaseModel):
    """Bike procurement request"""
    branch_id: str = Field(..., description="Branch where bike is procured")
    business_model: Optional[str] = Field("STOCK", pattern="^(HIRE_PURCHASE|DIRECT_SALE|STOCK)$")

    # Basic info
    title: str = Field(..., min_length=5, max_length=200)
    brand: str = Field(..., min_length=2, max_length=100)
    model: str = Field(..., min_length=2, max_length=100)
    year: Optional[int] = Field(None, ge=1990, le=2030)
    condition: Optional[str] = Field("USED", pattern="^(NEW|USED)$")
    license_plate: Optional[str] = Field(None, max_length=50)
    frame_number: Optional[str] = Field(None, max_length=100)
    engine_number: Optional[str] = Field(None, max_length=100)
    mileage_km: Optional[int] = Field(None, ge=0)
    description: Optional[str] = Field(None, max_length=2000)

    # Pricing
    purchase_price: float = Field(..., gt=0, description="Purchase price")
    cash_price: Optional[float] = Field(None, gt=0)
    hire_purchase_price: Optional[float] = Field(None, gt=0)

    # Procurement details
    procurement_date: Optional[date] = None
    procurement_source: Optional[str] = Field(None, pattern="^(CUSTOMER|AUCTION|DEALER|TRADE_IN|OTHER)$")
    bought_method: Optional[str] = None
    hand_amount: Optional[float] = Field(None, ge=0)
    settlement_amount: Optional[float] = Field(None, ge=0)
    payment_branch_id: Optional[str] = None
    cr_location: Optional[str] = None
    buyer_employee_id: Optional[str] = None

    # Control flags
    first_od: Optional[str] = None
    ldate: Optional[date] = None
    sk_flag: Optional[bool] = False
    ls_flag: Optional[bool] = False
    caller: Optional[str] = None
    house_use: Optional[bool] = False


class BikeLifecycleOut(BaseModel):
    """Bike lifecycle output with all fields"""
    id: str
    company_id: Optional[str]
    business_model: str
    current_stock_number: Optional[str]
    current_branch_id: Optional[str]

    # Basic info
    title: str
    brand: str
    model: str
    year: int
    condition: str
    license_plate: Optional[str]
    frame_number: Optional[str]
    engine_number: Optional[str]
    mileage_km: Optional[int]
    description: Optional[str]
    branch_id: str
    status: str

    # Procurement
    procurement_date: Optional[str]
    procurement_source: Optional[str]
    bought_method: Optional[str]
    hand_amount: Optional[float]
    settlement_amount: Optional[float]

    # Cost tracking
    base_purchase_price: Optional[float]
    total_repair_cost: Optional[float]
    total_branch_expenses: float
    total_expenses: float

    # Sale tracking
    sold_date: Optional[str]
    selling_price: Optional[float]
    profit_or_loss: Optional[float]

    # Timestamps
    created_at: str
    updated_at: str


class BikeListResponse(BaseModel):
    """Paginated bike list"""
    items: list[BikeLifecycleOut]
    total: int
    offset: int
    limit: int


class BikeCostSummary(BaseModel):
    """Bike cost summary (summery.xlsx format)"""
    bicycle_id: str
    bike_no: Optional[str]
    model: str
    brand: str
    branch: Optional[str]
    stock_number: Optional[str]
    received_date: Optional[str]
    purchased_price: float
    branch_expenses: float
    garage_expenses: float
    total_expenses: float
    released_date: Optional[str]
    selling_price: Optional[float]
    profit_or_loss: Optional[float]
    status: str


class StockNumberHistoryItem(BaseModel):
    """Stock number assignment history item"""
    id: str
    company_id: str
    branch_id: str
    running_number: int
    full_stock_number: str
    assigned_date: str
    released_date: Optional[str]
    assignment_reason: str
    notes: Optional[str]
    is_current: bool


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/procure", response_model=BikeLifecycleOut, status_code=status.HTTP_201_CREATED)
async def procure_bike(
    data: BikeProcurementRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Procure (purchase/acquire) a new bike.
    Automatically assigns first stock number.

    Requires permission: bikes:write
    """
    require_permission(current_user, "bikes:write")
    require_branch_access(current_user, data.branch_id)

    async with SessionLocal() as db:
        try:
            bike = await BikeLifecycleService.procure_bike(
                db,
                procurement_data=data.model_dump()
            )
            await db.commit()
            await db.refresh(bike)

            return BikeLifecycleOut(**bike.to_dict())

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to procure bike: {str(e)}"
            )


@router.get("", response_model=BikeListResponse)
async def list_bikes(
    company_id: Optional[str] = Query(None, description="Filter by company"),
    branch_id: Optional[str] = Query(None, description="Filter by branch"),
    status: Optional[str] = Query(None, description="Filter by status"),
    business_model: Optional[str] = Query(None, description="Filter by business model"),
    stock_number: Optional[str] = Query(None, description="Search by stock number"),
    license_plate: Optional[str] = Query(None, description="Search by license plate"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
):
    """
    List bikes with filters and pagination.

    Query Parameters:
    - company_id: Filter by company
    - branch_id: Filter by branch
    - status: Filter by status
    - business_model: Filter by business model
    - stock_number: Search by stock number (partial match)
    - license_plate: Search by license plate (partial match)
    - offset: Pagination offset
    - limit: Items per page (max 200)
    """
    async with SessionLocal() as db:
        query = select(Bicycle).where(
            Bicycle.business_model.in_(["DIRECT_SALE", "STOCK"])
        )

        # Apply filters
        if company_id:
            query = query.where(Bicycle.company_id == company_id)

        if branch_id:
            query = query.where(Bicycle.current_branch_id == branch_id)

        if status:
            query = query.where(Bicycle.status == status)

        if business_model:
            query = query.where(Bicycle.business_model == business_model)

        if stock_number:
            query = query.where(Bicycle.current_stock_number.ilike(f"%{stock_number}%"))

        if license_plate:
            query = query.where(Bicycle.license_plate.ilike(f"%{license_plate}%"))

        # Get total count
        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar()

        # Apply pagination and ordering
        query = query.order_by(Bicycle.created_at.desc())
        query = query.offset(offset).limit(limit)

        result = await db.execute(query)
        bikes = list(result.scalars().all())

        return {
            "items": [BikeLifecycleOut(**b.to_dict()) for b in bikes],
            "total": total,
            "offset": offset,
            "limit": limit,
        }


@router.get("/{bike_id}", response_model=BikeLifecycleOut)
async def get_bike(
    bike_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get bike details by ID."""
    async with SessionLocal() as db:
        result = await db.execute(select(Bicycle).where(Bicycle.id == bike_id))
        bike = result.scalar_one_or_none()

        if not bike:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bike '{bike_id}' not found"
            )

        return BikeLifecycleOut(**bike.to_dict())


@router.get("/{bike_id}/cost-summary", response_model=BikeCostSummary)
async def get_bike_cost_summary(
    bike_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get detailed cost breakdown for a bike.
    Returns data in summery.xlsx format.
    """
    async with SessionLocal() as db:
        try:
            summary = await BikeLifecycleService.calculate_bike_cost_summary(db, bike_id)
            return BikeCostSummary(**summary)

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bike '{bike_id}' not found"
            )


@router.get("/{bike_id}/stock-history", response_model=list[StockNumberHistoryItem])
async def get_bike_stock_history(
    bike_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get stock number assignment history for a bike."""
    async with SessionLocal() as db:
        # First verify bike exists
        result = await db.execute(select(Bicycle).where(Bicycle.id == bike_id))
        bike = result.scalar_one_or_none()

        if not bike:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bike '{bike_id}' not found"
            )

        # Get stock number history
        history = await StockNumberService.get_assignment_history(db, bike_id)

        return [
            StockNumberHistoryItem(
                **assignment.to_dict(),
                is_current=assignment.is_current
            )
            for assignment in history
        ]


@router.put("/{bike_id}", response_model=BikeLifecycleOut)
async def update_bike(
    bike_id: str,
    data: dict,
    current_user: dict = Depends(get_current_user),
):
    """
    Update bike details (admin only).

    Requires permission: bikes:write
    """
    require_permission(current_user, "bikes:write")

    async with SessionLocal() as db:
        result = await db.execute(select(Bicycle).where(Bicycle.id == bike_id))
        bike = result.scalar_one_or_none()

        if not bike:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bike '{bike_id}' not found"
            )

        # Update only provided fields
        for key, value in data.items():
            if hasattr(bike, key):
                setattr(bike, key, value)

        await db.commit()
        await db.refresh(bike)

        return BikeLifecycleOut(**bike.to_dict())


@router.delete("/{bike_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bike(
    bike_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Delete bike (admin only).

    Requires permission: bikes:delete
    Note: This permanently deletes the bike and all related records (cascade).
    """
    require_permission(current_user, "bikes:delete")

    async with SessionLocal() as db:
        result = await db.execute(select(Bicycle).where(Bicycle.id == bike_id))
        bike = result.scalar_one_or_none()

        if not bike:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bike '{bike_id}' not found"
            )

        # Check if bike can be deleted (not sold)
        if bike.status == "SOLD":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete a sold bike"
            )

        await db.delete(bike)
        await db.commit()
