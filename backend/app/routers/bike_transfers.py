"""
Bike Transfers Router

API endpoints for managing bicycle transfers between branches:
- Initiate transfer requests
- Approve/reject transfers
- Complete transfers
- View transfer history
"""

from fastapi import APIRouter, HTTPException, Query, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ..db import SessionLocal
from ..models import BicycleTransfer
from ..services.transfer_service import TransferService
from ..rbac import require_permission, get_current_user, require_branch_access


router = APIRouter(prefix="/v1", tags=["bike-transfers"])


# ============================================================================
# Pydantic Models
# ============================================================================

class TransferInitiateRequest(BaseModel):
    """Initiate transfer request"""
    to_branch_id: str = Field(..., description="Destination branch ID")
    transfer_reason: Optional[str] = Field(None, max_length=500)
    reference_doc_number: Optional[str] = Field(None, max_length=50)


class TransferApproveRequest(BaseModel):
    """Approve transfer request"""
    pass  # No additional data needed


class TransferRejectRequest(BaseModel):
    """Reject transfer request"""
    reason: str = Field(..., min_length=5, max_length=500, description="Rejection reason")


class TransferOut(BaseModel):
    """Transfer output"""
    id: str
    bicycle_id: str
    from_branch_id: str
    to_branch_id: str
    from_stock_number: Optional[str]
    to_stock_number: Optional[str]
    status: str

    # Request details
    requested_by: str
    requested_at: str

    # Approval details
    approved_by: Optional[str]
    approved_at: Optional[str]

    # Completion details
    completed_by: Optional[str]
    completed_at: Optional[str]

    # Rejection details
    rejected_by: Optional[str]
    rejected_at: Optional[str]
    rejection_reason: Optional[str]

    # Additional info
    transfer_reason: Optional[str]
    reference_doc_number: Optional[str]
    notes: Optional[str]


class TransferListResponse(BaseModel):
    """Paginated transfer list"""
    items: list[TransferOut]
    total: int


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/bikes/{bike_id}/transfers", response_model=TransferOut, status_code=status.HTTP_201_CREATED)
async def initiate_transfer(
    bike_id: str,
    data: TransferInitiateRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Initiate a transfer request for a bike.

    Requires permission: bikes:transfer
    Requires access to source branch
    """
    require_permission(current_user, "bikes:transfer")

    async with SessionLocal() as db:
        try:
            # Get user identifier
            user_id = current_user.get("id") or current_user.get("sub") or "unknown"

            transfer = await TransferService.initiate_transfer(
                db,
                bicycle_id=bike_id,
                to_branch_id=data.to_branch_id,
                requested_by=str(user_id),
                transfer_reason=data.transfer_reason,
                reference_doc_number=data.reference_doc_number
            )

            await db.commit()
            await db.refresh(transfer)

            return TransferOut(**transfer.to_dict())

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to initiate transfer: {str(e)}"
            )


@router.get("/transfers", response_model=TransferListResponse)
async def list_transfers(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    branch_id: Optional[str] = Query(None, description="Filter by branch (from or to)"),
    bicycle_id: Optional[str] = Query(None, description="Filter by bicycle"),
    current_user: dict = Depends(get_current_user),
):
    """
    List transfers with optional filters.

    Query Parameters:
    - status: Filter by status (PENDING, APPROVED, IN_TRANSIT, COMPLETED, REJECTED, CANCELLED)
    - branch_id: Filter by branch (from or to)
    - bicycle_id: Filter by bicycle ID
    """
    async with SessionLocal() as db:
        query = select(BicycleTransfer)

        # Apply filters
        if status_filter:
            query = query.where(BicycleTransfer.status == status_filter)

        if branch_id:
            query = query.where(
                or_(
                    BicycleTransfer.from_branch_id == branch_id,
                    BicycleTransfer.to_branch_id == branch_id
                )
            )

        if bicycle_id:
            query = query.where(BicycleTransfer.bicycle_id == bicycle_id)

        # Order by requested_at desc
        query = query.order_by(BicycleTransfer.requested_at.desc())

        result = await db.execute(query)
        transfers = list(result.scalars().all())

        return {
            "items": [TransferOut(**t.to_dict()) for t in transfers],
            "total": len(transfers),
        }


@router.get("/transfers/{transfer_id}", response_model=TransferOut)
async def get_transfer(
    transfer_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get transfer details by ID."""
    async with SessionLocal() as db:
        result = await db.execute(
            select(BicycleTransfer).where(BicycleTransfer.id == transfer_id)
        )
        transfer = result.scalar_one_or_none()

        if not transfer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transfer '{transfer_id}' not found"
            )

        return TransferOut(**transfer.to_dict())


