"""Pydantic schemas for Commission models"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any
from datetime import datetime
from enum import Enum


# ============= Enums =============

class CommissionTypeEnum(str, Enum):
    BIKE_SALE = "BIKE_SALE"
    LOAN_APPROVAL = "LOAN_APPROVAL"
    LOAN_DISBURSEMENT = "LOAN_DISBURSEMENT"
    REFERRAL = "REFERRAL"


class FormulaTypeEnum(str, Enum):
    FLAT_RATE = "FLAT_RATE"
    PERCENTAGE_OF_SALE = "PERCENTAGE_OF_SALE"
    PERCENTAGE_OF_PROFIT = "PERCENTAGE_OF_PROFIT"
    TIERED = "TIERED"
    CUSTOM = "CUSTOM"


class TierBasisEnum(str, Enum):
    SALE_AMOUNT = "SALE_AMOUNT"
    PROFIT_AMOUNT = "PROFIT_AMOUNT"
    UNIT_COUNT = "UNIT_COUNT"


# ============= CommissionRule Schemas =============

class TierConfiguration(BaseModel):
    """Schema for tier configuration"""
    min: float = Field(..., ge=0)
    max: Optional[float] = Field(None, ge=0)
    rate: float = Field(..., ge=0)

    @field_validator('max')
    @classmethod
    def validate_max(cls, v, info):
        if v is not None and 'min' in info.data:
            if v <= info.data['min']:
                raise ValueError('max must be greater than min')
        return v


class TierConfigurationWrapper(BaseModel):
    """Wrapper for tier configuration JSONB"""
    tiers: list[TierConfiguration]


class CommissionRuleBase(BaseModel):
    """Base schema for commission rule"""
    rule_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    commission_type: CommissionTypeEnum
    applicable_roles: list[str] = Field(default_factory=list)
    formula_type: FormulaTypeEnum
    flat_amount: Optional[float] = Field(None, ge=0)
    percentage_rate: Optional[float] = Field(None, ge=0, le=100)
    tier_basis: Optional[TierBasisEnum] = None
    tier_configuration: Optional[dict[str, Any]] = None
    min_commission: Optional[float] = Field(None, ge=0)
    max_commission: Optional[float] = Field(None, ge=0)
    min_sale_amount: Optional[float] = Field(None, ge=0)
    min_profit_amount: Optional[float] = Field(None, ge=0)
    branch_id: Optional[str] = None
    vehicle_condition: Optional[str] = Field(None, pattern="^(NEW|USED)$")
    priority: int = Field(default=0, ge=0)
    is_active: bool = True
    effective_from: Optional[datetime] = None
    effective_until: Optional[datetime] = None

    @field_validator('tier_configuration')
    @classmethod
    def validate_tier_configuration(cls, v, info):
        if v is not None:
            # Validate tier structure
            if 'tiers' not in v:
                raise ValueError('tier_configuration must contain "tiers" key')
            if not isinstance(v['tiers'], list):
                raise ValueError('tiers must be a list')
            if len(v['tiers']) == 0:
                raise ValueError('tiers list cannot be empty')

            # Validate each tier
            for tier in v['tiers']:
                if 'min' not in tier or 'rate' not in tier:
                    raise ValueError('Each tier must have "min" and "rate"')
                if tier['min'] < 0 or tier['rate'] < 0:
                    raise ValueError('Tier min and rate must be non-negative')
                if 'max' in tier and tier['max'] is not None:
                    if tier['max'] <= tier['min']:
                        raise ValueError('Tier max must be greater than min')

        return v

    @field_validator('effective_until')
    @classmethod
    def validate_effective_until(cls, v, info):
        if v is not None and 'effective_from' in info.data and info.data['effective_from'] is not None:
            if v <= info.data['effective_from']:
                raise ValueError('effective_until must be after effective_from')
        return v

    @field_validator('max_commission')
    @classmethod
    def validate_max_commission(cls, v, info):
        if v is not None and 'min_commission' in info.data and info.data['min_commission'] is not None:
            if v <= info.data['min_commission']:
                raise ValueError('max_commission must be greater than min_commission')
        return v


class CommissionRuleCreate(CommissionRuleBase):
    """Schema for creating commission rule"""
    pass


class CommissionRuleUpdate(BaseModel):
    """Schema for updating commission rule"""
    rule_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    commission_type: Optional[CommissionTypeEnum] = None
    applicable_roles: Optional[list[str]] = None
    formula_type: Optional[FormulaTypeEnum] = None
    flat_amount: Optional[float] = Field(None, ge=0)
    percentage_rate: Optional[float] = Field(None, ge=0, le=100)
    tier_basis: Optional[TierBasisEnum] = None
    tier_configuration: Optional[dict[str, Any]] = None
    min_commission: Optional[float] = Field(None, ge=0)
    max_commission: Optional[float] = Field(None, ge=0)
    min_sale_amount: Optional[float] = Field(None, ge=0)
    min_profit_amount: Optional[float] = Field(None, ge=0)
    branch_id: Optional[str] = None
    vehicle_condition: Optional[str] = Field(None, pattern="^(NEW|USED)$")
    priority: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None
    effective_from: Optional[datetime] = None
    effective_until: Optional[datetime] = None


class CommissionRuleResponse(CommissionRuleBase):
    """Schema for commission rule response"""
    id: str
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None

    class Config:
        from_attributes = True


class CommissionRuleListResponse(BaseModel):
    """Schema for list of commission rules"""
    items: list[CommissionRuleResponse]
    total: int
    page: int = 1
    page_size: int = 50


# ============= Commission Calculation Schemas =============

class CommissionCalculationRequest(BaseModel):
    """Schema for commission calculation request"""
    commission_type: CommissionTypeEnum
    employee_id: str
    sale_amount: float = Field(..., gt=0)
    cost_amount: float = Field(..., ge=0)
    unit_count: int = Field(default=1, ge=1)
    branch_id: Optional[str] = None
    vehicle_condition: Optional[str] = Field(None, pattern="^(NEW|USED)$")
    transaction_date: Optional[datetime] = None

    @field_validator('cost_amount')
    @classmethod
    def validate_cost_amount(cls, v, info):
        if 'sale_amount' in info.data and v > info.data['sale_amount']:
            raise ValueError('cost_amount cannot exceed sale_amount')
        return v


class CommissionCalculationResponse(BaseModel):
    """Schema for commission calculation response"""
    commission_amount: float
    applied_rule_id: Optional[str] = None
    applied_rule_name: Optional[str] = None
    formula_type: Optional[str] = None
    calculation_details: dict[str, Any] = Field(default_factory=dict)


class CommissionBatchCalculationRequest(BaseModel):
    """Schema for batch commission calculation (multiple employees)"""
    commission_type: CommissionTypeEnum
    employee_ids: list[str] = Field(..., min_length=1)
    sale_amount: float = Field(..., gt=0)
    cost_amount: float = Field(..., ge=0)
    unit_count: int = Field(default=1, ge=1)
    branch_id: Optional[str] = None
    vehicle_condition: Optional[str] = Field(None, pattern="^(NEW|USED)$")
    transaction_date: Optional[datetime] = None


class EmployeeCommissionResult(BaseModel):
    """Schema for individual employee commission result"""
    employee_id: str
    commission_amount: float
    applied_rule_id: Optional[str] = None
    applied_rule_name: Optional[str] = None
    formula_type: Optional[str] = None


class CommissionBatchCalculationResponse(BaseModel):
    """Schema for batch commission calculation response"""
    results: list[EmployeeCommissionResult]
    total_commission: float
    calculation_date: datetime


# ============= Commission Auto-generation Schemas =============

class CommissionAutoGenerateRequest(BaseModel):
    """Schema for auto-generating commissions on sale"""
    sale_id: str
    employee_ids: Optional[list[str]] = None  # If None, determine from sale record


class CommissionAutoGenerateResponse(BaseModel):
    """Schema for auto-generation response"""
    commissions_created: int
    commission_ids: list[str]
    total_amount: float
    details: list[EmployeeCommissionResult]
