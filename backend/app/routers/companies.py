"""
Companies Router

API endpoints for managing companies (MA/IN).
Handles company CRUD operations.
"""

from fastapi import APIRouter, HTTPException, Query, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ..db import SessionLocal
from ..models import Company
from ..rbac import require_permission, get_current_user


router = APIRouter(prefix="/v1/companies", tags=["companies"])


# ============================================================================
# Pydantic Models
# ============================================================================

class CompanyCreate(BaseModel):
    """Create company request"""
    id: str = Field(..., min_length=2, max_length=10, pattern="^[A-Z]+$")
    name: str = Field(..., min_length=3, max_length=200)
    district: str = Field(..., min_length=2, max_length=100)
    contact_person: Optional[str] = Field(None, max_length=200)
    contact_phone: Optional[str] = Field(None, max_length=50)
    contact_email: Optional[str] = Field(None, max_length=200)
    address: Optional[dict] = None
    tax_id: Optional[str] = Field(None, max_length=50)


class CompanyUpdate(BaseModel):
    """Update company request"""
    name: Optional[str] = Field(None, min_length=3, max_length=200)
    district: Optional[str] = Field(None, min_length=2, max_length=100)
    contact_person: Optional[str] = Field(None, max_length=200)
    contact_phone: Optional[str] = Field(None, max_length=50)
    contact_email: Optional[str] = Field(None, max_length=200)
    address: Optional[dict] = None
    tax_id: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None


class CompanyOut(BaseModel):
    """Company output"""
    id: str
    name: str
    district: str
    contact_person: Optional[str]
    contact_phone: Optional[str]
    contact_email: Optional[str]
    address: Optional[dict]
    tax_id: Optional[str]
    is_active: bool
    created_at: str
    updated_at: str


class CompanyListResponse(BaseModel):
    """Paginated company list"""
    items: list[CompanyOut]
    total: int


# ============================================================================
# Endpoints
# ============================================================================

@router.get("", response_model=CompanyListResponse)
async def list_companies(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: dict = Depends(get_current_user),
):
    """
    List all companies.

    Query Parameters:
    - is_active: Filter by active status (true/false)
    """
    async with SessionLocal() as db:
        query = select(Company)

        if is_active is not None:
            query = query.where(Company.is_active == is_active)

        query = query.order_by(Company.name)

        result = await db.execute(query)
        companies = list(result.scalars().all())

        return {
            "items": [CompanyOut(**c.to_dict()) for c in companies],
            "total": len(companies),
        }


@router.post("", response_model=CompanyOut, status_code=status.HTTP_201_CREATED)
async def create_company(
    data: CompanyCreate,
    current_user: dict = Depends(get_current_user),
):
    """
    Create new company (admin only).

    Requires permission: companies:write
    """
    require_permission(current_user, "companies:write")

    async with SessionLocal() as db:
        # Check if company ID already exists
        result = await db.execute(select(Company).where(Company.id == data.id))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Company with ID '{data.id}' already exists"
            )

        company = Company(**data.model_dump())
        db.add(company)
        await db.commit()
        await db.refresh(company)

        return CompanyOut(**company.to_dict())


@router.get("/{company_id}", response_model=CompanyOut)
async def get_company(
    company_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get company details by ID."""
    async with SessionLocal() as db:
        result = await db.execute(select(Company).where(Company.id == company_id))
        company = result.scalar_one_or_none()

        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company '{company_id}' not found"
            )

        return CompanyOut(**company.to_dict())


@router.put("/{company_id}", response_model=CompanyOut)
async def update_company(
    company_id: str,
    data: CompanyUpdate,
    current_user: dict = Depends(get_current_user),
):
    """
    Update company (admin only).

    Requires permission: companies:write
    """
    require_permission(current_user, "companies:write")

    async with SessionLocal() as db:
        result = await db.execute(select(Company).where(Company.id == company_id))
        company = result.scalar_one_or_none()

        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company '{company_id}' not found"
            )

        # Update only provided fields
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(company, key, value)

        await db.commit()
        await db.refresh(company)

        return CompanyOut(**company.to_dict())


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
    company_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Deactivate company (admin only).

    Requires permission: companies:write
    Note: This soft-deletes by setting is_active=False
    """
    require_permission(current_user, "companies:write")

    async with SessionLocal() as db:
        result = await db.execute(select(Company).where(Company.id == company_id))
        company = result.scalar_one_or_none()

        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company '{company_id}' not found"
            )

        company.is_active = False
        await db.commit()