@router.post("/transfers/{transfer_id}/approve", response_model=TransferOut)
async def approve_transfer(
    transfer_id: str,
    data: TransferApproveRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Approve a transfer request.
    This assigns a new stock number and moves status to IN_TRANSIT.

    Requires permission: bikes:transfer:approve
    """
    require_permission(current_user, "bikes:transfer:approve")

    async with SessionLocal() as db:
        try:
            # Get user identifier
            user_id = current_user.get("id") or current_user.get("sub") or "unknown"

            transfer = await TransferService.approve_transfer(
                db,
                transfer_id=transfer_id,
                approved_by=str(user_id)
            )

            await db.commit()
            await db.refresh(transfer)

            return TransferOut(**transfer.to_dict())

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to approve transfer: {str(e)}"
            )


@router.post("/transfers/{transfer_id}/complete", response_model=TransferOut)
async def complete_transfer(
    transfer_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Mark a transfer as completed.

    Requires permission: bikes:transfer
    """
    require_permission(current_user, "bikes:transfer")

    async with SessionLocal() as db:
        try:
            # Get user identifier
            user_id = current_user.get("id") or current_user.get("sub") or "unknown"

            transfer = await TransferService.complete_transfer(
                db,
                transfer_id=transfer_id,
                completed_by=str(user_id)
            )

            await db.commit()
            await db.refresh(transfer)

            return TransferOut(**transfer.to_dict())

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to complete transfer: {str(e)}"
            )


@router.post("/transfers/{transfer_id}/reject", response_model=TransferOut)
async def reject_transfer(
    transfer_id: str,
    data: TransferRejectRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Reject a transfer request.
    This reverts the stock number if transfer was already approved.

    Requires permission: bikes:transfer:approve
    """
    require_permission(current_user, "bikes:transfer:approve")

    async with SessionLocal() as db:
        try:
            # Get user identifier
            user_id = current_user.get("id") or current_user.get("sub") or "unknown"

            transfer = await TransferService.reject_transfer(
                db,
                transfer_id=transfer_id,
                rejected_by=str(user_id),
                reason=data.reason
            )

            await db.commit()
            await db.refresh(transfer)

            return TransferOut(**transfer.to_dict())

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to reject transfer: {str(e)}"
            )


@router.post("/transfers/{transfer_id}/cancel", response_model=TransferOut)
async def cancel_transfer(
    transfer_id: str,
    data: TransferRejectRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Cancel a pending transfer request.

    Requires permission: bikes:transfer
    """
    require_permission(current_user, "bikes:transfer")

    async with SessionLocal() as db:
        try:
            # Get user identifier
            user_id = current_user.get("id") or current_user.get("sub") or "unknown"

            transfer = await TransferService.cancel_transfer(
                db,
                transfer_id=transfer_id,
                cancelled_by=str(user_id),
                reason=data.reason
            )

            await db.commit()
            await db.refresh(transfer)

            return TransferOut(**transfer.to_dict())

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to cancel transfer: {str(e)}"
            )


@router.get("/bikes/{bike_id}/transfers", response_model=TransferListResponse)
async def get_bike_transfers(
    bike_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get transfer history for a specific bike."""
    async with SessionLocal() as db:
        history = await TransferService.get_transfer_history(db, bike_id)

        return {
            "items": [TransferOut(**t.to_dict()) for t in history],
            "total": len(history),
        }
