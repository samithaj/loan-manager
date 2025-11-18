"""
Bike Sales Router

API endpoints for managing bicycle sales:
- Record bike sales
- View sales records
- Generate profit reports
- Commission tracking
"""

from fastapi import APIRouter, HTTPException, Query, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import date
from decimal import Decimal

from ..db import SessionLocal
from ..models import BicycleSale, BonusPayment
from ..services.bike_lifecycle_service import BikeLifecycleService
from ..services.commission_service import CommissionService
from ..rbac import require_permission, get_current_user


router = APIRouter(prefix="/v1", tags=["bike-sales"])


# ============================================================================
# Pydantic Models
# ============================================================================

class BikeSaleRequest(BaseModel):
    """Bike sale request"""
    selling_price: float = Field(..., gt=0, description="Selling price")
    payment_method: str = Field(..., pattern="^(CASH|FINANCE|TRADE_IN|BANK_TRANSFER|MIXED)$")
    selling_branch_id: Optional[str] = Field(None, description="Selling branch (defaults to current branch)")
    sale_date: Optional[date] = None

    # Customer details
    customer_name: Optional[str] = Field(None, max_length=200)
    customer_phone: Optional[str] = Field(None, max_length=50)
    customer_email: Optional[str] = Field(None, max_length=200)
    customer_address: Optional[str] = Field(None, max_length=500)
    customer_nic: Optional[str] = Field(None, max_length=50)

    # Trade-in details
    trade_in_bicycle_id: Optional[str] = None
    trade_in_value: Optional[float] = Field(None, ge=0)

    # Finance details
    finance_institution: Optional[str] = Field(None, max_length=200)
    down_payment: Optional[float] = Field(None, ge=0)
    financed_amount: Optional[float] = Field(None, ge=0)

    # Sale details
    sale_invoice_number: Optional[str] = Field(None, max_length=100)
    delivery_date: Optional[date] = None
    warranty_months: Optional[int] = Field(None, ge=0, le=60)
    notes: Optional[str] = Field(None, max_length=1000)


class BikeSaleOut(BaseModel):
    """Bike sale output"""
    id: str
    bicycle_id: str
    selling_branch_id: str
    selling_company_id: str
    stock_number_at_sale: Optional[str]
    sale_date: str
    selling_price: float
    payment_method: str

    # Customer details
    customer_name: Optional[str]
    customer_phone: Optional[str]
    customer_email: Optional[str]
    customer_address: Optional[str]
    customer_nic: Optional[str]

    # Trade-in details
    trade_in_bicycle_id: Optional[str]
    trade_in_value: Optional[float]

    # Finance details
    finance_institution: Optional[str]
    down_payment: Optional[float]
    financed_amount: Optional[float]

    # Sale details
    sold_by: str
    sale_invoice_number: Optional[str]
    delivery_date: Optional[str]
    warranty_months: Optional[int]

    # Computed fields
    total_cost: Optional[float]
    profit_or_loss: Optional[float]

    notes: Optional[str]


class SaleListResponse(BaseModel):
    """Paginated sale list"""
    items: list[BikeSaleOut]
    total: int
    offset: int
    limit: int


class ProfitReportItem(BaseModel):
    """Profit report item"""
    bicycle_id: str
    bike_no: Optional[str]
    stock_number: Optional[str]
    sale_date: str
    selling_branch_id: str
    selling_price: float
    total_cost: float
    profit_or_loss: float


class ProfitReportResponse(BaseModel):
    """Profit report response"""
    items: list[ProfitReportItem]
    total_sales: int
    total_selling_price: float
    total_cost: float
    total_profit: float
    average_profit_per_sale: float


