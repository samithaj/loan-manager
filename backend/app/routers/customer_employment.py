"""Customer Employment API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..rbac import require_permission
from ..services.customer_kyc_service import CustomerKYCService
from ..schemas.customer_kyc_schemas import (
    CustomerEmploymentCreate,
    CustomerEmploymentUpdate,
    CustomerEmploymentVerify,
    CustomerEmploymentResponse,
    CustomerEmploymentListResponse,
)

router = APIRouter(prefix="/v1", tags=["Customer KYC - Employment"])


@router.get(
    "/customers/{customer_id}/employment",
    response_model=CustomerEmploymentListResponse,
    dependencies=[Depends(require_permission("view:customer_employment"))]
)
async def list_customer_employment(
    customer_id: str,
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """List all employment records for a customer"""
    skip = (page - 1) * page_size
    employment, total = await CustomerKYCService.list_employment(
        db, customer_id, skip=skip, limit=page_size
    )

    return {
        "items": [CustomerEmploymentResponse.model_validate(e) for e in employment],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post(
    "/customers/{customer_id}/employment",
    response_model=CustomerEmploymentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("create:customer_employment"))]
)
async def create_customer_employment(
    customer_id: str,
    employment: CustomerEmploymentCreate,
    current_user: dict = Depends(require_permission("create:customer_employment")),
    db: AsyncSession = Depends(get_db)
):
    """Create a new employment record for a customer"""
    # Ensure customer_id matches
    if employment.customer_id != customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer ID mismatch"
        )

    created_employment = await CustomerKYCService.create_employment(
        db, employment, created_by=current_user["username"]
    )

    return CustomerEmploymentResponse.model_validate(created_employment)


@router.get(
    "/employment/{employment_id}",
    response_model=CustomerEmploymentResponse,
    dependencies=[Depends(require_permission("view:customer_employment"))]
)
async def get_employment(
    employment_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific employment record by ID"""
    employment = await CustomerKYCService.get_employment(db, employment_id)
    if not employment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employment record not found"
        )

    return CustomerEmploymentResponse.model_validate(employment)


@router.put(
    "/employment/{employment_id}",
    response_model=CustomerEmploymentResponse,
    dependencies=[Depends(require_permission("edit:customer_employment"))]
)
async def update_employment(
    employment_id: str,
    employment_data: CustomerEmploymentUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an employment record"""
    employment = await CustomerKYCService.update_employment(db, employment_id, employment_data)
    if not employment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employment record not found"
        )

    return CustomerEmploymentResponse.model_validate(employment)


@router.delete(
    "/employment/{employment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("delete:customer_employment"))]
)
async def delete_employment(
    employment_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete an employment record"""
    success = await CustomerKYCService.delete_employment(db, employment_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employment record not found"
        )

    return None


@router.post(
    "/employment/{employment_id}/verify",
    response_model=CustomerEmploymentResponse,
    dependencies=[Depends(require_permission("verify:customer_employment"))]
)
async def verify_employment(
    employment_id: str,
    verify_data: CustomerEmploymentVerify,
    current_user: dict = Depends(require_permission("verify:customer_employment")),
    db: AsyncSession = Depends(get_db)
):
    """Verify an employment record"""
    employment = await CustomerKYCService.verify_employment(
        db, employment_id, verified_by=current_user["username"],
        verification_method=verify_data.verification_method
    )
    if not employment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employment record not found"
        )

    return CustomerEmploymentResponse.model_validate(employment)
