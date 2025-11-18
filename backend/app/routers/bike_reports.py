"""
Bike Reports Router

API endpoints for bike lifecycle reports:
- Acquisition ledger (November notebook)
- Cost summary (summery.xlsx)
- Branch commissions
- Stock summary by branch
"""

from fastapi import APIRouter, HTTPException, Query, Depends, status
from pydantic import BaseModel
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import date

from ..db import SessionLocal
from ..models import Bicycle, BicycleSale, BicycleBranchExpense
from ..services.commission_service import CommissionService
from ..rbac import get_current_user


router = APIRouter(prefix="/v1/reports", tags=["bike-reports"])


# ============================================================================
# Pydantic Models
# ============================================================================

class AcquisitionLedgerItem(BaseModel):
    """Acquisition ledger item (November notebook format)"""
    bicycle_id: str
    stock_number: Optional[str]
    license_plate: Optional[str]
    model: str
    procurement_date: Optional[str]
    procurement_source: Optional[str]
    bought_method: Optional[str]
    purchase_price: float
    hand_amount: Optional[float]
    settlement_amount: Optional[float]
    payment_branch_id: Optional[str]
    cr_location: Optional[str]
    buyer_employee_id: Optional[str]
    first_od: Optional[str]
    ldate: Optional[str]
    sk_flag: bool
    ls_flag: bool
    caller: Optional[str]
    house_use: bool
    status: str


class AcquisitionLedgerResponse(BaseModel):
    """Acquisition ledger response"""
    items: list[AcquisitionLedgerItem]
    total: int
    total_investment: float


class CostSummaryItem(BaseModel):
    """Cost summary item (summery.xlsx format)"""
    bicycle_id: str
    bike_no: Optional[str]
    stock_number: Optional[str]
    branch_name: Optional[str]
    model: str
    received_date: Optional[str]
    purchased_price: float
    branch_expenses: float
    garage_expenses: float
    total_expenses: float
    released_date: Optional[str]
    selling_price: Optional[float]
    profit_or_loss: Optional[float]
    status: str


class CostSummaryResponse(BaseModel):
    """Cost summary response"""
    items: list[CostSummaryItem]
    total: int
    total_purchased_price: float
    total_branch_expenses: float
    total_garage_expenses: float
    total_expenses: float
    total_selling_price: float
    total_profit_or_loss: float


class BranchCommissionReport(BaseModel):
    """Branch commission report"""
    branch_id: str
    start_date: str
    end_date: str
    buyer_commission: float
    seller_commission: float
    total_commission: float
    sale_count: int
    payment_count: int


class BranchStockItem(BaseModel):
    """Branch stock summary item"""
    branch_id: str
    branch_name: str
    company_id: Optional[str]
    status: str
    bike_count: int
    total_value: float


