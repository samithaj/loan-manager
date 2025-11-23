"""Customer Guarantor API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ..db import get_db
from ..rbac import require_permission
from ..services.customer_kyc_service import CustomerKYCService
from ..schemas.customer_kyc_schemas import (
    CustomerGuarantorCreate,
    CustomerGuarantorUpdate,
    CustomerGuarantorVerify,
    CustomerGuarantorResponse,
    CustomerGuarantorListResponse,
)

router = APIRouter(prefix="/v1", tags=["Customer KYC - Guarantors"])


@router.get(
    "/customers/{customer_id}/guarantors",
    response_model=CustomerGuarantorListResponse,
    dependencies=[Depends(require_permission("view:customer_guarantors"))]
)
async def list_customer_guarantors(
    customer_id: str,
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """List all guarantors for a customer"""
    skip = (page - 1) * page_size
    guarantors, total = await CustomerKYCService.list_guarantors(
        db, customer_id, skip=skip, limit=page_size
    )

    return {
        "items": [CustomerGuarantorResponse.model_validate(g) for g in guarantors],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post(
    "/customers/{customer_id}/guarantors",
    response_model=CustomerGuarantorResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("create:customer_guarantors"))]
)
async def create_customer_guarantor(
    customer_id: str,
    guarantor: CustomerGuarantorCreate,
    current_user: dict = Depends(require_permission("create:customer_guarantors")),
    db: AsyncSession = Depends(get_db)
):
    """Create a new guarantor for a customer"""
    # Ensure customer_id matches
    if guarantor.customer_id != customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer ID mismatch"
        )

    created_guarantor = await CustomerKYCService.create_guarantor(
        db, guarantor, created_by=current_user["username"]
    )

    return CustomerGuarantorResponse.model_validate(created_guarantor)


@router.get(
    "/guarantors/{guarantor_id}",
    response_model=CustomerGuarantorResponse,
    dependencies=[Depends(require_permission("view:customer_guarantors"))]
)
async def get_guarantor(
    guarantor_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific guarantor by ID"""
    guarantor = await CustomerKYCService.get_guarantor(db, guarantor_id)
    if not guarantor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Guarantor not found"
        )

    return CustomerGuarantorResponse.model_validate(guarantor)


@router.put(
    "/guarantors/{guarantor_id}",
    response_model=CustomerGuarantorResponse,
    dependencies=[Depends(require_permission("edit:customer_guarantors"))]
)
async def update_guarantor(
    guarantor_id: str,
    guarantor_data: CustomerGuarantorUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a guarantor"""
    guarantor = await CustomerKYCService.update_guarantor(db, guarantor_id, guarantor_data)
    if not guarantor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Guarantor not found"
        )

    return CustomerGuarantorResponse.model_validate(guarantor)


@router.delete(
    "/guarantors/{guarantor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("delete:customer_guarantors"))]
)
async def delete_guarantor(
    guarantor_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a guarantor"""
    success = await CustomerKYCService.delete_guarantor(db, guarantor_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Guarantor not found"
        )

    return None


@router.post(
    "/guarantors/{guarantor_id}/verify",
    response_model=CustomerGuarantorResponse,
    dependencies=[Depends(require_permission("verify:customer_guarantors"))]
)
async def verify_guarantor(
    guarantor_id: str,
    verify_data: CustomerGuarantorVerify,
    current_user: dict = Depends(require_permission("verify:customer_guarantors")),
    db: AsyncSession = Depends(get_db)
):
    """Verify a guarantor"""
    guarantor = await CustomerKYCService.verify_guarantor(
        db, guarantor_id, verified_by=current_user["username"]
    )
    if not guarantor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Guarantor not found"
        )

    return CustomerGuarantorResponse.model_validate(guarantor)
