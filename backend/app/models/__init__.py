"""
SQLAlchemy models for the loan manager application.
"""

# Reference models
from .reference import Office, Staff, Holiday

# User models
from .user import User

# Loan models
from .client import Client
from .loan_product import LoanProduct
from .loan import Loan

# Loan Application models
from .branch import Branch
from .loan_application import LoanApplication, ApplicationStatus
from .loan_application_customer import LoanApplicationCustomer
from .loan_application_vehicle import LoanApplicationVehicle
from .loan_application_document import LoanApplicationDocument, DocumentType
from .loan_application_decision import LoanApplicationDecision, DecisionType
from .loan_application_audit import LoanApplicationAudit
from .loan_approval_threshold import LoanApprovalThreshold

# Vehicle Cost Ledger models
from .fund_source import FundSource
from .vehicle_cost_ledger import VehicleCostLedger, CostEventType
from .vehicle_cost_summary import VehicleCostSummary
from .bill_number_sequence import BillNumberSequence

# Bicycle models
from .bicycle import Bicycle, BicycleCondition, BicycleStatus
from .bicycle_application import BicycleApplication

# Company and lifecycle models
from .company import Company
from .stock_number import StockNumberSequence, StockNumberAssignment
from .bicycle_transfer import BicycleTransfer, TransferStatus
from .bicycle_expense import BicycleBranchExpense, ExpenseCategory
from .bicycle_sale import BicycleSale, SalePaymentMethod

# HR models
from .hr_leave import (
    LeaveType, LeaveApplication, LeaveBalance,
    LeaveStatus
)
from .leave_approval import (
    LeaveApproval, LeaveAuditLog, LeavePolicy,
    ApprovalDecision, ApproverRole
)
from .hr_attendance import (
    AttendanceRecord, AttendanceStatus
)
from .hr_bonus import (
    SalesTarget, PerformanceMetric, BonusRule, BonusTier,
    BonusPayment, TargetType, BonusRuleType, BonusPaymentStatus
)

# Workshop models
from .workshop_part import (
    PartCategory, PartStockBatch, PartStockMovement,
    StockMovementType
)
from .workshop_markup import (
    MarkupRule, MarkupTargetType, MarkupType
)
from .workshop_job import (
    RepairJob, RepairJobPart, RepairJobLabour, RepairJobOverhead,
    RepairJobType, RepairJobStatus
)

# Vendor models
from .vendor import Vendor, VendorCategory, VendorContact

# Customer KYC models
from .customer_guarantor import CustomerGuarantor
from .customer_employment import CustomerEmployment, EmploymentType, IncomeFrequency
from .customer_bank_account import CustomerBankAccount, AccountType, BankAccountStatus

# Commission models
from .commission_rule import CommissionRule, CommissionType, FormulaType, TierBasis

# Accounting models
from .chart_of_accounts import ChartOfAccounts, AccountCategory, AccountType as ChartAccountType
from .journal_entry import JournalEntry, JournalEntryLine, JournalEntryStatus, JournalEntryType
from .petty_cash import PettyCashFloat, PettyCashVoucher, VoucherType, VoucherStatus

# Utility models
from .idempotency import IdempotencyRecord

__all__ = [
    # Reference
    "Office",
    "Staff",
    "Holiday",
    # User
    "User",
    # Loan
    "Client",
    "LoanProduct",
    "Loan",
    # Loan Application
    "Branch",
    "LoanApplication",
    "ApplicationStatus",
    "LoanApplicationCustomer",
    "LoanApplicationVehicle",
    "LoanApplicationDocument",
    "DocumentType",
    "LoanApplicationDecision",
    "DecisionType",
    "LoanApplicationAudit",
    "LoanApprovalThreshold",
    # Vehicle Cost Ledger
    "FundSource",
    "VehicleCostLedger",
    "CostEventType",
    "VehicleCostSummary",
    "BillNumberSequence",
    # Bicycle
    "Bicycle",
    "BicycleCondition",
    "BicycleStatus",
    "BicycleApplication",
    # Company and lifecycle
    "Company",
    "StockNumberSequence",
    "StockNumberAssignment",
    "BicycleTransfer",
    "TransferStatus",
    "BicycleBranchExpense",
    "ExpenseCategory",
    "BicycleSale",
    "SalePaymentMethod",
    # HR
    "LeaveType",
    "LeaveApplication",
    "LeaveBalance",
    "LeaveStatus",
    "LeaveApproval",
    "LeaveAuditLog",
    "LeavePolicy",
    "ApprovalDecision",
    "ApproverRole",
    "AttendanceRecord",
    "AttendanceStatus",
    "SalesTarget",
    "PerformanceMetric",
    "BonusRule",
    "BonusTier",
    "BonusPayment",
    "TargetType",
    "BonusRuleType",
    "BonusPaymentStatus",
    # Workshop
    "PartCategory",
    "PartStockBatch",
    "PartStockMovement",
    "StockMovementType",
    "MarkupRule",
    "MarkupTargetType",
    "MarkupType",
    "RepairJob",
    "RepairJobPart",
    "RepairJobLabour",
    "RepairJobOverhead",
    "RepairJobType",
    "RepairJobStatus",
    # Vendor
    "Vendor",
    "VendorCategory",
    "VendorContact",
    # Customer KYC
    "CustomerGuarantor",
    "CustomerEmployment",
    "EmploymentType",
    "IncomeFrequency",
    "CustomerBankAccount",
    "AccountType",
    "BankAccountStatus",
    # Commission
    "CommissionRule",
    "CommissionType",
    "FormulaType",
    "TierBasis",
    # Accounting
    "ChartOfAccounts",
    "AccountCategory",
    "ChartAccountType",
    "JournalEntry",
    "JournalEntryLine",
    "JournalEntryStatus",
    "JournalEntryType",
    "PettyCashFloat",
    "PettyCashVoucher",
    "VoucherType",
    "VoucherStatus",
    # Utility
    "IdempotencyRecord",
]
