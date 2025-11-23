"""
Loan Application API Router
Handles loan application CRUD, submissions, decisions, and document management
"""
from __future__ import annotations

from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..rbac import get_current_user, require_permission, ROLE_LOAN_OFFICER
from ..services.loan_application_service import LoanApplicationService, StateTransitionError
from ..services.loan_document_storage_service import DocumentStorageService
from ..schemas.loan_application_schemas import (
    LoanApplicationCreate,
    LoanApplicationUpdate,
    LoanApplicationResponse,
    LoanApplicationDetailResponse,
    LoanApplicationListResponse,
    LoanApplicationFilters,
    DecisionCreate,
    DecisionResponse,
    DocumentUploadRequest,
    DocumentUploadResponse,
    DocumentConfirmRequest,
    DocumentResponse,
    DocumentDownloadResponse,
    LoanApplicationTimeline,
    TimelineEvent,
    BranchCreate,
    BranchUpdate,
    BranchResponse,
)
from ..models.loan_application import ApplicationStatus


router = APIRouter(prefix="/api/v1/loan-applications", tags=["loan_applications"])


# ============================================================================
# Branch Management Endpoints
# ============================================================================


@router.post("/branches", response_model=BranchResponse, status_code=status.HTTP_201_CREATED)
async def create_branch(
    data: BranchCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dict, Depends(require_permission("branches:write"))],
):
    """Create a new branch (Admin only)"""
    from ..models.branch import Branch

    branch = Branch(**data.model_dump())
    db.add(branch)
    await db.commit()
    await db.refresh(branch)

    return branch


@router.get("/branches", response_model=list[BranchResponse])
async def list_branches(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dict, Depends(require_permission("branches:read"))],
    active_only: bool = Query(True, description="Filter active branches only"),
):
    """List all branches"""
    from sqlalchemy import select
    from ..models.branch import Branch

    stmt = select(Branch)
    if active_only:
        stmt = stmt.where(Branch.is_active == True)

    result = await db.execute(stmt)
    branches = result.scalars().all()

    return branches


@router.get("/branches/{branch_id}", response_model=BranchResponse)
async def get_branch(
    branch_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dict, Depends(require_permission("branches:read"))],
):
    """Get branch by ID"""
    from ..models.branch import Branch

    branch = await db.get(Branch, branch_id)
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")

    return branch


# ============================================================================
# Loan Application CRUD Endpoints
# ============================================================================


