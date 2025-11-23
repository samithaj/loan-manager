"""Petty Cash API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from decimal import Decimal

from ..db import get_db
from ..rbac import require_permission
from ..services.petty_cash_service import PettyCashService
from ..schemas.petty_cash_schemas import (
    PettyCashFloatCreate,
    PettyCashFloatUpdate,
    PettyCashFloatResponse,
    PettyCashFloatListResponse,
    PettyCashFloatReconcile,
    PettyCashVoucherCreate,
    PettyCashVoucherUpdate,
    PettyCashVoucherResponse,
    PettyCashVoucherListResponse,
    PettyCashVoucherApprove,
    PettyCashVoucherReject,
    PettyCashVoucherPost,
)

router = APIRouter(prefix="/v1/petty-cash", tags=["Petty Cash"])


# ============= Petty Cash Float Endpoints =============

@router.get(
    "/floats",
    response_model=PettyCashFloatListResponse,
    dependencies=[Depends(require_permission("view:petty_cash"))]
)
async def list_petty_cash_floats(
    branch_id: str | None = None,
    custodian_id: str | None = None,
    is_active: bool | None = None,
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """List petty cash floats with optional filters"""
    skip = (page - 1) * page_size
    floats, total = await PettyCashService.list_floats(
        db,
        branch_id=branch_id,
        custodian_id=custodian_id,
        is_active=is_active,
        skip=skip,
        limit=page_size
    )

    return {
        "items": [PettyCashFloatResponse.model_validate(f) for f in floats],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post(
    "/floats",
    response_model=PettyCashFloatResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("create:petty_cash"))]
)
async def create_petty_cash_float(
    float_data: PettyCashFloatCreate,
    current_user: dict = Depends(require_permission("create:petty_cash")),
    db: AsyncSession = Depends(get_db)
):
    """Create a new petty cash float"""
    created_float = await PettyCashService.create_float(
        db, float_data, created_by=current_user["username"]
    )

    return PettyCashFloatResponse.model_validate(created_float)


@router.get(
    "/floats/{float_id}",
    response_model=PettyCashFloatResponse,
    dependencies=[Depends(require_permission("view:petty_cash"))]
)
async def get_petty_cash_float(
    float_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific petty cash float by ID"""
    float_obj = await PettyCashService.get_float(db, float_id)
    if not float_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Petty cash float not found"
        )

    return PettyCashFloatResponse.model_validate(float_obj)


@router.put(
    "/floats/{float_id}",
    response_model=PettyCashFloatResponse,
    dependencies=[Depends(require_permission("edit:petty_cash"))]
)
async def update_petty_cash_float(
    float_id: str,
    float_data: PettyCashFloatUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a petty cash float"""
    float_obj = await PettyCashService.update_float(db, float_id, float_data)
    if not float_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Petty cash float not found"
        )

    return PettyCashFloatResponse.model_validate(float_obj)


@router.post(
    "/floats/{float_id}/reconcile",
    response_model=PettyCashFloatResponse,
    dependencies=[Depends(require_permission("reconcile:petty_cash"))]
)
async def reconcile_petty_cash_float(
    float_id: str,
    reconcile_data: PettyCashFloatReconcile,
    current_user: dict = Depends(require_permission("reconcile:petty_cash")),
    db: AsyncSession = Depends(get_db)
):
    """Reconcile a petty cash float"""
    float_obj = await PettyCashService.reconcile_float(
        db,
        float_id,
        actual_balance=reconcile_data.actual_balance,
        reconciled_by=current_user["username"],
        reconciliation_notes=reconcile_data.reconciliation_notes
    )
    if not float_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Petty cash float not found"
        )

    return PettyCashFloatResponse.model_validate(float_obj)


# ============= Petty Cash Voucher Endpoints =============

@router.get(
    "/vouchers",
    response_model=PettyCashVoucherListResponse,
    dependencies=[Depends(require_permission("view:petty_cash"))]
)
async def list_petty_cash_vouchers(
    float_id: str | None = None,
    branch_id: str | None = None,
    voucher_type: str | None = None,
    status: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """List petty cash vouchers with optional filters"""
    skip = (page - 1) * page_size
    vouchers, total = await PettyCashService.list_vouchers(
        db,
        float_id=float_id,
        branch_id=branch_id,
        voucher_type=voucher_type,
        status=status,
        date_from=date_from,
        date_to=date_to,
        skip=skip,
        limit=page_size
    )

    return {
        "items": [PettyCashVoucherResponse.model_validate(v) for v in vouchers],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post(
    "/vouchers",
    response_model=PettyCashVoucherResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("create:petty_cash"))]
)
async def create_petty_cash_voucher(
    voucher_data: PettyCashVoucherCreate,
    current_user: dict = Depends(require_permission("create:petty_cash")),
    db: AsyncSession = Depends(get_db)
):
    """Create a new petty cash voucher"""
    try:
        created_voucher = await PettyCashService.create_voucher(
            db, voucher_data, created_by=current_user["username"]
        )
        return PettyCashVoucherResponse.model_validate(created_voucher)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/vouchers/{voucher_id}",
    response_model=PettyCashVoucherResponse,
    dependencies=[Depends(require_permission("view:petty_cash"))]
)
async def get_petty_cash_voucher(
    voucher_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific petty cash voucher by ID"""
    voucher = await PettyCashService.get_voucher(db, voucher_id)
    if not voucher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Petty cash voucher not found"
        )

    return PettyCashVoucherResponse.model_validate(voucher)


