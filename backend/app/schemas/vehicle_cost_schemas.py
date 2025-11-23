"""
Pydantic schemas for Vehicle Cost Ledger API
"""
from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, date
from uuid import UUID
from decimal import Decimal
from ..models.vehicle_cost_ledger import CostEventType


# ============================================================================
# Fund Source Schemas
# ============================================================================


class FundSourceBase(BaseModel):
    code: str = Field(..., max_length=10)
    name: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: bool = True
    requires_approval: bool = False
    approval_threshold: Optional[float] = None


class FundSourceCreate(FundSourceBase):
    pass


class FundSourceUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None
    requires_approval: Optional[bool] = None
    approval_threshold: Optional[float] = None


class FundSourceResponse(FundSourceBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID


# ============================================================================
# Vehicle Cost Ledger Schemas
# ============================================================================


class VehicleCostCreate(BaseModel):
    """Create a new cost entry"""
    vehicle_id: str
    branch_id: UUID
    event_type: CostEventType
    fund_source_id: UUID
    amount: float = Field(..., gt=0)
    currency: str = Field(default="LKR", max_length=3)
    description: str = Field(..., min_length=1, max_length=500)
    notes: Optional[str] = Field(None, max_length=2000)
    reference_table: Optional[str] = Field(None, max_length=100)
    reference_id: Optional[str] = Field(None, max_length=100)
    receipt_urls: Optional[list[str]] = Field(default_factory=list)
    meta_json: Optional[dict] = Field(default_factory=dict)
    transaction_date: Optional[date] = None  # For bill number generation


class VehicleCostUpdate(BaseModel):
    """Update cost entry (only for unlocked entries)"""
    amount: Optional[float] = Field(None, gt=0)
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    notes: Optional[str] = Field(None, max_length=2000)
    receipt_urls: Optional[list[str]] = None
    meta_json: Optional[dict] = None


class VehicleCostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    vehicle_id: str
    branch_id: UUID
    event_type: CostEventType
    bill_no: str
    fund_source_id: UUID
    amount: float
    currency: str
    description: str
    notes: Optional[str]
    reference_table: Optional[str]
    reference_id: Optional[str]
    receipt_urls: Optional[list[str]]
    meta_json: Optional[dict]
    created_by: UUID
    created_at: datetime
    is_locked: bool
    locked_at: Optional[datetime]
    is_approved: bool
    approved_by: Optional[UUID]
    approved_at: Optional[datetime]


class VehicleCostDetailResponse(VehicleCostResponse):
    """Detailed cost entry with related data"""
    branch_name: Optional[str] = None
    fund_source_code: Optional[str] = None
    fund_source_name: Optional[str] = None
    creator_name: Optional[str] = None


class VehicleCostListResponse(BaseModel):
    """Paginated list of cost entries"""
    items: list[VehicleCostResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================================================
# Vehicle Cost Summary Schemas
# ============================================================================


class VehicleCostSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    vehicle_id: str
    purchase_cost: float
    transfer_cost: float
    repair_cost: float
    parts_cost: float
    admin_cost: float
    registration_cost: float
    insurance_cost: float
    transport_cost: float
    other_cost: float
    total_cost: float
    sale_price: Optional[float]
    profit: Optional[float]
    profit_margin_pct: Optional[float]
    total_entries: int
    locked_entries: int
    updated_at: datetime


class CostBreakdown(BaseModel):
    """Cost breakdown by category"""
    category: str
    amount: float
    percentage: float
    entry_count: int


class VehicleCostAnalysis(BaseModel):
    """Detailed cost analysis for a vehicle"""
    vehicle_id: str
    summary: VehicleCostSummaryResponse
    breakdown: list[CostBreakdown]
    by_branch: dict[str, float]
    by_fund_source: dict[str, float]
    timeline: list[dict]  # Chronological cost entries


# ============================================================================
# Bill Number Schemas
# ============================================================================


class BillNumberRequest(BaseModel):
    """Request to generate a bill number"""
    branch_id: UUID
    fund_source_id: UUID
    transaction_date: Optional[date] = None


class BillNumberResponse(BaseModel):
    """Generated bill number"""
    bill_no: str
    branch_code: str
    fund_code: str
    date: date
    sequence: int


class BillNumberValidation(BaseModel):
    """Bill number validation result"""
    is_valid: bool
    bill_no: str
    error_message: Optional[str] = None
    parsed_data: Optional[dict] = None


# ============================================================================
# Vehicle Sale Schemas
# ============================================================================


class VehicleSaleRequest(BaseModel):
    """Record a vehicle sale"""
    vehicle_id: str
    sale_price: float = Field(..., gt=0)
    sold_at: date
    buyer_name: Optional[str] = Field(None, max_length=200)
    buyer_contact: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=1000)
    lock_costs: bool = True  # Lock all cost entries after sale


class VehicleSaleResponse(BaseModel):
    """Sale confirmation with profit calculation"""
    vehicle_id: str
    sale_price: float
    total_cost: float
    profit: float
    profit_margin_pct: float
    sold_at: date
    costs_locked: bool


# ============================================================================
# Cost Filters and Queries
# ============================================================================


class VehicleCostFilters(BaseModel):
    """Filters for cost entry queries"""
    vehicle_id: Optional[str] = None
    branch_id: Optional[UUID] = None
    event_type: Optional[CostEventType] = None
    fund_source_id: Optional[UUID] = None
    bill_no: Optional[str] = None
    is_locked: Optional[bool] = None
    is_approved: Optional[bool] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None


class CostStatistics(BaseModel):
    """Cost statistics summary"""
    total_vehicles: int
    total_cost_entries: int
    total_amount: float
    avg_cost_per_vehicle: float
    locked_entries: int
    pending_approval: int
    by_event_type: dict[str, float]
    by_fund_source: dict[str, float]


# ============================================================================
# Petty Cash Tracking Schemas
# ============================================================================


class PettyCashSummary(BaseModel):
    """Petty cash summary for a branch"""
    branch_id: UUID
    branch_name: str
    period_start: date
    period_end: date
    opening_float: float
    total_spent: float
    replenishments: float
    closing_balance: float
    pending_reconciliation: int


class PettyCashEntry(BaseModel):
    """Individual petty cash transaction"""
    bill_no: str
    date: date
    amount: float
    description: str
    vehicle_id: Optional[str]
    receipt_attached: bool
    created_by: str