@router.post("", response_model=LoanApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(
    data: LoanApplicationCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dict, Depends(require_permission("loan_applications:write"))],
):
    """Create a new loan application (DRAFT status)"""
    service = LoanApplicationService(db)

    try:
        # Extract user ID from current_user
        from sqlalchemy import select
        from ..models.user import User

        stmt = select(User.id).where(User.username == current_user["username"])
        result = await db.execute(stmt)
        user_id = result.scalar_one()

        application = await service.create_application(data, user_id)

        # Load relations for response
        application = await service.get_application(application.id, load_relations=True)

        return application

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=LoanApplicationListResponse)
async def list_applications(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dict, Depends(require_permission("loan_applications:read"))],
    status_filter: ApplicationStatus = Query(None, alias="status"),
    branch_id: UUID = Query(None),
    nic: str = Query(None),
    chassis_no: str = Query(None),
    application_no: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List loan applications with filters and pagination"""
    service = LoanApplicationService(db)

    # Build filters
    filters = LoanApplicationFilters(
        status=status_filter,
        branch_id=branch_id,
        nic=nic,
        chassis_no=chassis_no,
        application_no=application_no,
    )

    # Check if user is branch-scoped
    user_branch_id = current_user.get("metadata", {}).get("branch_id")

    items, total = await service.list_applications(
        filters=filters,
        page=page,
        page_size=page_size,
        user_branch_id=user_branch_id,
    )

    total_pages = (total + page_size - 1) // page_size

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.get("/{application_id}", response_model=LoanApplicationDetailResponse)
async def get_application(
    application_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dict, Depends(require_permission("loan_applications:read"))],
):
    """Get application by ID with full details"""
    service = LoanApplicationService(db)

    application = await service.get_application(application_id, load_relations=True)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    return application


@router.patch("/{application_id}", response_model=LoanApplicationResponse)
async def update_application(
    application_id: UUID,
    data: LoanApplicationUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dict, Depends(require_permission("loan_applications:write"))],
):
    """Update draft application"""
    service = LoanApplicationService(db)

    try:
        # Get user ID
        from sqlalchemy import select
        from ..models.user import User

        stmt = select(User.id).where(User.username == current_user["username"])
        result = await db.execute(stmt)
        user_id = result.scalar_one()

        application = await service.update_application(application_id, data, user_id)
        return application

    except StateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# State Transition Endpoints
# ============================================================================


@router.post("/{application_id}/submit", response_model=LoanApplicationResponse)
async def submit_application(
    application_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dict, Depends(require_permission("loan_applications:submit"))],
):
    """Submit application for review"""
    service = LoanApplicationService(db)

    try:
        # Get user ID
        from sqlalchemy import select
        from ..models.user import User

        stmt = select(User.id).where(User.username == current_user["username"])
        result = await db.execute(stmt)
        user_id = result.scalar_one()

        application = await service.submit_application(application_id, user_id)
        return application

    except StateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{application_id}/start-review", response_model=LoanApplicationResponse)
async def start_review(
    application_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dict, Depends(require_permission("loan_applications:review"))],
):
    """Start reviewing application (Loan Officer)"""
    service = LoanApplicationService(db)

    try:
        # Get user ID
        from sqlalchemy import select
        from ..models.user import User

        stmt = select(User.id).where(User.username == current_user["username"])
        result = await db.execute(stmt)
        user_id = result.scalar_one()

        application = await service.start_review(application_id, user_id)
        return application

    except StateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{application_id}/decision", response_model=LoanApplicationResponse)
async def make_decision(
    application_id: UUID,
    decision: DecisionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dict, Depends(require_permission("loan_applications:approve"))],
):
    """Make decision on application (Approve/Reject/Request Info)"""
    service = LoanApplicationService(db)

    try:
        # Get user ID
        from sqlalchemy import select
        from ..models.user import User

        stmt = select(User.id).where(User.username == current_user["username"])
        result = await db.execute(stmt)
        user_id = result.scalar_one()

        application = await service.make_decision(application_id, decision, user_id)
        return application

    except StateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{application_id}/cancel", response_model=LoanApplicationResponse)
async def cancel_application(
    application_id: UUID,
    reason: str = Query(..., min_length=1),
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dict, Depends(require_permission("loan_applications:write"))],
):
    """Cancel application"""
    service = LoanApplicationService(db)

    try:
        # Get user ID
        from sqlalchemy import select
        from ..models.user import User

        stmt = select(User.id).where(User.username == current_user["username"])
        result = await db.execute(stmt)
        user_id = result.scalar_one()

        application = await service.cancel_application(application_id, user_id, reason)
        return application

    except StateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# Document Management Endpoints
# ============================================================================


@router.post("/{application_id}/documents/presign", response_model=DocumentUploadResponse)
async def create_presigned_upload_url(
    application_id: UUID,
    request: DocumentUploadRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dict, Depends(require_permission("loan_applications:upload_documents"))],
):
    """Get pre-signed URL for document upload"""
    service = DocumentStorageService(db)

    try:
        # Get user ID
        from sqlalchemy import select
        from ..models.user import User

        stmt = select(User.id).where(User.username == current_user["username"])
        result = await db.execute(stmt)
        user_id = result.scalar_one()

        upload_url, file_url, doc_id = await service.create_presigned_upload_url(
            application_id, request, user_id
        )

        return {
            "upload_url": upload_url,
            "file_url": file_url,
            "doc_id": doc_id,
            "expires_in": 3600,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/documents/{doc_id}/confirm", response_model=DocumentResponse)
async def confirm_document_upload(
    doc_id: UUID,
    request: DocumentConfirmRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dict, Depends(require_permission("loan_applications:upload_documents"))],
):
    """Confirm successful document upload"""
    service = DocumentStorageService(db)

    try:
        document = await service.confirm_upload(
            request.doc_id,
            file_hash=request.file_hash,
            meta_json=request.meta_json,
        )
        return document

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/documents/{doc_id}/download", response_model=DocumentDownloadResponse)
async def get_document_download_url(
    doc_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dict, Depends(require_permission("loan_applications:view_documents"))],
):
    """Get pre-signed URL for document download"""
    service = DocumentStorageService(db)

    try:
        download_url = await service.create_presigned_download_url(doc_id)

        return {
            "download_url": download_url,
            "expires_in": 3600,
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{application_id}/documents", response_model=list[DocumentResponse])
async def list_application_documents(
    application_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dict, Depends(require_permission("loan_applications:view_documents"))],
):
    """List all documents for an application"""
    from sqlalchemy import select
    from ..models.loan_application_document import LoanApplicationDocument

    stmt = select(LoanApplicationDocument).where(
        LoanApplicationDocument.application_id == application_id
    ).order_by(LoanApplicationDocument.uploaded_at.desc())

    result = await db.execute(stmt)
    documents = result.scalars().all()

    return documents


@router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    doc_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dict, Depends(require_permission("loan_applications:upload_documents"))],
):
    """Delete a document"""
    service = DocumentStorageService(db)

    success = await service.delete_document(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")


# ============================================================================
# Timeline/Audit Endpoints
# ============================================================================


@router.get("/{application_id}/timeline", response_model=LoanApplicationTimeline)
async def get_application_timeline(
    application_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dict, Depends(require_permission("loan_applications:read"))],
):
    """Get complete timeline of application events"""
    service = LoanApplicationService(db)

    # Verify application exists
    application = await service.get_application(application_id, load_relations=False)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    # Get audit logs
    audit_logs = await service.get_timeline(application_id)

    # Convert audit logs to timeline events
    events = []
    for log in audit_logs:
        # Get actor username if available
        actor_name = None
        if log.actor_user_id:
            from sqlalchemy import select
            from ..models.user import User

            stmt = select(User.username).where(User.id == log.actor_user_id)
            result = await db.execute(stmt)
            actor_name = result.scalar_one_or_none()

        # Build description based on action
        description = log.action.replace("_", " ").title()
        if log.from_status and log.to_status:
            description += f": {log.from_status} → {log.to_status}"

        events.append(
            TimelineEvent(
                timestamp=log.created_at,
                event_type=log.action,
                actor=actor_name,
                description=description,
                details=log.payload_json,
            )
        )

    return {
        "application_id": application_id,
        "events": events,
    }


# ============================================================================
# Statistics/Dashboard Endpoints (for Loan Officers)
# ============================================================================


@router.get("/stats/queue", response_model=dict)
async def get_queue_statistics(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dict, Depends(require_permission("loan_applications:review"))],
):
    """Get queue statistics for loan officers"""
    from sqlalchemy import select, func
    from ..models.loan_application import LoanApplication

    # Count applications by status
    stmt = select(
        LoanApplication.status,
        func.count(LoanApplication.id).label("count")
    ).group_by(LoanApplication.status)

    result = await db.execute(stmt)
    status_counts = {row.status.value: row.count for row in result}

    return {
        "submitted": status_counts.get(ApplicationStatus.SUBMITTED.value, 0),
        "under_review": status_counts.get(ApplicationStatus.UNDER_REVIEW.value, 0),
        "needs_more_info": status_counts.get(ApplicationStatus.NEEDS_MORE_INFO.value, 0),
        "approved": status_counts.get(ApplicationStatus.APPROVED.value, 0),
        "rejected": status_counts.get(ApplicationStatus.REJECTED.value, 0),
    }