@router.put(
    "/vouchers/{voucher_id}",
    response_model=PettyCashVoucherResponse,
    dependencies=[Depends(require_permission("edit:petty_cash"))]
)
async def update_petty_cash_voucher(
    voucher_id: str,
    voucher_data: PettyCashVoucherUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a petty cash voucher (DRAFT only)"""
    try:
        voucher = await PettyCashService.update_voucher(db, voucher_id, voucher_data)
        if not voucher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Petty cash voucher not found"
            )
        return PettyCashVoucherResponse.model_validate(voucher)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete(
    "/vouchers/{voucher_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("delete:petty_cash"))]
)
async def delete_petty_cash_voucher(
    voucher_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a petty cash voucher (DRAFT only)"""
    try:
        success = await PettyCashService.delete_voucher(db, voucher_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Petty cash voucher not found"
            )
        return None
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/vouchers/{voucher_id}/approve",
    response_model=PettyCashVoucherResponse,
    dependencies=[Depends(require_permission("approve:petty_cash"))]
)
async def approve_petty_cash_voucher(
    voucher_id: str,
    current_user: dict = Depends(require_permission("approve:petty_cash")),
    db: AsyncSession = Depends(get_db)
):
    """Approve a petty cash voucher"""
    try:
        voucher = await PettyCashService.approve_voucher(
            db, voucher_id, approved_by=current_user["username"]
        )
        if not voucher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Petty cash voucher not found"
            )
        return PettyCashVoucherResponse.model_validate(voucher)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/vouchers/{voucher_id}/reject",
    response_model=PettyCashVoucherResponse,
    dependencies=[Depends(require_permission("approve:petty_cash"))]
)
async def reject_petty_cash_voucher(
    voucher_id: str,
    reject_data: PettyCashVoucherReject,
    current_user: dict = Depends(require_permission("approve:petty_cash")),
    db: AsyncSession = Depends(get_db)
):
    """Reject a petty cash voucher"""
    try:
        voucher = await PettyCashService.reject_voucher(
            db,
            voucher_id,
            rejected_by=current_user["username"],
            rejection_reason=reject_data.rejection_reason
        )
        if not voucher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Petty cash voucher not found"
            )
        return PettyCashVoucherResponse.model_validate(voucher)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/vouchers/{voucher_id}/post",
    dependencies=[Depends(require_permission("post:petty_cash"))]
)
async def post_petty_cash_voucher(
    voucher_id: str,
    post_data: PettyCashVoucherPost,
    current_user: dict = Depends(require_permission("post:petty_cash")),
    db: AsyncSession = Depends(get_db)
):
    """Post an approved voucher to journal"""
    try:
        entry = await PettyCashService.post_voucher_to_journal(
            db,
            voucher_id,
            petty_cash_account_id=post_data.petty_cash_account_id,
            expense_account_id=post_data.expense_account_id,
            posted_by=current_user["username"]
        )
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Petty cash voucher not found"
            )
        return {
            "success": True,
            "journal_entry_id": entry.id,
            "entry_number": entry.entry_number
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
