from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Any
from ..db import SessionLocal
from ..models.bicycle import Bicycle, BicycleStatus, BicycleCondition
from ..models.reference import Office


router = APIRouter(prefix="/public", tags=["public"])


class BicyclePublicOut(BaseModel):
    """Public-facing bicycle information"""
    id: str
    title: str
    brand: str
    model: str
    year: int
    condition: str
    license_plate: str | None = None
    mileage_km: int | None = None
    description: str | None = None
    branch_id: str
    branch_name: str | None = None
    cash_price: float
    hire_purchase_price: float
    image_urls: list[str] = []
    thumbnail_url: str | None = None
    monthly_payment_estimate: float


class BicycleListResponse(BaseModel):
    """Paginated bicycle list response"""
    items: list[BicyclePublicOut]
    total: int
    offset: int
    limit: int


class BranchPublicOut(BaseModel):
    """Public-facing branch information"""
    id: str
    name: str
    operating_hours: str | None = None
    public_description: str | None = None
    map_coordinates: dict[str, Any] | None = None
    bicycle_display_order: int


@router.get("/bicycles", response_model=BicycleListResponse)
async def list_public_bicycles(
    condition: Optional[str] = Query(None, description="Filter by condition: NEW or USED"),
    branch_id: Optional[str] = Query(None, description="Filter by branch ID"),
    min_price: Optional[float] = Query(None, description="Minimum cash price"),
    max_price: Optional[float] = Query(None, description="Maximum cash price"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    search: Optional[str] = Query(None, description="Search in title, brand, model"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Items per page")
):
    """
    Get list of available bicycles for public viewing.
    Only shows bicycles with AVAILABLE status.
    """
    async with SessionLocal() as session:  # type: AsyncSession
        # Build base query - only show AVAILABLE bicycles
        stmt = select(Bicycle).where(Bicycle.status == BicycleStatus.AVAILABLE.value)

        # Apply filters
        filters = []

        if condition:
            filters.append(Bicycle.condition == condition.upper())

        if branch_id:
            filters.append(Bicycle.branch_id == branch_id)

        if min_price is not None:
            filters.append(Bicycle.cash_price >= min_price)

        if max_price is not None:
            filters.append(Bicycle.cash_price <= max_price)

        if brand:
            filters.append(Bicycle.brand.ilike(f"%{brand}%"))

        if search:
            search_pattern = f"%{search}%"
            filters.append(
                or_(
                    Bicycle.title.ilike(search_pattern),
                    Bicycle.brand.ilike(search_pattern),
                    Bicycle.model.ilike(search_pattern),
                )
            )

        if filters:
            stmt = stmt.where(and_(*filters))

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await session.scalar(count_stmt) or 0

        # Apply pagination and ordering
        stmt = stmt.order_by(Bicycle.created_at.desc()).offset(offset).limit(limit)

        # Execute query
        result = await session.execute(stmt)
        bicycles = result.scalars().all()

        # Fetch branch names for each bicycle
        branch_ids = list(set(b.branch_id for b in bicycles))
        branch_stmt = select(Office).where(Office.id.in_(branch_ids))
        branch_result = await session.execute(branch_stmt)
        branches = {b.id: b.name for b in branch_result.scalars().all()}

        # Convert to response format
        items = [
            BicyclePublicOut(
                id=b.id,
                title=b.title,
                brand=b.brand,
                model=b.model,
                year=b.year,
                condition=b.condition,
                license_plate=b.license_plate,
                mileage_km=b.mileage_km,
                description=b.description,
                branch_id=b.branch_id,
                branch_name=branches.get(b.branch_id),
                cash_price=float(b.cash_price),
                hire_purchase_price=float(b.hire_purchase_price),
                image_urls=b.image_urls or [],
                thumbnail_url=b.thumbnail_url,
                monthly_payment_estimate=b.calculate_monthly_payment(),
            )
            for b in bicycles
        ]

        return BicycleListResponse(
            items=items,
            total=total,
            offset=offset,
            limit=limit,
        )


@router.get("/bicycles/{bicycle_id}", response_model=BicyclePublicOut)
async def get_public_bicycle(bicycle_id: str):
    """
    Get detailed information about a specific bicycle.
    Only shows bicycles with AVAILABLE status.
    """
    async with SessionLocal() as session:  # type: AsyncSession
        bicycle = await session.get(Bicycle, bicycle_id)

        if not bicycle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "BICYCLE_NOT_FOUND", "message": "Bicycle not found"}
            )

        # Only show available bicycles to public
        if bicycle.status != BicycleStatus.AVAILABLE.value:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "BICYCLE_NOT_AVAILABLE", "message": "Bicycle is not available"}
            )

        # Fetch branch name
        branch = await session.get(Office, bicycle.branch_id)
        branch_name = branch.name if branch else None

        return BicyclePublicOut(
            id=bicycle.id,
            title=bicycle.title,
            brand=bicycle.brand,
            model=bicycle.model,
            year=bicycle.year,
            condition=bicycle.condition,
            license_plate=bicycle.license_plate,
            mileage_km=bicycle.mileage_km,
            description=bicycle.description,
            branch_id=bicycle.branch_id,
            branch_name=branch_name,
            cash_price=float(bicycle.cash_price),
            hire_purchase_price=float(bicycle.hire_purchase_price),
            image_urls=bicycle.image_urls or [],
            thumbnail_url=bicycle.thumbnail_url,
            monthly_payment_estimate=bicycle.calculate_monthly_payment(),
        )


@router.get("/branches", response_model=list[BranchPublicOut])
async def list_public_branches():
    """
    Get list of branches that allow bicycle sales.
    Ordered by display_order for consistent public display.
    """
    async with SessionLocal() as session:  # type: AsyncSession
        stmt = (
            select(Office)
            .where(Office.allows_bicycle_sales == True)
            .order_by(Office.bicycle_display_order, Office.name)
        )

        result = await session.execute(stmt)
        branches = result.scalars().all()

        return [
            BranchPublicOut(
                id=b.id,
                name=b.name,
                operating_hours=b.operating_hours,
                public_description=b.public_description,
                map_coordinates=b.map_coordinates,
                bicycle_display_order=b.bicycle_display_order,
            )
            for b in branches
        ]


@router.get("/branches/{branch_id}", response_model=BranchPublicOut)
async def get_public_branch(branch_id: str):
    """
    Get detailed information about a specific branch.
    Only shows branches that allow bicycle sales.
    """
    async with SessionLocal() as session:  # type: AsyncSession
        branch = await session.get(Office, branch_id)

        if not branch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "BRANCH_NOT_FOUND", "message": "Branch not found"}
            )

        if not branch.allows_bicycle_sales:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "BRANCH_NOT_AVAILABLE", "message": "Branch does not offer bicycle sales"}
            )

        return BranchPublicOut(
            id=branch.id,
            name=branch.name,
            operating_hours=branch.operating_hours,
            public_description=branch.public_description,
            map_coordinates=branch.map_coordinates,
            bicycle_display_order=branch.bicycle_display_order,
        )
