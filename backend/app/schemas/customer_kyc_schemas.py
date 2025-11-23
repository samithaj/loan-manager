"""Pydantic schemas for Customer KYC models"""

from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional
from datetime import date, datetime
from enum import Enum


# ============= Enums =============

class EmploymentTypeEnum(str, Enum):
    PERMANENT = "PERMANENT"
    CONTRACT = "CONTRACT"
    TEMPORARY = "TEMPORARY"
    SELF_EMPLOYED = "SELF_EMPLOYED"
    BUSINESS_OWNER = "BUSINESS_OWNER"
    RETIRED = "RETIRED"
    UNEMPLOYED = "UNEMPLOYED"


class IncomeFrequencyEnum(str, Enum):
    MONTHLY = "MONTHLY"
    WEEKLY = "WEEKLY"
    DAILY = "DAILY"
    ANNUAL = "ANNUAL"


class AccountTypeEnum(str, Enum):
    SAVINGS = "SAVINGS"
    CURRENT = "CURRENT"
    FIXED_DEPOSIT = "FIXED_DEPOSIT"
    SALARY = "SALARY"


class BankAccountStatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    CLOSED = "CLOSED"


# ============= CustomerGuarantor Schemas =============

class CustomerGuarantorBase(BaseModel):
    """Base schema for guarantor"""
    customer_id: str
    full_name: str = Field(..., min_length=1, max_length=200)
    nic: str = Field(..., min_length=1, max_length=20)
    date_of_birth: Optional[date] = None
    mobile: str = Field(..., min_length=1, max_length=20)
    email: Optional[EmailStr] = None
    address_line1: str = Field(..., min_length=1, max_length=200)
    address_line2: Optional[str] = Field(None, max_length=200)
    city: str = Field(..., min_length=1, max_length=100)
    province: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=10)
    relationship_to_customer: str = Field(..., min_length=1, max_length=50)
    employer_name: Optional[str] = Field(None, max_length=200)
    job_title: Optional[str] = Field(None, max_length=100)
    employment_type: Optional[str] = Field(None, max_length=50)
    monthly_income: Optional[float] = Field(None, ge=0)
    years_employed: Optional[float] = Field(None, ge=0)
    employer_address: Optional[str] = None
    employer_phone: Optional[str] = Field(None, max_length=20)
    nic_document_url: Optional[str] = Field(None, max_length=500)
    salary_slip_url: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None
    is_primary: bool = False


class CustomerGuarantorCreate(CustomerGuarantorBase):
    """Schema for creating guarantor"""
    pass


class CustomerGuarantorUpdate(BaseModel):
    """Schema for updating guarantor"""
    full_name: Optional[str] = Field(None, min_length=1, max_length=200)
    nic: Optional[str] = Field(None, min_length=1, max_length=20)
    date_of_birth: Optional[date] = None
    mobile: Optional[str] = Field(None, min_length=1, max_length=20)
    email: Optional[EmailStr] = None
    address_line1: Optional[str] = Field(None, min_length=1, max_length=200)
    address_line2: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    province: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=10)
    relationship_to_customer: Optional[str] = Field(None, min_length=1, max_length=50)
    employer_name: Optional[str] = Field(None, max_length=200)
    job_title: Optional[str] = Field(None, max_length=100)
    employment_type: Optional[str] = Field(None, max_length=50)
    monthly_income: Optional[float] = Field(None, ge=0)
    years_employed: Optional[float] = Field(None, ge=0)
    employer_address: Optional[str] = None
    employer_phone: Optional[str] = Field(None, max_length=20)
    nic_document_url: Optional[str] = Field(None, max_length=500)
    salary_slip_url: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None
    is_primary: Optional[bool] = None


class CustomerGuarantorVerify(BaseModel):
    """Schema for verifying guarantor"""
    notes: Optional[str] = None


class CustomerGuarantorResponse(CustomerGuarantorBase):
    """Schema for guarantor response"""
    id: str
    is_verified: bool
    verified_at: Optional[datetime] = None
    verified_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============= CustomerEmployment Schemas =============

class CustomerEmploymentBase(BaseModel):
    """Base schema for employment"""
    customer_id: str
    employment_type: EmploymentTypeEnum
    employer_name: str = Field(..., min_length=1, max_length=200)
    job_title: str = Field(..., min_length=1, max_length=100)
    industry: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    start_date: date
    end_date: Optional[date] = None
    is_current: bool = True
    gross_income: float = Field(..., gt=0)
    income_frequency: IncomeFrequencyEnum = IncomeFrequencyEnum.MONTHLY
    other_income: Optional[float] = Field(None, ge=0)
    other_income_source: Optional[str] = Field(None, max_length=200)
    employer_address: Optional[str] = None
    employer_phone: Optional[str] = Field(None, max_length=20)
    employer_email: Optional[EmailStr] = None
    hr_contact_name: Optional[str] = Field(None, max_length=100)
    hr_contact_phone: Optional[str] = Field(None, max_length=20)
    salary_slip_url: Optional[str] = Field(None, max_length=500)
    employment_letter_url: Optional[str] = Field(None, max_length=500)
    bank_statement_url: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None

    @field_validator('end_date')
    @classmethod
    def validate_end_date(cls, v, info):
        if v is not None and 'start_date' in info.data:
            if v < info.data['start_date']:
                raise ValueError('end_date must be after start_date')
        return v


