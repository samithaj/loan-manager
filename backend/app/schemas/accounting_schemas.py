"""Pydantic schemas for Accounting models"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any
from datetime import date, datetime
from enum import Enum


# ============= Enums =============

class AccountCategoryEnum(str, Enum):
    ASSET = "ASSET"
    LIABILITY = "LIABILITY"
    EQUITY = "EQUITY"
    REVENUE = "REVENUE"
    EXPENSE = "EXPENSE"


class AccountTypeEnum(str, Enum):
    # Assets
    CURRENT_ASSET = "CURRENT_ASSET"
    FIXED_ASSET = "FIXED_ASSET"
    INVENTORY = "INVENTORY"
    ACCOUNTS_RECEIVABLE = "ACCOUNTS_RECEIVABLE"
    CASH_AND_BANK = "CASH_AND_BANK"
    # Liabilities
    CURRENT_LIABILITY = "CURRENT_LIABILITY"
    LONG_TERM_LIABILITY = "LONG_TERM_LIABILITY"
    ACCOUNTS_PAYABLE = "ACCOUNTS_PAYABLE"
    # Equity
    OWNER_EQUITY = "OWNER_EQUITY"
    RETAINED_EARNINGS = "RETAINED_EARNINGS"
    # Revenue
    SALES_REVENUE = "SALES_REVENUE"
    SERVICE_REVENUE = "SERVICE_REVENUE"
    OTHER_INCOME = "OTHER_INCOME"
    # Expenses
    COST_OF_GOODS_SOLD = "COST_OF_GOODS_SOLD"
    OPERATING_EXPENSE = "OPERATING_EXPENSE"
    ADMINISTRATIVE_EXPENSE = "ADMINISTRATIVE_EXPENSE"
    DEPRECIATION = "DEPRECIATION"
    INTEREST_EXPENSE = "INTEREST_EXPENSE"


class JournalEntryStatusEnum(str, Enum):
    DRAFT = "DRAFT"
    POSTED = "POSTED"
    VOID = "VOID"


class JournalEntryTypeEnum(str, Enum):
    GENERAL = "GENERAL"
    VEHICLE_PURCHASE = "VEHICLE_PURCHASE"
    VEHICLE_SALE = "VEHICLE_SALE"
    REPAIR_EXPENSE = "REPAIR_EXPENSE"
    PETTY_CASH = "PETTY_CASH"
    SALARY = "SALARY"
    COMMISSION = "COMMISSION"
    LOAN_DISBURSEMENT = "LOAN_DISBURSEMENT"
    LOAN_REPAYMENT = "LOAN_REPAYMENT"
    DEPRECIATION = "DEPRECIATION"
    ADJUSTMENT = "ADJUSTMENT"


class VoucherTypeEnum(str, Enum):
    RECEIPT = "RECEIPT"
    DISBURSEMENT = "DISBURSEMENT"


class VoucherStatusEnum(str, Enum):
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    POSTED = "POSTED"
    VOID = "VOID"


# ============= ChartOfAccounts Schemas =============

class ChartOfAccountsBase(BaseModel):
    """Base schema for chart of accounts"""
    account_code: str = Field(..., min_length=1, max_length=20)
    account_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category: AccountCategoryEnum
    account_type: AccountTypeEnum
    parent_account_id: Optional[str] = None
    level: int = Field(default=0, ge=0)
    is_header: bool = False
    branch_id: Optional[str] = None
    is_active: bool = True


class ChartOfAccountsCreate(ChartOfAccountsBase):
    """Schema for creating account"""
    pass


class ChartOfAccountsUpdate(BaseModel):
    """Schema for updating account"""
    account_code: Optional[str] = Field(None, min_length=1, max_length=20)
    account_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[AccountCategoryEnum] = None
    account_type: Optional[AccountTypeEnum] = None
    parent_account_id: Optional[str] = None
    level: Optional[int] = Field(None, ge=0)
    is_header: Optional[bool] = None
    branch_id: Optional[str] = None
    is_active: Optional[bool] = None


class ChartOfAccountsResponse(ChartOfAccountsBase):
    """Schema for account response"""
    id: str
    normal_balance: str
    is_system: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None

    class Config:
        from_attributes = True


class ChartOfAccountsHierarchyResponse(ChartOfAccountsResponse):
    """Schema for account with children"""
    sub_accounts: list["ChartOfAccountsHierarchyResponse"] = Field(default_factory=list)


class ChartOfAccountsListResponse(BaseModel):
    """Schema for list of accounts"""
    items: list[ChartOfAccountsResponse]
    total: int
    page: int = 1
    page_size: int = 100


# ============= JournalEntry Schemas =============

class JournalEntryLineBase(BaseModel):
    """Base schema for journal entry line"""
    line_number: int = Field(..., ge=1)
    account_id: str
    description: Optional[str] = None
    debit_amount: Optional[float] = Field(None, ge=0)
    credit_amount: Optional[float] = Field(None, ge=0)
    cost_center: Optional[str] = Field(None, max_length=50)

    @field_validator('credit_amount')
    @classmethod
    def validate_debit_or_credit(cls, v, info):
        debit = info.data.get('debit_amount')
        if (debit is None and v is None) or (debit is not None and v is not None):
            raise ValueError('Exactly one of debit_amount or credit_amount must be provided')
        return v


class JournalEntryLineCreate(JournalEntryLineBase):
    """Schema for creating journal entry line"""
    pass


class JournalEntryLineResponse(JournalEntryLineBase):
    """Schema for journal entry line response"""
    id: str
    journal_entry_id: str
    account_code: Optional[str] = None
    account_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class JournalEntryBase(BaseModel):
    """Base schema for journal entry"""
    entry_date: date
    entry_type: JournalEntryTypeEnum = JournalEntryTypeEnum.GENERAL
    description: str = Field(..., min_length=1)
    branch_id: str
    reference_type: Optional[str] = Field(None, max_length=50)
    reference_id: Optional[str] = None
    reference_number: Optional[str] = Field(None, max_length=100)


class JournalEntryCreate(JournalEntryBase):
    """Schema for creating journal entry"""
    lines: list[JournalEntryLineCreate] = Field(..., min_length=2)

    @field_validator('lines')
    @classmethod
    def validate_balanced_entry(cls, v):
        total_debit = sum(line.debit_amount or 0 for line in v)
        total_credit = sum(line.credit_amount or 0 for line in v)
        if abs(total_debit - total_credit) > 0.01:
            raise ValueError(f'Entry is not balanced: debits={total_debit}, credits={total_credit}')
        return v


class JournalEntryUpdate(BaseModel):
    """Schema for updating journal entry (only DRAFT entries)"""
    entry_date: Optional[date] = None
    entry_type: Optional[JournalEntryTypeEnum] = None
    description: Optional[str] = Field(None, min_length=1)
    reference_type: Optional[str] = Field(None, max_length=50)
    reference_id: Optional[str] = None
    reference_number: Optional[str] = Field(None, max_length=100)
    lines: Optional[list[JournalEntryLineCreate]] = Field(None, min_length=2)

    @field_validator('lines')
    @classmethod
    def validate_balanced_entry(cls, v):
        if v is not None:
            total_debit = sum(line.debit_amount or 0 for line in v)
            total_credit = sum(line.credit_amount or 0 for line in v)
            if abs(total_debit - total_credit) > 0.01:
                raise ValueError(f'Entry is not balanced: debits={total_debit}, credits={total_credit}')
        return v


class JournalEntryVoid(BaseModel):
    """Schema for voiding journal entry"""
    void_reason: str = Field(..., min_length=1)


class JournalEntryResponse(JournalEntryBase):
    """Schema for journal entry response"""
    id: str
    entry_number: str
    status: JournalEntryStatusEnum
    total_debit: float
    total_credit: float
    posted_at: Optional[datetime] = None
    posted_by: Optional[str] = None
    voided_at: Optional[datetime] = None
    voided_by: Optional[str] = None
    void_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    created_by: str

    class Config:
        from_attributes = True


class JournalEntryDetailResponse(JournalEntryResponse):
    """Schema for journal entry with lines"""
    lines: list[JournalEntryLineResponse]


class JournalEntryListResponse(BaseModel):
    """Schema for list of journal entries"""
    items: list[JournalEntryResponse]
    total: int
    page: int = 1
    page_size: int = 50


# ============= PettyCash Schemas =============

class PettyCashFloatBase(BaseModel):
    """Base schema for petty cash float"""
    branch_id: str
    fund_source_id: str
    opening_balance: float = Field(..., gt=0)
    custodian_user_id: str
    is_active: bool = True


class PettyCashFloatCreate(PettyCashFloatBase):
    """Schema for creating petty cash float"""
    pass


class PettyCashFloatUpdate(BaseModel):
    """Schema for updating petty cash float"""
    custodian_user_id: Optional[str] = None
    is_active: Optional[bool] = None


class PettyCashFloatReconcile(BaseModel):
    """Schema for reconciling petty cash"""
    actual_balance: float = Field(..., ge=0)
    notes: Optional[str] = None


class PettyCashFloatResponse(PettyCashFloatBase):
    """Schema for petty cash float response"""
    id: str
    current_balance: float
    last_reconciled_at: Optional[datetime] = None
    last_reconciled_by: Optional[str] = None
    reconciled_balance: Optional[float] = None
    variance: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    created_by: str

    class Config:
        from_attributes = True


class PettyCashFloatListResponse(BaseModel):
    """Schema for list of petty cash floats"""
    items: list[PettyCashFloatResponse]
    total: int
    page: int = 1
    page_size: int = 50


# ============= PettyCashVoucher Schemas =============

class PettyCashVoucherBase(BaseModel):
    """Base schema for petty cash voucher"""
    petty_cash_float_id: str
    voucher_date: date
    voucher_type: VoucherTypeEnum
    amount: float = Field(..., gt=0)
    payee_payer: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    expense_category: Optional[str] = Field(None, max_length=100)
    gl_account_id: Optional[str] = None
    receipt_url: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None


class PettyCashVoucherCreate(PettyCashVoucherBase):
    """Schema for creating petty cash voucher"""
    pass


class PettyCashVoucherUpdate(BaseModel):
    """Schema for updating petty cash voucher (only DRAFT)"""
    voucher_date: Optional[date] = None
    voucher_type: Optional[VoucherTypeEnum] = None
    amount: Optional[float] = Field(None, gt=0)
    payee_payer: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1)
    expense_category: Optional[str] = Field(None, max_length=100)
    gl_account_id: Optional[str] = None
    receipt_url: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None


class PettyCashVoucherApprove(BaseModel):
    """Schema for approving voucher"""
    notes: Optional[str] = None


class PettyCashVoucherReject(BaseModel):
    """Schema for rejecting voucher"""
    rejection_reason: str = Field(..., min_length=1)


class PettyCashVoucherResponse(PettyCashVoucherBase):
    """Schema for petty cash voucher response"""
    id: str
    voucher_number: str
    status: VoucherStatusEnum
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejected_by: Optional[str] = None
    rejected_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    posted_to_journal: bool
    journal_entry_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    created_by: str

    class Config:
        from_attributes = True


class PettyCashVoucherListResponse(BaseModel):
    """Schema for list of petty cash vouchers"""
    items: list[PettyCashVoucherResponse]
    total: int
    page: int = 1
    page_size: int = 50


# ============= Accounting Reports Schemas =============

class AccountBalanceReport(BaseModel):
    """Schema for account balance report"""
    account_id: str
    account_code: str
    account_name: str
    debit_total: float
    credit_total: float
    balance: float


class TrialBalanceReport(BaseModel):
    """Schema for trial balance report"""
    as_of_date: date
    accounts: list[AccountBalanceReport]
    total_debits: float
    total_credits: float
    is_balanced: bool


class GeneralLedgerEntry(BaseModel):
    """Schema for general ledger entry"""
    date: date
    entry_number: str
    description: str
    debit_amount: Optional[float] = None
    credit_amount: Optional[float] = None
    balance: float


class GeneralLedgerReport(BaseModel):
    """Schema for general ledger report"""
    account_id: str
    account_code: str
    account_name: str
    from_date: date
    to_date: date
    opening_balance: float
    entries: list[GeneralLedgerEntry]
    closing_balance: float
