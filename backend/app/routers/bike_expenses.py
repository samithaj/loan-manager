"""
Bike Expenses Router

API endpoints for managing bicycle branch-level expenses:
- Record expenses (transport, repair, insurance, etc.)
- View expense history
- Update/delete expenses
"""

from fastapi import APIRouter, HTTPException, Query, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import date
import secrets

from ..db import SessionLocal
from ..models import BicycleBranchExpense, Bicycle
from ..services.bike_lifecycle_service import BikeLifecycleService
from ..rbac import require_permission, get_current_user, require_branch_access


router = APIRouter(prefix="/v1", tags=["bike-expenses"])


# ============================================================================
# Pydantic Models
# ============================================================================

class ExpenseCreateRequest(BaseModel):
    """Create expense request"""
    branch_id: str = Field(..., description="Branch where expense occurred")
    expense_date: date = Field(..., description="Expense date")
    description: str = Field(..., min_length=5, max_length=500)
    category: str = Field(
        ...,
        pattern="^(TRANSPORT|MINOR_REPAIR|LICENSE_RENEWAL|INSURANCE|CLEANING|DOCUMENTATION|STORAGE|OTHER)$"
    )
    amount: float = Field(..., gt=0, description="Expense amount")
    invoice_number: Optional[str] = Field(None, max_length=100)
    vendor_name: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = Field(None, max_length=1000)


class ExpenseUpdateRequest(BaseModel):
    """Update expense request"""
    expense_date: Optional[date] = None
    description: Optional[str] = Field(None, min_length=5, max_length=500)
    category: Optional[str] = Field(
        None,
        pattern="^(TRANSPORT|MINOR_REPAIR|LICENSE_RENEWAL|INSURANCE|CLEANING|DOCUMENTATION|STORAGE|OTHER)$"
    )
    amount: Optional[float] = Field(None, gt=0)
    invoice_number: Optional[str] = Field(None, max_length=100)
    vendor_name: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = Field(None, max_length=1000)


class ExpenseOut(BaseModel):
    """Expense output"""
    id: str
    bicycle_id: str
    branch_id: str
    expense_date: str
    description: str
    category: str
    amount: float
    invoice_number: Optional[str]
    vendor_name: Optional[str]
    recorded_by: str
    notes: Optional[str]


class ExpenseListResponse(BaseModel):
    """Paginated expense list"""
    items: list[ExpenseOut]
    total: int
    total_amount: float


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/bikes/{bike_id}/expenses", response_model=ExpenseOut, status_code=status.HTTP_201_CREATED)
async def create_expense(
    bike_id: str,
    data: ExpenseCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Record a branch-level expense for a bike.

    Requires permission: bikes:expenses:write
    Requires access to branch
    """
    require_permission(current_user, "bikes:expenses:write")
    require_branch_access(current_user, data.branch_id)

    async with SessionLocal() as db:
        # Verify bike exists
        result = await db.execute(select(Bicycle).where(Bicycle.id == bike_id))
        bike = result.scalar_one_or_none()

        if not bike:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bike '{bike_id}' not found"
            )

        # Get user identifier
        user_id = current_user.get("id") or current_user.get("sub") or "unknown"

        # Create expense
        expense_id = f"EXP-{bike_id[:8]}-{secrets.token_hex(3).upper()}"
        expense = BicycleBranchExpense(
            id=expense_id,
            bicycle_id=bike_id,
            branch_id=data.branch_id,
            expense_date=data.expense_date,
            description=data.description,
            category=data.category,
            amount=data.amount,
            invoice_number=data.invoice_number,
            vendor_name=data.vendor_name,
            recorded_by=str(user_id),
            notes=data.notes
        )

        db.add(expense)
        await db.commit()
        await db.refresh(expense)

        # Update bike's total_branch_expenses
        await BikeLifecycleService.update_branch_expenses(db, bike_id)
        await db.commit()

        return ExpenseOut(**expense.to_dict())


@router.get("/bikes/{bike_id}/expenses", response_model=ExpenseListResponse)
async def list_bike_expenses(
    bike_id: str,
    category: Optional[str] = Query(None, description="Filter by category"),
    branch_id: Optional[str] = Query(None, description="Filter by branch"),
    start_date: Optional[date] = Query(None, description="Filter from date"),
    end_date: Optional[date] = Query(None, description="Filter to date"),
    current_user: dict = Depends(get_current_user),
):
    """
    List expenses for a specific bike with optional filters.

    Query Parameters:
    - category: Filter by expense category
    - branch_id: Filter by branch
    - start_date: Filter expenses from date
    - end_date: Filter expenses to date
    """
    async with SessionLocal() as db:
        # Verify bike exists
        result = await db.execute(select(Bicycle).where(Bicycle.id == bike_id))
        bike = result.scalar_one_or_none()

        if not bike:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bike '{bike_id}' not found"
            )

        # Build query
        query = select(BicycleBranchExpense).where(
            BicycleBranchExpense.bicycle_id == bike_id
        )

        # Apply filters
        if category:
            query = query.where(BicycleBranchExpense.category == category)

        if branch_id:
            query = query.where(BicycleBranchExpense.branch_id == branch_id)

        if start_date:
            query = query.where(BicycleBranchExpense.expense_date >= start_date)

        if end_date:
            query = query.where(BicycleBranchExpense.expense_date <= end_date)

        # Order by date desc
        query = query.order_by(BicycleBranchExpense.expense_date.desc())

        result = await db.execute(query)
        expenses = list(result.scalars().all())

        # Calculate total
        total_amount = sum(float(e.amount) for e in expenses)

        return {
            "items": [ExpenseOut(**e.to_dict()) for e in expenses],
            "total": len(expenses),
            "total_amount": total_amount,
        }


@router.get("/expenses/{expense_id}", response_model=ExpenseOut)
async def get_expense(
    expense_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get expense details by ID."""
    async with SessionLocal() as db:
        result = await db.execute(
            select(BicycleBranchExpense).where(BicycleBranchExpense.id == expense_id)
        )
        expense = result.scalar_one_or_none()

        if not expense:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Expense '{expense_id}' not found"
            )

        return ExpenseOut(**expense.to_dict())