class CustomerEmploymentCreate(CustomerEmploymentBase):
    """Schema for creating employment record"""
    pass


class CustomerEmploymentUpdate(BaseModel):
    """Schema for updating employment record"""
    employment_type: Optional[EmploymentTypeEnum] = None
    employer_name: Optional[str] = Field(None, min_length=1, max_length=200)
    job_title: Optional[str] = Field(None, min_length=1, max_length=100)
    industry: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: Optional[bool] = None
    gross_income: Optional[float] = Field(None, gt=0)
    income_frequency: Optional[IncomeFrequencyEnum] = None
    other_income: Optional[float] = Field(None, ge=0)
    other_income_source: Optional[str] = Field(None, max_length=200)
    employer_address: Optional[str] = None
    employer_phone: Optional[str] = Field(None, max_length=20)
    employer_email: Optional[EmailStr] = None
    hr_contact_name: Optional[str] = Field(None, max_length=100)
    hr_contact_phone: Optional[str] = Field(None, max_length=20)
    salary_slip_url: Optional[str] = Field(None, max_length=500)
    employment_letter_url: Optional[str] = Field(None, max_length=500)
    bank_statement_url: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None


class CustomerEmploymentVerify(BaseModel):
    """Schema for verifying employment"""
    verification_method: str = Field(..., max_length=50)  # PHONE_CALL, LETTER, EMAIL
    notes: Optional[str] = None


class CustomerEmploymentResponse(CustomerEmploymentBase):
    """Schema for employment response"""
    id: str
    monthly_income: float
    is_verified: bool
    verified_at: Optional[datetime] = None
    verified_by: Optional[str] = None
    verification_method: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    years_employed: float

    class Config:
        from_attributes = True


# ============= CustomerBankAccount Schemas =============

class CustomerBankAccountBase(BaseModel):
    """Base schema for bank account"""
    customer_id: str
    bank_name: str = Field(..., min_length=1, max_length=100)
    bank_code: Optional[str] = Field(None, max_length=20)
    branch_name: str = Field(..., min_length=1, max_length=100)
    branch_code: Optional[str] = Field(None, max_length=20)
    account_number: str = Field(..., min_length=1, max_length=50)
    account_name: str = Field(..., min_length=1, max_length=200)
    account_type: AccountTypeEnum
    status: BankAccountStatusEnum = BankAccountStatusEnum.ACTIVE
    is_primary: bool = False
    is_salary_account: bool = False
    bank_statement_url: Optional[str] = Field(None, max_length=500)
    bank_letter_url: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None


class CustomerBankAccountCreate(CustomerBankAccountBase):
    """Schema for creating bank account"""
    pass


class CustomerBankAccountUpdate(BaseModel):
    """Schema for updating bank account"""
    bank_name: Optional[str] = Field(None, min_length=1, max_length=100)
    bank_code: Optional[str] = Field(None, max_length=20)
    branch_name: Optional[str] = Field(None, min_length=1, max_length=100)
    branch_code: Optional[str] = Field(None, max_length=20)
    account_number: Optional[str] = Field(None, min_length=1, max_length=50)
    account_name: Optional[str] = Field(None, min_length=1, max_length=200)
    account_type: Optional[AccountTypeEnum] = None
    status: Optional[BankAccountStatusEnum] = None
    is_primary: Optional[bool] = None
    is_salary_account: Optional[bool] = None
    bank_statement_url: Optional[str] = Field(None, max_length=500)
    bank_letter_url: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None


class CustomerBankAccountVerify(BaseModel):
    """Schema for verifying bank account"""
    verification_method: str = Field(..., max_length=50)  # BANK_STATEMENT, LETTER
    notes: Optional[str] = None


class CustomerBankAccountResponse(CustomerBankAccountBase):
    """Schema for bank account response"""
    id: str
    is_verified: bool
    verified_at: Optional[datetime] = None
    verified_by: Optional[str] = None
    verification_method: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============= List Response Schemas =============

class CustomerGuarantorListResponse(BaseModel):
    """Schema for list of guarantors"""
    items: list[CustomerGuarantorResponse]
    total: int
    page: int = 1
    page_size: int = 50


class CustomerEmploymentListResponse(BaseModel):
    """Schema for list of employment records"""
    items: list[CustomerEmploymentResponse]
    total: int
    page: int = 1
    page_size: int = 50


class CustomerBankAccountListResponse(BaseModel):
    """Schema for list of bank accounts"""
    items: list[CustomerBankAccountResponse]
    total: int
    page: int = 1
    page_size: int = 50
