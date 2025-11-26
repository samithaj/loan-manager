"""Vendor/Supplier Management API Router"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Depends, status
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from decimal import Decimal

from ..db import get_db
from ..services.vendor_service import VendorService
from ..models.vendor import Vendor, VendorCategory, VendorContact
from ..rbac import require_permission, get_current_user


router = APIRouter(prefix="/v1/vendors", tags=["vendors"])


# ============================================================================
# Pydantic Schemas
# ============================================================================

class VendorCreateIn(BaseModel):
    """Create vendor request"""
    company_id: str
    name: str = Field(..., min_length=2, max_length=200)
    vendor_code: Optional[str] = Field(None, max_length=50)

    # Contact
    contact_person: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None

    # Address
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    province: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)

    # Business
    tax_id: Optional[str] = Field(None, max_length=50)
    payment_terms: Optional[str] = Field(None, max_length=100)
    credit_limit: Optional[Decimal] = Field(0, ge=0)

    category_id: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=2000)


class VendorUpdateIn(BaseModel):
    """Update vendor request"""
    name: Optional[str] = Field(None, min_length=2, max_length=200)

    # Contact
    contact_person: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None

    # Address
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    province: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)

    # Business
    tax_id: Optional[str] = Field(None, max_length=50)
    business_registration_no: Optional[str] = Field(None, max_length=100)
    payment_terms: Optional[str] = Field(None, max_length=100)
    credit_limit: Optional[Decimal] = Field(None, ge=0)

    # Banking
    bank_name: Optional[str] = Field(None, max_length=200)
    bank_account_no: Optional[str] = Field(None, max_length=50)
    bank_branch: Optional[str] = Field(None, max_length=200)

    is_active: Optional[bool] = None
    category_id: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=2000)


class VendorOut(BaseModel):
    """Vendor response"""
    id: str
    company_id: str
    vendor_code: str
    name: str
    contact_person: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    address: Optional[str]
    city: Optional[str]
    province: Optional[str]
    postal_code: Optional[str]
    country: str
    tax_id: Optional[str]
    business_registration_no: Optional[str]
    payment_terms: Optional[str]
    credit_limit: float
    currency: str
    bank_name: Optional[str]
    bank_account_no: Optional[str]
    bank_branch: Optional[str]
    is_active: bool
    total_purchases: float
    total_orders: int
    last_purchase_date: Optional[str]
    category_id: Optional[str]
    notes: Optional[str]
    created_by: Optional[str]
    created_at: str
    updated_at: str


class VendorListResponse(BaseModel):
    """Paginated vendor list"""
    items: List[VendorOut]
    total: int
    offset: int
    limit: int


class VendorContactCreateIn(BaseModel):
    """Create vendor contact"""
    name: str = Field(..., min_length=2, max_length=200)
    position: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    mobile: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    is_primary: bool = False
    notes: Optional[str] = Field(None, max_length=500)


class VendorContactOut(BaseModel):
    """Vendor contact response"""
    id: str
    vendor_id: str
    name: str
    position: Optional[str]
    phone: Optional[str]
    mobile: Optional[str]
    email: Optional[str]
    is_primary: bool
    notes: Optional[str]
    created_at: str
    updated_at: str


class VendorCategoryOut(BaseModel):
    """Vendor category response"""
    id: str
    name: str
    description: Optional[str]
    created_at: str


# ============================================================================
# Helper Functions
# ============================================================================

async def get_db_session():
    """Get database session"""
    async with get_db() as session:
        yield session


# ============================================================================
# Vendor CRUD Endpoints
# ============================================================================

@router.post("", response_model=VendorOut, status_code=status.HTTP_201_CREATED)
async def create_vendor(
    data: VendorCreateIn,
    current_user: dict = Depends(require_permission("vendors:write")),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Create a new vendor

    Permissions: vendors:write
    """
    service = VendorService(db)

    try:
        vendor = await service.create_vendor(
            company_id=data.company_id,
            name=data.name,
            vendor_code=data.vendor_code,
            contact_person=data.contact_person,
            phone=data.phone,
            email=data.email,
            address=data.address,
            city=data.city,
            province=data.province,
            postal_code=data.postal_code,
            tax_id=data.tax_id,
            payment_terms=data.payment_terms,
            credit_limit=float(data.credit_limit) if data.credit_limit else 0,
            category_id=data.category_id,
            notes=data.notes,
            created_by=current_user.get("username", "unknown")
        )

        await db.commit()
        await db.refresh(vendor)

        return VendorOut(**vendor.to_dict())

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=VendorListResponse)
async def list_vendors(
    company_id: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    category_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None, description="Search by name, code, or contact person"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(require_permission("vendors:read")),
    db: AsyncSession = Depends(get_db_session)
):
    """
    List vendors with filters

    Permissions: vendors:read
    """
    service = VendorService(db)

    vendors, total = await service.list_vendors(
        company_id=company_id,
        is_active=is_active,
        category_id=category_id,
        search=search,
        offset=offset,
        limit=limit
    )

    items = [VendorOut(**v.to_dict()) for v in vendors]

    return VendorListResponse(
        items=items,
        total=total,
        offset=offset,
        limit=limit
    )


