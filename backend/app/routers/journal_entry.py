"""Journal Entry API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from ..db import get_db
from ..rbac import require_permission
from ..services.journal_entry_service import JournalEntryService
from ..schemas.accounting_schemas import (
    JournalEntryCreate,
    JournalEntryUpdate,
    JournalEntryResponse,
    JournalEntryListResponse,
    JournalEntryVoid,
)

router = APIRouter(prefix="/v1/accounting", tags=["Journal Entries"])


@router.get(
    "/journal-entries",
    response_model=JournalEntryListResponse,
    dependencies=[Depends(require_permission("view:journal_entries"))]
)
async def list_journal_entries(
    entry_type: str | None = None,
    status: str | None = None,
    branch_id: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """List journal entries with optional filters"""
    skip = (page - 1) * page_size
    entries, total = await JournalEntryService.list_entries(
        db,
        entry_type=entry_type,
        status=status,
        branch_id=branch_id,
        date_from=date_from,
        date_to=date_to,
        skip=skip,
        limit=page_size
    )

    return {
        "items": [JournalEntryResponse.model_validate(e) for e in entries],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post(
    "/journal-entries",
    response_model=JournalEntryResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("create:journal_entries"))]
)
async def create_journal_entry(
    entry: JournalEntryCreate,
    current_user: dict = Depends(require_permission("create:journal_entries")),
    db: AsyncSession = Depends(get_db)
):
    """Create a new journal entry"""
    try:
        created_entry = await JournalEntryService.create_entry(
            db, entry, created_by=current_user["username"]
        )
        return JournalEntryResponse.model_validate(created_entry)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/journal-entries/{entry_id}",
    response_model=JournalEntryResponse,
    dependencies=[Depends(require_permission("view:journal_entries"))]
)
async def get_journal_entry(
    entry_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific journal entry by ID"""
    entry = await JournalEntryService.get_entry(db, entry_id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Journal entry not found"
        )

    return JournalEntryResponse.model_validate(entry)


@router.put(
    "/journal-entries/{entry_id}",
    response_model=JournalEntryResponse,
    dependencies=[Depends(require_permission("edit:journal_entries"))]
)
async def update_journal_entry(
    entry_id: str,
    entry_data: JournalEntryUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a journal entry (DRAFT only)"""
    try:
        entry = await JournalEntryService.update_entry(db, entry_id, entry_data)
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Journal entry not found"
            )
        return JournalEntryResponse.model_validate(entry)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete(
    "/journal-entries/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("delete:journal_entries"))]
)
async def delete_journal_entry(
    entry_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a journal entry (DRAFT only)"""
    try:
        success = await JournalEntryService.delete_entry(db, entry_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Journal entry not found"
            )
        return None
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/journal-entries/{entry_id}/post",
    response_model=JournalEntryResponse,
    dependencies=[Depends(require_permission("post:journal_entries"))]
)
async def post_journal_entry(
    entry_id: str,
    current_user: dict = Depends(require_permission("post:journal_entries")),
    db: AsyncSession = Depends(get_db)
):
    """Post a journal entry to the ledger"""
    try:
        entry = await JournalEntryService.post_entry(
            db, entry_id, posted_by=current_user["username"]
        )
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Journal entry not found"
            )
        return JournalEntryResponse.model_validate(entry)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/journal-entries/{entry_id}/void",
    response_model=JournalEntryResponse,
    dependencies=[Depends(require_permission("void:journal_entries"))]
)
async def void_journal_entry(
    entry_id: str,
    void_data: JournalEntryVoid,
    current_user: dict = Depends(require_permission("void:journal_entries")),
    db: AsyncSession = Depends(get_db)
):
    """Void a posted journal entry"""
    try:
        entry = await JournalEntryService.void_entry(
            db, entry_id, voided_by=current_user["username"],
            void_reason=void_data.void_reason
        )
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Journal entry not found"
            )
        return JournalEntryResponse.model_validate(entry)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