@router.put("/expenses/{expense_id}", response_model=ExpenseOut)
async def update_expense(
    expense_id: str,
    data: ExpenseUpdateRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Update an expense record.

    Requires permission: bikes:expenses:write
    """
    require_permission(current_user, "bikes:expenses:write")

    async with SessionLocal() as db:
        result = await db.execute(
            select(BicycleBranchExpense).where(BicycleBranchExpense.id == expense_id)
        )
        expense = result.scalar_one_or_none()

        if not expense:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Expense '{expense_id}' not found"
            )

        # Check branch access
        require_branch_access(current_user, expense.branch_id)

        # Update only provided fields
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(expense, key, value)

        await db.commit()
        await db.refresh(expense)

        # Update bike's total_branch_expenses if amount changed
        if "amount" in update_data:
            await BikeLifecycleService.update_branch_expenses(db, expense.bicycle_id)
            await db.commit()

        return ExpenseOut(**expense.to_dict())


@router.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    expense_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Delete an expense record.

    Requires permission: bikes:expenses:delete
    """
    require_permission(current_user, "bikes:expenses:delete")

    async with SessionLocal() as db:
        result = await db.execute(
            select(BicycleBranchExpense).where(BicycleBranchExpense.id == expense_id)
        )
        expense = result.scalar_one_or_none()

        if not expense:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Expense '{expense_id}' not found"
            )

        # Check branch access
        require_branch_access(current_user, expense.branch_id)

        bicycle_id = expense.bicycle_id

        await db.delete(expense)
        await db.commit()

        # Update bike's total_branch_expenses
        await BikeLifecycleService.update_branch_expenses(db, bicycle_id)
        await db.commit()


@router.get("/expenses", response_model=ExpenseListResponse)
async def list_all_expenses(
    bicycle_id: Optional[str] = Query(None, description="Filter by bicycle"),
    branch_id: Optional[str] = Query(None, description="Filter by branch"),
    category: Optional[str] = Query(None, description="Filter by category"),
    start_date: Optional[date] = Query(None, description="Filter from date"),
    end_date: Optional[date] = Query(None, description="Filter to date"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
):
    """
    List all expenses with filters and pagination.

    Query Parameters:
    - bicycle_id: Filter by bicycle
    - branch_id: Filter by branch
    - category: Filter by expense category
    - start_date: Filter expenses from date
    - end_date: Filter expenses to date
    - offset: Pagination offset
    - limit: Items per page (max 200)
    """
    async with SessionLocal() as db:
        query = select(BicycleBranchExpense)

        # Apply filters
        if bicycle_id:
            query = query.where(BicycleBranchExpense.bicycle_id == bicycle_id)

        if branch_id:
            query = query.where(BicycleBranchExpense.branch_id == branch_id)

        if category:
            query = query.where(BicycleBranchExpense.category == category)

        if start_date:
            query = query.where(BicycleBranchExpense.expense_date >= start_date)

        if end_date:
            query = query.where(BicycleBranchExpense.expense_date <= end_date)

        # Order by date desc
        query = query.order_by(BicycleBranchExpense.expense_date.desc())

        # Apply pagination
        query_paginated = query.offset(offset).limit(limit)

        result = await db.execute(query_paginated)
        expenses = list(result.scalars().all())

        # Calculate total amount (for all matching, not just current page)
        result_all = await db.execute(query)
        all_expenses = list(result_all.scalars().all())
        total_amount = sum(float(e.amount) for e in all_expenses)

        return {
            "items": [ExpenseOut(**e.to_dict()) for e in expenses],
            "total": len(all_expenses),
            "total_amount": total_amount,
        }