@router.get("/{vendor_id}", response_model=VendorOut)
async def get_vendor(
    vendor_id: str,
    current_user: dict = Depends(require_permission("vendors:read")),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get vendor by ID

    Permissions: vendors:read
    """
    service = VendorService(db)
    vendor = await service.get_vendor(vendor_id)

    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vendor {vendor_id} not found"
        )

    return VendorOut(**vendor.to_dict())


@router.put("/{vendor_id}", response_model=VendorOut)
async def update_vendor(
    vendor_id: str,
    data: VendorUpdateIn,
    current_user: dict = Depends(require_permission("vendors:write")),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Update vendor

    Permissions: vendors:write
    """
    service = VendorService(db)

    try:
        # Convert data to dict and remove None values
        updates = {k: v for k, v in data.model_dump().items() if v is not None}

        vendor = await service.update_vendor(vendor_id, **updates)

        await db.commit()
        await db.refresh(vendor)

        return VendorOut(**vendor.to_dict())

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/{vendor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vendor(
    vendor_id: str,
    current_user: dict = Depends(require_permission("vendors:delete")),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Delete vendor (soft delete)

    Permissions: vendors:delete
    """
    service = VendorService(db)

    success = await service.delete_vendor(vendor_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vendor {vendor_id} not found"
        )

    await db.commit()


# ============================================================================
# Vendor Contacts Endpoints
# ============================================================================

@router.post("/{vendor_id}/contacts", response_model=VendorContactOut, status_code=status.HTTP_201_CREATED)
async def add_vendor_contact(
    vendor_id: str,
    data: VendorContactCreateIn,
    current_user: dict = Depends(require_permission("vendors:write")),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Add contact person to vendor

    Permissions: vendors:write
    """
    service = VendorService(db)

    try:
        contact = await service.add_vendor_contact(
            vendor_id=vendor_id,
            name=data.name,
            position=data.position,
            phone=data.phone,
            mobile=data.mobile,
            email=data.email,
            is_primary=data.is_primary,
            notes=data.notes
        )

        await db.commit()
        await db.refresh(contact)

        return VendorContactOut(**contact.to_dict())

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/{vendor_id}/contacts", response_model=List[VendorContactOut])
async def list_vendor_contacts(
    vendor_id: str,
    current_user: dict = Depends(require_permission("vendors:read")),
    db: AsyncSession = Depends(get_db_session)
):
    """
    List vendor contacts

    Permissions: vendors:read
    """
    service = VendorService(db)
    contacts = await service.list_vendor_contacts(vendor_id)

    return [VendorContactOut(**c.to_dict()) for c in contacts]


# ============================================================================
# Categories Endpoints
# ============================================================================

@router.get("/categories/all", response_model=List[VendorCategoryOut])
async def list_vendor_categories(
    current_user: dict = Depends(require_permission("vendors:read")),
    db: AsyncSession = Depends(get_db_session)
):
    """
    List all vendor categories

    Permissions: vendors:read
    """
    from sqlalchemy import select

    stmt = select(VendorCategory).order_by(VendorCategory.name)
    result = await db.execute(stmt)
    categories = result.scalars().all()

    return [VendorCategoryOut(**c.to_dict()) for c in categories]
