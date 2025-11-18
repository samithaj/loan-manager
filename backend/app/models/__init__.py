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
    # Utility
    "IdempotencyRecord",
]