class BranchStockResponse(BaseModel):
    """Branch stock summary response"""
    items: list[BranchStockItem]
    total_bikes: int
    total_value: float


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/acquisition-ledger", response_model=AcquisitionLedgerResponse)
async def get_acquisition_ledger(
    company_id: Optional[str] = Query(None, description="Filter by company"),
    branch_id: Optional[str] = Query(None, description="Filter by branch"),
    start_date: Optional[date] = Query(None, description="Filter from procurement date"),
    end_date: Optional[date] = Query(None, description="Filter to procurement date"),
    procurement_source: Optional[str] = Query(None, description="Filter by source"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get acquisition ledger (November notebook format).
    Shows all bike procurement records.

    Query Parameters:
    - company_id: Filter by company
    - branch_id: Filter by branch
    - start_date: Filter from procurement date
    - end_date: Filter to procurement date
    - procurement_source: Filter by procurement source
    """
    async with SessionLocal() as db:
        query = select(Bicycle).where(
            Bicycle.business_model.in_(["DIRECT_SALE", "STOCK"])
        )

        # Apply filters
        if company_id:
            query = query.where(Bicycle.company_id == company_id)

        if branch_id:
            query = query.where(Bicycle.branch_id == branch_id)

        if start_date:
            query = query.where(Bicycle.procurement_date >= start_date)

        if end_date:
            query = query.where(Bicycle.procurement_date <= end_date)

        if procurement_source:
            query = query.where(Bicycle.procurement_source == procurement_source)

        query = query.order_by(Bicycle.procurement_date.desc())

        result = await db.execute(query)
        bikes = list(result.scalars().all())

        # Calculate total investment
        total_investment = sum(float(b.base_purchase_price or 0) for b in bikes)

        items = []
        for bike in bikes:
            items.append(AcquisitionLedgerItem(
                bicycle_id=bike.id,
                stock_number=bike.current_stock_number,
                license_plate=bike.license_plate,
                model=bike.model,
                procurement_date=bike.procurement_date.isoformat() if bike.procurement_date else None,
                procurement_source=bike.procurement_source,
                bought_method=bike.bought_method,
                purchase_price=float(bike.base_purchase_price or 0),
                hand_amount=float(bike.hand_amount) if bike.hand_amount else None,
                settlement_amount=float(bike.settlement_amount) if bike.settlement_amount else None,
                payment_branch_id=bike.payment_branch_id,
                cr_location=bike.cr_location,
                buyer_employee_id=bike.buyer_employee_id,
                first_od=bike.first_od,
                ldate=bike.ldate.isoformat() if bike.ldate else None,
                sk_flag=bike.sk_flag,
                ls_flag=bike.ls_flag,
                caller=bike.caller,
                house_use=bike.house_use,
                status=bike.status
            ))

        return AcquisitionLedgerResponse(
            items=items,
            total=len(bikes),
            total_investment=total_investment
        )


@router.get("/cost-summary", response_model=CostSummaryResponse)
async def get_cost_summary(
    company_id: Optional[str] = Query(None, description="Filter by company"),
    branch_id: Optional[str] = Query(None, description="Filter by branch"),
    status: Optional[str] = Query(None, description="Filter by status"),
    start_date: Optional[date] = Query(None, description="Filter from procurement date"),
    end_date: Optional[date] = Query(None, description="Filter to procurement date"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get cost summary report (summery.xlsx format).
    Shows purchase price, expenses, selling price, and P&L per bike.

    Query Parameters:
    - company_id: Filter by company
    - branch_id: Filter by current branch
    - status: Filter by bike status
    - start_date: Filter from procurement date
    - end_date: Filter to procurement date
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

        if start_date:
            query = query.where(Bicycle.procurement_date >= start_date)

        if end_date:
            query = query.where(Bicycle.procurement_date <= end_date)

        query = query.order_by(Bicycle.procurement_date.desc())

        result = await db.execute(query)
        bikes = list(result.scalars().all())

        # Calculate aggregates
        total_purchased_price = 0
        total_branch_expenses = 0
        total_garage_expenses = 0
        total_expenses = 0
        total_selling_price = 0
        total_profit_or_loss = 0

        items = []
        for bike in bikes:
            purchased_price = float(bike.base_purchase_price or 0)
            branch_expenses = bike.get_total_branch_expenses
            garage_expenses = float(bike.total_repair_cost or 0)
            expenses = purchased_price + branch_expenses + garage_expenses
            selling_price = float(bike.selling_price or 0)
            profit_or_loss = selling_price - expenses if bike.selling_price else None

            total_purchased_price += purchased_price
            total_branch_expenses += branch_expenses
            total_garage_expenses += garage_expenses
            total_expenses += expenses
            total_selling_price += selling_price
            if profit_or_loss:
                total_profit_or_loss += profit_or_loss

            items.append(CostSummaryItem(
                bicycle_id=bike.id,
                bike_no=bike.license_plate,
                stock_number=bike.current_stock_number,
                branch_name=bike.current_branch_id,
                model=bike.model,
                received_date=bike.procurement_date.isoformat() if bike.procurement_date else None,
                purchased_price=purchased_price,
                branch_expenses=branch_expenses,
                garage_expenses=garage_expenses,
                total_expenses=expenses,
                released_date=bike.sold_date.isoformat() if bike.sold_date else None,
                selling_price=selling_price if bike.selling_price else None,
                profit_or_loss=profit_or_loss,
                status=bike.status
            ))

        return CostSummaryResponse(
            items=items,
            total=len(bikes),
            total_purchased_price=total_purchased_price,
            total_branch_expenses=total_branch_expenses,
            total_garage_expenses=total_garage_expenses,
            total_expenses=total_expenses,
            total_selling_price=total_selling_price,
            total_profit_or_loss=total_profit_or_loss
        )


@router.get("/branch-commissions", response_model=BranchCommissionReport)
async def get_branch_commission_report(
    branch_id: str = Query(..., description="Branch ID"),
    start_date: date = Query(..., description="Report start date"),
    end_date: date = Query(..., description="Report end date"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get commission report for a specific branch.

    Query Parameters:
    - branch_id: Branch ID (required)
    - start_date: Report start date (required)
    - end_date: Report end date (required)
    """
    async with SessionLocal() as db:
        report = await CommissionService.get_branch_commission_report(
            db,
            branch_id=branch_id,
            start_date=start_date,
            end_date=end_date
        )

        return BranchCommissionReport(**report)


@router.get("/branch-stock", response_model=BranchStockResponse)
async def get_branch_stock_summary(
    company_id: Optional[str] = Query(None, description="Filter by company"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get stock summary by branch.
    Shows count and value of bikes at each branch.

    Query Parameters:
    - company_id: Filter by company
    """
    async with SessionLocal() as db:
        query = select(
            Bicycle.current_branch_id,
            Bicycle.company_id,
            Bicycle.status,
            func.count(Bicycle.id).label("bike_count"),
            func.sum(Bicycle.base_purchase_price).label("total_value")
        ).where(
            Bicycle.business_model.in_(["DIRECT_SALE", "STOCK"])
        ).group_by(
            Bicycle.current_branch_id,
            Bicycle.company_id,
            Bicycle.status
        )

        if company_id:
            query = query.where(Bicycle.company_id == company_id)

        result = await db.execute(query)
        rows = result.all()

        # Build response
        items = []
        total_bikes = 0
        total_value = 0

        for row in rows:
            branch_id = row[0]
            company = row[1]
            bike_status = row[2]
            count = row[3]
            value = float(row[4] or 0)

            total_bikes += count
            total_value += value

            items.append(BranchStockItem(
                branch_id=branch_id or "Unknown",
                branch_name=branch_id or "Unknown",  # Can join with offices table for name
                company_id=company,
                status=bike_status,
                bike_count=count,
                total_value=value
            ))

        return BranchStockResponse(
            items=items,
            total_bikes=total_bikes,
            total_value=total_value
        )
