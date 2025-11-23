"""Chart of Accounts API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..rbac import require_permission
from ..services.chart_of_accounts_service import ChartOfAccountsService
from ..schemas.accounting_schemas import (
    ChartOfAccountsCreate,
    ChartOfAccountsUpdate,
    ChartOfAccountsResponse,
    ChartOfAccountsListResponse,
)

router = APIRouter(prefix="/v1/accounting", tags=["Chart of Accounts"])


@router.get(
    "/accounts",
    response_model=ChartOfAccountsListResponse,
    dependencies=[Depends(require_permission("view:chart_of_accounts"))]
)
async def list_accounts(
    category: str | None = None,
    is_active: bool | None = None,
    is_header: bool | None = None,
    branch_id: str | None = None,
    page: int = 1,
    page_size: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List accounts with optional filters"""
    skip = (page - 1) * page_size
    accounts, total = await ChartOfAccountsService.list_accounts(
        db,
        category=category,
        is_active=is_active,
        is_header=is_header,
        branch_id=branch_id,
        skip=skip,
        limit=page_size
    )

    return {
        "items": [ChartOfAccountsResponse.model_validate(a) for a in accounts],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get(
    "/accounts/hierarchy",
    response_model=list[ChartOfAccountsResponse],
    dependencies=[Depends(require_permission("view:chart_of_accounts"))]
)
async def get_account_hierarchy(
    db: AsyncSession = Depends(get_db)
):
    """Get full account hierarchy (top-level accounts with children)"""
    accounts = await ChartOfAccountsService.get_account_hierarchy(db)
    return [ChartOfAccountsResponse.model_validate(a) for a in accounts]


@router.post(
    "/accounts",
    response_model=ChartOfAccountsResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("create:chart_of_accounts"))]
)
async def create_account(
    account: ChartOfAccountsCreate,
    current_user: dict = Depends(require_permission("create:chart_of_accounts")),
    db: AsyncSession = Depends(get_db)
):
    """Create a new account"""
    try:
        created_account = await ChartOfAccountsService.create_account(
            db, account, created_by=current_user["username"]
        )
        return ChartOfAccountsResponse.model_validate(created_account)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/accounts/{account_id}",
    response_model=ChartOfAccountsResponse,
    dependencies=[Depends(require_permission("view:chart_of_accounts"))]
)
async def get_account(
    account_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific account by ID"""
    account = await ChartOfAccountsService.get_account(db, account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    return ChartOfAccountsResponse.model_validate(account)


@router.put(
    "/accounts/{account_id}",
    response_model=ChartOfAccountsResponse,
    dependencies=[Depends(require_permission("edit:chart_of_accounts"))]
)
async def update_account(
    account_id: str,
    account_data: ChartOfAccountsUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an account"""
    try:
        account = await ChartOfAccountsService.update_account(db, account_id, account_data)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
        return ChartOfAccountsResponse.model_validate(account)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete(
    "/accounts/{account_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("delete:chart_of_accounts"))]
)
async def delete_account(
    account_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete an account"""
    try:
        success = await ChartOfAccountsService.delete_account(db, account_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
        return None
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
