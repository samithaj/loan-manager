"""
Pydantic schemas for loan application API
"""
from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, date
from uuid import UUID
from ..models.loan_application import ApplicationStatus
from ..models.loan_application_document import DocumentType
from ..models.loan_application_decision import DecisionType


# ============================================================================
# Branch Schemas
# ============================================================================


class BranchBase(BaseModel):
    code: str = Field(..., max_length=20)
    name: str = Field(..., max_length=200)
    region: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    is_active: bool = True


class BranchCreate(BranchBase):
    pass


class BranchUpdate(BaseModel):
    code: Optional[str] = Field(None, max_length=20)
    name: Optional[str] = Field(None, max_length=200)
    region: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class BranchResponse(BranchBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID


# ============================================================================
# Customer Schemas
# ============================================================================


class CustomerBase(BaseModel):
    nic: str = Field(..., max_length=20)
    full_name: str = Field(..., max_length=200)
    dob: Optional[date] = None
    address: str = Field(..., max_length=500)
    phone: str = Field(..., max_length=20)
    email: Optional[str] = Field(None, max_length=100)


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    nic: Optional[str] = Field(None, max_length=20)
    full_name: Optional[str] = Field(None, max_length=200)
    dob: Optional[date] = None
    address: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)


class CustomerResponse(CustomerBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    application_id: UUID


# ============================================================================
# Vehicle Schemas
# ============================================================================


class VehicleBase(BaseModel):
    chassis_no: str = Field(..., max_length=50)
    engine_no: Optional[str] = Field(None, max_length=50)
    make: str = Field(..., max_length=100)
    model: str = Field(..., max_length=100)
    year: Optional[int] = None
    color: Optional[str] = Field(None, max_length=50)
    registration_no: Optional[str] = Field(None, max_length=20)


class VehicleCreate(VehicleBase):
    pass


class VehicleUpdate(BaseModel):
    chassis_no: Optional[str] = Field(None, max_length=50)
    engine_no: Optional[str] = Field(None, max_length=50)
    make: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    year: Optional[int] = None
    color: Optional[str] = Field(None, max_length=50)
    registration_no: Optional[str] = Field(None, max_length=20)


class VehicleResponse(VehicleBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    application_id: UUID


# ============================================================================
# Document Schemas
# ============================================================================


class DocumentUploadRequest(BaseModel):
    """Request to get a pre-signed URL for document upload"""
    doc_type: DocumentType
    filename: str = Field(..., max_length=255)
    content_type: str = Field(..., max_length=100)
    file_size: int = Field(..., gt=0, description="File size in bytes")


class DocumentUploadResponse(BaseModel):
    """Response with pre-signed URL for upload"""
    upload_url: str
    file_url: str
    doc_id: UUID
    expires_in: int = Field(..., description="URL expiration time in seconds")


class DocumentConfirmRequest(BaseModel):
    """Confirm successful document upload"""
    doc_id: UUID
    file_hash: Optional[str] = Field(None, max_length=64)
    meta_json: Optional[dict] = None


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    application_id: UUID
    doc_type: DocumentType
    file_name: str
    file_size: int
    mime_type: str
    file_hash: Optional[str]
    meta_json: Optional[dict]
    uploaded_at: datetime
    uploaded_by: UUID


class DocumentDownloadResponse(BaseModel):
    """Response with pre-signed URL for download"""
    download_url: str
    expires_in: int = Field(..., description="URL expiration time in seconds")


# ============================================================================
# Decision Schemas
# ============================================================================


class DecisionCreate(BaseModel):
    decision: DecisionType
    notes: str = Field(..., min_length=1, max_length=2000)


class DecisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    application_id: UUID
    officer_user_id: UUID
    decision: DecisionType
    notes: str
    decided_at: datetime


# ============================================================================
# Audit Schemas
# ============================================================================


class AuditResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    application_id: UUID
    actor_user_id: Optional[UUID]
    action: str
    from_status: Optional[str]
    to_status: Optional[str]
    payload_json: Optional[dict]
    created_at: datetime


# ============================================================================
# Loan Application Schemas
# ============================================================================


class LoanApplicationCreate(BaseModel):
    """Create a new loan application (DRAFT)"""
    branch_id: UUID
    requested_amount: float = Field(..., gt=0)
    tenure_months: int = Field(..., gt=0, le=120)
    lmo_notes: Optional[str] = Field(None, max_length=2000)
    customer: CustomerCreate
    vehicle: VehicleCreate


class LoanApplicationUpdate(BaseModel):
    """Update draft application details"""
    requested_amount: Optional[float] = Field(None, gt=0)
    tenure_months: Optional[int] = Field(None, gt=0, le=120)
    lmo_notes: Optional[str] = Field(None, max_length=2000)
    customer: Optional[CustomerUpdate] = None
    vehicle: Optional[VehicleUpdate] = None


class LoanApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    application_no: str
    lmo_user_id: UUID
    branch_id: UUID
    requested_amount: float
    tenure_months: int
    status: ApplicationStatus
    lmo_notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    submitted_at: Optional[datetime]
    reviewed_at: Optional[datetime]
    decided_at: Optional[datetime]

    # Relationships (optional, loaded on demand)
    customer: Optional[CustomerResponse] = None
    vehicle: Optional[VehicleResponse] = None
    branch: Optional[BranchResponse] = None


class LoanApplicationDetailResponse(LoanApplicationResponse):
    """Detailed response with all related data"""
    documents: list[DocumentResponse] = []
    decisions: list[DecisionResponse] = []


class LoanApplicationListResponse(BaseModel):
    """Paginated list of applications"""
    items: list[LoanApplicationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class LoanApplicationFilters(BaseModel):
    """Filters for listing applications"""
    status: Optional[ApplicationStatus] = None
    branch_id: Optional[UUID] = None
    nic: Optional[str] = None
    chassis_no: Optional[str] = None
    application_no: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None


class TimelineEvent(BaseModel):
    """Timeline event for application history"""
    timestamp: datetime
    event_type: str
    actor: Optional[str] = None
    description: str
    details: Optional[dict] = None


class LoanApplicationTimeline(BaseModel):
    """Complete timeline of application events"""
    application_id: UUID
    events: list[TimelineEvent]
