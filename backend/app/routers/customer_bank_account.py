"""Customer Bank Account API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..rbac import require_permission
from ..services.customer_kyc_service import CustomerKYCService
from ..schemas.customer_kyc_schemas import (
    CustomerBankAccountCreate,
    CustomerBankAccountUpdate,
    CustomerBankAccountVerify,
    CustomerBankAccountResponse,
    CustomerBankAccountListResponse,
)

router = APIRouter(prefix="/v1", tags=["Customer KYC - Bank Accounts"])


@router.get(
    "/customers/{customer_id}/bank-accounts",
    response_model=CustomerBankAccountListResponse,
    dependencies=[Depends(require_permission("view:customer_bank_accounts"))]
)
async def list_customer_bank_accounts(
    customer_id: str,
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """List all bank accounts for a customer"""
    skip = (page - 1) * page_size
    accounts, total = await CustomerKYCService.list_bank_accounts(
        db, customer_id, skip=skip, limit=page_size
    )

    return {
        "items": [CustomerBankAccountResponse.model_validate(a) for a in accounts],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post(
    "/customers/{customer_id}/bank-accounts",
    response_model=CustomerBankAccountResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("create:customer_bank_accounts"))]
)
async def create_customer_bank_account(
    customer_id: str,
    account: CustomerBankAccountCreate,
    current_user: dict = Depends(require_permission("create:customer_bank_accounts")),
    db: AsyncSession = Depends(get_db)
):
    """Create a new bank account for a customer"""
    # Ensure customer_id matches
    if account.customer_id != customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer ID mismatch"
        )

    created_account = await CustomerKYCService.create_bank_account(
        db, account, created_by=current_user["username"]
    )

    return CustomerBankAccountResponse.model_validate(created_account)


@router.get(
    "/bank-accounts/{account_id}",
    response_model=CustomerBankAccountResponse,
    dependencies=[Depends(require_permission("view:customer_bank_accounts"))]
)
async def get_bank_account(
    account_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific bank account by ID"""
    account = await CustomerKYCService.get_bank_account(db, account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank account not found"
        )

    return CustomerBankAccountResponse.model_validate(account)


@router.put(
    "/bank-accounts/{account_id}",
    response_model=CustomerBankAccountResponse,
    dependencies=[Depends(require_permission("edit:customer_bank_accounts"))]
)
async def update_bank_account(
    account_id: str,
    account_data: CustomerBankAccountUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a bank account"""
    account = await CustomerKYCService.update_bank_account(db, account_id, account_data)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank account not found"
        )

    return CustomerBankAccountResponse.model_validate(account)


@router.delete(
    "/bank-accounts/{account_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("delete:customer_bank_accounts"))]
)
async def delete_bank_account(
    account_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a bank account"""
    success = await CustomerKYCService.delete_bank_account(db, account_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank account not found"
        )

    return None


@router.post(
    "/bank-accounts/{account_id}/verify",
    response_model=CustomerBankAccountResponse,
    dependencies=[Depends(require_permission("verify:customer_bank_accounts"))]
)
async def verify_bank_account(
    account_id: str,
    verify_data: CustomerBankAccountVerify,
    current_user: dict = Depends(require_permission("verify:customer_bank_accounts")),
    db: AsyncSession = Depends(get_db)
):
    """Verify a bank account"""
    account = await CustomerKYCService.verify_bank_account(
        db, account_id, verified_by=current_user["username"],
        verification_method=verify_data.verification_method
    )
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank account not found"
        )

    return CustomerBankAccountResponse.model_validate(account)


@router.post(
    "/customers/{customer_id}/bank-accounts/{account_id}/set-primary",
    response_model=CustomerBankAccountResponse,
    dependencies=[Depends(require_permission("edit:customer_bank_accounts"))]
)
async def set_primary_bank_account(
    customer_id: str,
    account_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Set a bank account as the primary account for the customer"""
    account = await CustomerKYCService.set_primary_account(db, account_id, customer_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank account not found or does not belong to this customer"
        )

    return CustomerBankAccountResponse.model_validate(account)