class CommissionOut(BaseModel):
    """Commission payment output"""
    id: str
    bicycle_sale_id: str
    commission_type: str
    bonus_amount: float
    status: str
    calculation_details: Optional[dict]


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/bikes/{bike_id}/sell", response_model=BikeSaleOut, status_code=status.HTTP_201_CREATED)
async def sell_bike(
    bike_id: str,
    data: BikeSaleRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Record a bike sale.
    Automatically calculates P&L and triggers commission.

    Requires permission: bikes:sell
    """
    require_permission(current_user, "bikes:sell")

    async with SessionLocal() as db:
        try:
            # Get user identifier for sold_by
            user_id = current_user.get("id") or current_user.get("sub") or "unknown"

            # Prepare sale data
            sale_data = data.model_dump()
            sale_data["sold_by"] = str(user_id)

            # Execute sale
            sale = await BikeLifecycleService.sell_bike(
                db,
                bicycle_id=bike_id,
                sale_data=sale_data
            )

            await db.commit()
            await db.refresh(sale)

            return BikeSaleOut(**sale.to_dict())

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to record sale: {str(e)}"
            )


@router.get("/sales", response_model=SaleListResponse)
async def list_sales(
    company_id: Optional[str] = Query(None, description="Filter by company"),
    branch_id: Optional[str] = Query(None, description="Filter by branch"),
    start_date: Optional[date] = Query(None, description="Filter sales from date"),
    end_date: Optional[date] = Query(None, description="Filter sales to date"),
    payment_method: Optional[str] = Query(None, description="Filter by payment method"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
):
    """
    List sales with filters and pagination.

    Query Parameters:
    - company_id: Filter by company
    - branch_id: Filter by selling branch
    - start_date: Filter sales from date
    - end_date: Filter sales to date
    - payment_method: Filter by payment method
    - offset: Pagination offset
    - limit: Items per page (max 200)
    """
    async with SessionLocal() as db:
        query = select(BicycleSale)

        # Apply filters
        if company_id:
            query = query.where(BicycleSale.selling_company_id == company_id)

        if branch_id:
            query = query.where(BicycleSale.selling_branch_id == branch_id)

        if start_date:
            query = query.where(BicycleSale.sale_date >= start_date)

        if end_date:
            query = query.where(BicycleSale.sale_date <= end_date)

        if payment_method:
            query = query.where(BicycleSale.payment_method == payment_method)

        # Get total count
        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar()

        # Apply pagination and ordering
        query = query.order_by(BicycleSale.sale_date.desc())
        query = query.offset(offset).limit(limit)

        result = await db.execute(query)
        sales = list(result.scalars().all())

        return {
            "items": [BikeSaleOut(**s.to_dict()) for s in sales],
            "total": total,
            "offset": offset,
            "limit": limit,
        }


@router.get("/sales/{sale_id}", response_model=BikeSaleOut)
async def get_sale(
    sale_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get sale details by ID."""
    async with SessionLocal() as db:
        result = await db.execute(
            select(BicycleSale).where(BicycleSale.id == sale_id)
        )
        sale = result.scalar_one_or_none()

        if not sale:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sale '{sale_id}' not found"
            )

        return BikeSaleOut(**sale.to_dict())


@router.get("/sales/{sale_id}/commissions", response_model=list[CommissionOut])
async def get_sale_commissions(
    sale_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get commission payments for a specific sale."""
    async with SessionLocal() as db:
        # First verify sale exists
        result = await db.execute(
            select(BicycleSale).where(BicycleSale.id == sale_id)
        )
        sale = result.scalar_one_or_none()

        if not sale:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sale '{sale_id}' not found"
            )

        # Get commissions
        commissions = await CommissionService.get_sale_commissions(db, sale_id)

        return [
            CommissionOut(
                id=c.id,
                bicycle_sale_id=c.bicycle_sale_id,
                commission_type=c.commission_type,
                bonus_amount=float(c.bonus_amount),
                status=c.status,
                calculation_details=c.calculation_details
            )
            for c in commissions
        ]


@router.get("/sales/profit-report", response_model=ProfitReportResponse)
async def get_profit_report(
    company_id: Optional[str] = Query(None, description="Filter by company"),
    branch_id: Optional[str] = Query(None, description="Filter by branch"),
    start_date: Optional[date] = Query(None, description="Report start date"),
    end_date: Optional[date] = Query(None, description="Report end date"),
    current_user: dict = Depends(get_current_user),
):
    """
    Generate profit/loss report for bike sales.

    Query Parameters:
    - company_id: Filter by company
    - branch_id: Filter by selling branch
    - start_date: Report start date
    - end_date: Report end date
    """
    async with SessionLocal() as db:
        query = select(BicycleSale)

        # Apply filters
        if company_id:
            query = query.where(BicycleSale.selling_company_id == company_id)

        if branch_id:
            query = query.where(BicycleSale.selling_branch_id == branch_id)

        if start_date:
            query = query.where(BicycleSale.sale_date >= start_date)

        if end_date:
            query = query.where(BicycleSale.sale_date <= end_date)

        query = query.order_by(BicycleSale.sale_date.desc())

        result = await db.execute(query)
        sales = list(result.scalars().all())

        # Calculate aggregates
        total_selling_price = sum(float(s.selling_price) for s in sales)
        total_cost = sum(float(s.total_cost or 0) for s in sales)
        total_profit = sum(float(s.profit_or_loss or 0) for s in sales)
        average_profit = total_profit / len(sales) if sales else 0

        # Build report items
        items = []
        for sale in sales:
            # Get bike info from relationship (if available)
            bike_no = None
            if hasattr(sale, 'bicycle') and sale.bicycle:
                bike_no = sale.bicycle.license_plate

            items.append(ProfitReportItem(
                bicycle_id=sale.bicycle_id,
                bike_no=bike_no,
                stock_number=sale.stock_number_at_sale,
                sale_date=sale.sale_date.isoformat(),
                selling_branch_id=sale.selling_branch_id,
                selling_price=float(sale.selling_price),
                total_cost=float(sale.total_cost or 0),
                profit_or_loss=float(sale.profit_or_loss or 0)
            ))

        return ProfitReportResponse(
            items=items,
            total_sales=len(sales),
            total_selling_price=total_selling_price,
            total_cost=total_cost,
            total_profit=total_profit,
            average_profit_per_sale=average_profit
        )
