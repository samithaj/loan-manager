# Second-Hand Bike Lifecycle Management System - Implementation Guide

**Project**: Loan Manager - Bike Lifecycle Module
**Created**: 2025-11-18
**Status**: Planning → Implementation
**Target Completion**: 8 weeks

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Phase 1: Database Schema](#phase-1-database-schema)
4. [Phase 2: Backend Models](#phase-2-backend-models)
5. [Phase 3: Business Logic Services](#phase-3-business-logic-services)
6. [Phase 4: API Endpoints](#phase-4-api-endpoints)
7. [Phase 5: Frontend UI](#phase-5-frontend-ui)
8. [Phase 6: Reports & Analytics](#phase-6-reports--analytics)
9. [Phase 7: Data Migration](#phase-7-data-migration)
10. [Phase 8: Testing & Deployment](#phase-8-testing--deployment)
11. [Appendix: Technical References](#appendix-technical-references)

---

## Overview

This implementation guide provides step-by-step instructions to build a complete second-hand bike lifecycle management system that replaces:
- **November notebook** (acquisition log)
- **BRC/garage Excel** (repair cost per bike)
- **summery.xlsx** (purchased price, expenses, selling price, P&L)

### Key Features
- Multi-company (MA/IN) and multi-branch (19 branches) support
- Dynamic stock number generation (`MA/WW/ST/2066` format)
- Complete bike lifecycle: Purchase → Transfer → Repair → Sale → Commission
- Integration with existing workshop module (FIFO parts costing)
- Integration with HR bonus system for commissions
- Real-time P&L calculation

### Architecture Decisions
✅ **Stock Numbers**: Exact format `MA/WW/ST/2066` (separate from database IDs)
✅ **Bicycle Management**: Extend existing `bicycles` table
✅ **Organization**: Companies own branches
✅ **Commissions**: Integrate with existing HR bonus system

---

## Prerequisites

### Development Environment
- [ ] PostgreSQL 14+ running locally
- [ ] Python 3.11+ with virtual environment
- [ ] Node.js 18+ and npm/yarn
- [ ] Git repository access
- [ ] IDE/Editor (VS Code recommended)

### Existing System Knowledge
- [ ] Review existing `bicycles` table structure
- [ ] Understand `repair_jobs` workflow
- [ ] Familiarize with `part_stock_batches` FIFO logic
- [ ] Review `bonus_rules` and `bonus_payments` tables
- [ ] Understand existing RBAC permissions

### Required Access
- [ ] Database admin credentials
- [ ] Backend repository write access
- [ ] Frontend repository write access
- [ ] Test environment deployment access

---

## Phase 1: Database Schema

**Duration**: 3-4 days
**Files**: `database/migrations/0008_bike_lifecycle_system.sql`

### Task 1.1: Create Companies Table

```sql
-- Task: Create companies table
-- File: database/migrations/0008_bike_lifecycle_system.sql
-- Status: [ ] Not Started | [ ] In Progress | [ ] Completed

CREATE TABLE companies (
    id TEXT PRIMARY KEY,  -- 'MA', 'IN'
    name TEXT NOT NULL,   -- 'SK Management', 'SK Investment'
    district TEXT NOT NULL,  -- 'Monaragala', 'Badulla'
    contact_person TEXT,
    contact_phone TEXT,
    contact_email TEXT,
    address JSONB,  -- { street, city, postal_code }
    tax_id TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Seed data
INSERT INTO companies (id, name, district) VALUES
    ('MA', 'SK Management', 'Monaragala'),
    ('IN', 'SK Investment', 'Badulla');

-- Trigger for updated_at
CREATE TRIGGER update_companies_updated_at
    BEFORE UPDATE ON companies
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

**Checklist**:
- [ ] Create table with all fields
- [ ] Add seed data for MA and IN
- [ ] Add updated_at trigger
- [ ] Create index on `is_active`
- [ ] Test: Verify 2 companies inserted

---

### Task 1.2: Extend Offices Table (Add Company Relationship)

```sql
-- Task: Link branches to companies
-- Status: [ ] Not Started | [ ] In Progress | [ ] Completed

-- Add company_id to offices
ALTER TABLE offices
    ADD COLUMN company_id TEXT REFERENCES companies(id),
    ADD COLUMN is_repair_center BOOLEAN NOT NULL DEFAULT FALSE;

-- Create index
CREATE INDEX idx_offices_company_id ON offices(company_id);

-- Update existing branches (MANUAL DATA ENTRY REQUIRED)
-- Map each branch to correct company based on district
UPDATE offices SET company_id = 'MA' WHERE id IN ('WW', 'BK', 'BT', 'MO', 'HP', 'BW', ...);  -- Monaragala branches
UPDATE offices SET company_id = 'IN' WHERE id IN (...);  -- Badulla branches

-- Mark BRC as repair center
UPDATE offices SET is_repair_center = TRUE WHERE id = 'BRC';

-- Add NOT NULL constraint after data migration
ALTER TABLE offices ALTER COLUMN company_id SET NOT NULL;
```

**Checklist**:
- [ ] Add `company_id` column (nullable initially)
- [ ] Add `is_repair_center` column
- [ ] Create index on `company_id`
- [ ] Map all 19 branches to correct companies
- [ ] Mark repair centers (BRC)
- [ ] Set `company_id` to NOT NULL
- [ ] Test: Verify all offices have company_id

---

### Task 1.3: Create Stock Number Tables

```sql
-- Task: Stock number sequence and assignment tracking
-- Status: [ ] Not Started | [ ] In Progress | [ ] Completed

-- Sequence tracking per company/branch
CREATE TABLE stock_number_sequences (
    company_id TEXT NOT NULL REFERENCES companies(id),
    branch_id TEXT NOT NULL REFERENCES offices(id),
    current_number INTEGER NOT NULL DEFAULT 0,
    last_assigned_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (company_id, branch_id)
);

-- Initialize sequences for all company/branch combinations
INSERT INTO stock_number_sequences (company_id, branch_id, current_number)
SELECT c.id, o.id, 0
FROM companies c
CROSS JOIN offices o
WHERE c.is_active = TRUE AND o.is_active = TRUE;

-- Stock number assignment history
CREATE TABLE stock_number_assignments (
    id TEXT PRIMARY KEY,
    bicycle_id TEXT NOT NULL REFERENCES bicycles(id) ON DELETE CASCADE,
    company_id TEXT NOT NULL REFERENCES companies(id),
    branch_id TEXT NOT NULL REFERENCES offices(id),
    running_number INTEGER NOT NULL,
    full_stock_number TEXT NOT NULL,  -- e.g., 'MA/WW/ST/2066'
    assigned_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    released_date TIMESTAMPTZ,  -- NULL = currently assigned
    assignment_reason TEXT NOT NULL,  -- PURCHASE, TRANSFER_IN, RETURN_FROM_GARAGE
    previous_assignment_id TEXT REFERENCES stock_number_assignments(id),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_stock_assignments_bicycle ON stock_number_assignments(bicycle_id);
CREATE INDEX idx_stock_assignments_current ON stock_number_assignments(bicycle_id, released_date)
    WHERE released_date IS NULL;
CREATE UNIQUE INDEX idx_stock_assignments_unique_current ON stock_number_assignments(bicycle_id)
    WHERE released_date IS NULL;
CREATE UNIQUE INDEX idx_stock_number_unique ON stock_number_assignments(full_stock_number);

-- Triggers
CREATE TRIGGER update_stock_number_sequences_updated_at
    BEFORE UPDATE ON stock_number_sequences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_stock_number_assignments_updated_at
    BEFORE UPDATE ON stock_number_assignments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

**Checklist**:
- [ ] Create `stock_number_sequences` table
- [ ] Initialize sequences for all company/branch combos
- [ ] Create `stock_number_assignments` table
- [ ] Add all indexes (bicycle_id, current assignment, unique stock number)
- [ ] Add updated_at triggers
- [ ] Test: Generate sample stock number, verify uniqueness

---

### Task 1.4: Create Bicycle Transfer Table

```sql
-- Task: Branch transfer workflow
-- Status: [ ] Not Started | [ ] In Progress | [ ] Completed

CREATE TYPE transfer_status AS ENUM (
    'PENDING', 'APPROVED', 'IN_TRANSIT', 'COMPLETED', 'REJECTED', 'CANCELLED'
);

CREATE TABLE bicycle_transfers (
    id TEXT PRIMARY KEY,
    bicycle_id TEXT NOT NULL REFERENCES bicycles(id) ON DELETE CASCADE,
    from_branch_id TEXT NOT NULL REFERENCES offices(id),
    to_branch_id TEXT NOT NULL REFERENCES offices(id),
    from_stock_number TEXT,  -- Stock number before transfer
    to_stock_number TEXT,    -- Stock number after transfer (assigned on approval)
    status transfer_status NOT NULL DEFAULT 'PENDING',
    requested_by TEXT NOT NULL,  -- User ID or staff name
    requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    approved_by TEXT,
    approved_at TIMESTAMPTZ,
    completed_by TEXT,
    completed_at TIMESTAMPTZ,
    rejected_by TEXT,
    rejected_at TIMESTAMPTZ,
    rejection_reason TEXT,
    transfer_reason TEXT,  -- Why transfer is needed
    reference_doc_number TEXT,  -- Physical transfer note number
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT different_branches CHECK (from_branch_id != to_branch_id)
);

-- Indexes
CREATE INDEX idx_transfers_bicycle ON bicycle_transfers(bicycle_id);
CREATE INDEX idx_transfers_status ON bicycle_transfers(status);
CREATE INDEX idx_transfers_from_branch ON bicycle_transfers(from_branch_id);
CREATE INDEX idx_transfers_to_branch ON bicycle_transfers(to_branch_id);

-- Trigger
CREATE TRIGGER update_bicycle_transfers_updated_at
    BEFORE UPDATE ON bicycle_transfers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

**Checklist**:
- [ ] Create `transfer_status` enum
- [ ] Create `bicycle_transfers` table
- [ ] Add CHECK constraint (from != to)
- [ ] Create all indexes
- [ ] Add updated_at trigger
- [ ] Test: Create sample transfer record

---

### Task 1.5: Create Bicycle Branch Expenses Table

```sql
-- Task: Track branch-level expenses per bike
-- Status: [ ] Not Started | [ ] In Progress | [ ] Completed

CREATE TYPE expense_category AS ENUM (
    'TRANSPORT', 'MINOR_REPAIR', 'LICENSE_RENEWAL', 'INSURANCE',
    'CLEANING', 'DOCUMENTATION', 'STORAGE', 'OTHER'
);

CREATE TABLE bicycle_branch_expenses (
    id TEXT PRIMARY KEY,
    bicycle_id TEXT NOT NULL REFERENCES bicycles(id) ON DELETE CASCADE,
    branch_id TEXT NOT NULL REFERENCES offices(id),
    expense_date DATE NOT NULL DEFAULT CURRENT_DATE,
    description TEXT NOT NULL,
    category expense_category NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    invoice_number TEXT,
    vendor_name TEXT,
    recorded_by TEXT NOT NULL,  -- User ID or staff name
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT positive_amount CHECK (amount >= 0)
);

-- Indexes
CREATE INDEX idx_branch_expenses_bicycle ON bicycle_branch_expenses(bicycle_id);
CREATE INDEX idx_branch_expenses_branch ON bicycle_branch_expenses(branch_id);
CREATE INDEX idx_branch_expenses_date ON bicycle_branch_expenses(expense_date);

-- Trigger
CREATE TRIGGER update_bicycle_branch_expenses_updated_at
    BEFORE UPDATE ON bicycle_branch_expenses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

**Checklist**:
- [ ] Create `expense_category` enum
- [ ] Create `bicycle_branch_expenses` table
- [ ] Add CHECK constraint (amount >= 0)
- [ ] Create all indexes
- [ ] Add updated_at trigger
- [ ] Test: Insert sample expense

---

### Task 1.6: Create Bicycle Sales Table

```sql
-- Task: Record bike sale transactions
-- Status: [ ] Not Started | [ ] In Progress | [ ] Completed

CREATE TYPE sale_payment_method AS ENUM (
    'CASH', 'FINANCE', 'TRADE_IN', 'BANK_TRANSFER', 'MIXED'
);

CREATE TABLE bicycle_sales (
    id TEXT PRIMARY KEY,
    bicycle_id TEXT NOT NULL REFERENCES bicycles(id) ON DELETE RESTRICT,
    selling_branch_id TEXT NOT NULL REFERENCES offices(id),
    selling_company_id TEXT NOT NULL REFERENCES companies(id),
    stock_number_at_sale TEXT,  -- Stock number when sold
    sale_date DATE NOT NULL DEFAULT CURRENT_DATE,
    selling_price DECIMAL(12, 2) NOT NULL,
    payment_method sale_payment_method NOT NULL,

    -- Customer details
    customer_name TEXT,
    customer_phone TEXT,
    customer_email TEXT,
    customer_address TEXT,
    customer_nic TEXT,

    -- Trade-in details (if applicable)
    trade_in_bicycle_id TEXT REFERENCES bicycles(id),
    trade_in_value DECIMAL(12, 2),

    -- Finance details (if applicable)
    finance_institution TEXT,
    down_payment DECIMAL(12, 2),
    financed_amount DECIMAL(12, 2),

    -- Sale details
    sold_by TEXT NOT NULL,  -- Staff ID or name
    sale_invoice_number TEXT,
    delivery_date DATE,
    warranty_months INTEGER,

    -- Computed fields (updated by trigger)
    total_cost DECIMAL(12, 2),  -- Purchase + branch expenses + garage
    profit_or_loss DECIMAL(12, 2),  -- Selling price - total cost

    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT positive_selling_price CHECK (selling_price > 0),
    CONSTRAINT valid_trade_in CHECK (
        (payment_method = 'TRADE_IN' AND trade_in_bicycle_id IS NOT NULL) OR
        (payment_method != 'TRADE_IN' AND trade_in_bicycle_id IS NULL)
    )
);

-- Indexes
CREATE UNIQUE INDEX idx_sales_bicycle ON bicycle_sales(bicycle_id);  -- One sale per bike
CREATE INDEX idx_sales_branch ON bicycle_sales(selling_branch_id);
CREATE INDEX idx_sales_company ON bicycle_sales(selling_company_id);
CREATE INDEX idx_sales_date ON bicycle_sales(sale_date);
CREATE INDEX idx_sales_customer_phone ON bicycle_sales(customer_phone);

-- Trigger
CREATE TRIGGER update_bicycle_sales_updated_at
    BEFORE UPDATE ON bicycle_sales
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

**Checklist**:
- [ ] Create `sale_payment_method` enum
- [ ] Create `bicycle_sales` table
- [ ] Add CHECK constraints (price > 0, trade-in validation)
- [ ] Create all indexes (including UNIQUE on bicycle_id)
- [ ] Add updated_at trigger
- [ ] Test: Insert sample sale

---

### Task 1.7: Extend Bicycles Table

```sql
-- Task: Add bike lifecycle fields to existing bicycles table
-- Status: [ ] Not Started | [ ] In Progress | [ ] Completed

-- Add new fields
ALTER TABLE bicycles
    ADD COLUMN company_id TEXT REFERENCES companies(id),
    ADD COLUMN business_model TEXT NOT NULL DEFAULT 'HIRE_PURCHASE',  -- HIRE_PURCHASE, DIRECT_SALE, STOCK
    ADD COLUMN current_stock_number TEXT,  -- Denormalized for quick lookup
    ADD COLUMN current_branch_id TEXT REFERENCES offices(id),  -- Override branch_id for clarity

    -- Procurement details (from November notebook)
    ADD COLUMN procurement_date DATE,
    ADD COLUMN procurement_source TEXT,  -- CUSTOMER, AUCTION, DEALER, TRADE_IN
    ADD COLUMN bought_method TEXT,  -- CASH, LOAN_CLOSED, PREVIOUS_BIKE, AUCTION
    ADD COLUMN hand_amount DECIMAL(12, 2),  -- From "Hand" column
    ADD COLUMN settlement_amount DECIMAL(12, 2),  -- From "Settlement" column
    ADD COLUMN payment_branch_id TEXT REFERENCES offices(id),  -- Where payment was processed
    ADD COLUMN cr_location TEXT,  -- Where CR/documents are held
    ADD COLUMN buyer_employee_id TEXT REFERENCES staff(id),  -- "Bought person"

    -- Control flags (from notebook)
    ADD COLUMN first_od TEXT,  -- First owner details
    ADD COLUMN ldate DATE,  -- License/loan date
    ADD COLUMN sk_flag BOOLEAN DEFAULT FALSE,
    ADD COLUMN ls_flag BOOLEAN DEFAULT FALSE,
    ADD COLUMN caller TEXT,
    ADD COLUMN house_use BOOLEAN DEFAULT FALSE,

    -- Cost tracking (computed fields)
    ADD COLUMN total_branch_expenses DECIMAL(12, 2) DEFAULT 0,  -- Sum of branch expenses
    ADD COLUMN total_expenses DECIMAL(12, 2) GENERATED ALWAYS AS (
        COALESCE(base_purchase_price, 0) +
        COALESCE(total_repair_cost, 0) +
        COALESCE(total_branch_expenses, 0)
    ) STORED,

    -- Sale tracking
    ADD COLUMN sold_date DATE,
    ADD COLUMN selling_price DECIMAL(12, 2),
    ADD COLUMN profit_or_loss DECIMAL(12, 2) GENERATED ALWAYS AS (
        CASE
            WHEN selling_price IS NOT NULL
            THEN selling_price - (
                COALESCE(base_purchase_price, 0) +
                COALESCE(total_repair_cost, 0) +
                COALESCE(total_branch_expenses, 0)
            )
            ELSE NULL
        END
    ) STORED;

-- Update existing status enum to include new values
ALTER TYPE bicycle_status RENAME TO bicycle_status_old;

CREATE TYPE bicycle_status AS ENUM (
    'AVAILABLE', 'RESERVED', 'SOLD', 'MAINTENANCE',
    'IN_STOCK', 'ALLOCATED', 'IN_TRANSIT', 'WRITTEN_OFF'
);

ALTER TABLE bicycles
    ALTER COLUMN status TYPE bicycle_status USING status::text::bicycle_status;

DROP TYPE bicycle_status_old;

-- Add new indexes
CREATE INDEX idx_bicycles_company ON bicycles(company_id);
CREATE INDEX idx_bicycles_business_model ON bicycles(business_model);
CREATE INDEX idx_bicycles_current_stock_number ON bicycles(current_stock_number);
CREATE INDEX idx_bicycles_current_branch ON bicycles(current_branch_id);
CREATE INDEX idx_bicycles_procurement_date ON bicycles(procurement_date);
CREATE INDEX idx_bicycles_sold_date ON bicycles(sold_date);

-- Add constraints
ALTER TABLE bicycles
    ADD CONSTRAINT valid_business_model
        CHECK (business_model IN ('HIRE_PURCHASE', 'DIRECT_SALE', 'STOCK')),
    ADD CONSTRAINT valid_procurement_source
        CHECK (procurement_source IN ('CUSTOMER', 'AUCTION', 'DEALER', 'TRADE_IN', 'OTHER'));
```

**Checklist**:
- [ ] Add company_id column
- [ ] Add business_model column with CHECK constraint
- [ ] Add current_stock_number (denormalized cache)
- [ ] Add all procurement fields (from notebook)
- [ ] Add control flags (first_od, ldate, sk_flag, etc.)
- [ ] Add cost tracking fields (total_branch_expenses)
- [ ] Add generated columns (total_expenses, profit_or_loss)
- [ ] Extend bicycle_status enum
- [ ] Create all new indexes
- [ ] Test: Insert sample bike with all new fields

---

### Task 1.8: Extend Repair Jobs Table

```sql
-- Task: Add job category to repair jobs
-- Status: [ ] Not Started | [ ] In Progress | [ ] Completed

ALTER TABLE repair_jobs
    ADD COLUMN job_category TEXT DEFAULT 'CUSTOMER_REPAIR';

ALTER TABLE repair_jobs
    ADD CONSTRAINT valid_job_category
        CHECK (job_category IN ('PRE_SALE_PREP', 'CUSTOMER_REPAIR', 'WARRANTY', 'MAINTENANCE'));

CREATE INDEX idx_repair_jobs_category ON repair_jobs(job_category);

-- Update existing FULL_OVERHAUL_BEFORE_SALE jobs
UPDATE repair_jobs
SET job_category = 'PRE_SALE_PREP'
WHERE job_type = 'FULL_OVERHAUL_BEFORE_SALE';
```

**Checklist**:
- [ ] Add `job_category` column
- [ ] Add CHECK constraint
- [ ] Create index
- [ ] Update existing records
- [ ] Test: Verify pre-sale jobs marked correctly

---

### Task 1.9: Extend Bonus System for Commissions

```sql
-- Task: Extend HR bonus system for bike sale commissions
-- Status: [ ] Not Started | [ ] In Progress | [ ] Completed

-- Add bike-specific fields to bonus_rules
ALTER TABLE bonus_rules
    ADD COLUMN applies_to_bike_sales BOOLEAN DEFAULT FALSE,
    ADD COLUMN commission_base TEXT DEFAULT 'PROFIT',  -- PROFIT, SALE_PRICE
    ADD COLUMN buyer_branch_percent DECIMAL(5, 2),  -- Percentage for purchasing branch
    ADD COLUMN seller_branch_percent DECIMAL(5, 2);  -- Percentage for selling branch

ALTER TABLE bonus_rules
    ADD CONSTRAINT valid_commission_base
        CHECK (commission_base IN ('PROFIT', 'SALE_PRICE')),
    ADD CONSTRAINT valid_commission_percentages
        CHECK (
            (applies_to_bike_sales = FALSE) OR
            (buyer_branch_percent >= 0 AND seller_branch_percent >= 0 AND
             buyer_branch_percent + seller_branch_percent = 100)
        );

-- Add bike sale reference to bonus_payments
ALTER TABLE bonus_payments
    ADD COLUMN bicycle_sale_id TEXT REFERENCES bicycle_sales(id),
    ADD COLUMN commission_type TEXT;  -- BUYER, SELLER

ALTER TABLE bonus_payments
    ADD CONSTRAINT valid_commission_type
        CHECK (commission_type IN ('BUYER', 'SELLER', NULL));

CREATE INDEX idx_bonus_payments_bike_sale ON bonus_payments(bicycle_sale_id);

-- Insert default bike commission rule
INSERT INTO bonus_rules (
    id, name, rule_type, applies_to_bike_sales, commission_base,
    buyer_branch_percent, seller_branch_percent,
    is_active, effective_from
) VALUES (
    'BIKE-COMM-001',
    'Default Bike Sale Commission',
    'BIKE_SALE',
    TRUE,
    'PROFIT',
    40.00,  -- 40% to buyer branch
    60.00,  -- 60% to seller branch
    TRUE,
    CURRENT_DATE
);
```

**Checklist**:
- [ ] Add bike sale fields to `bonus_rules`
- [ ] Add percentage validation constraint
- [ ] Add `bicycle_sale_id` to `bonus_payments`
- [ ] Add `commission_type` field
- [ ] Create index on bicycle_sale_id
- [ ] Insert default commission rule (40/60 split)
- [ ] Test: Verify constraint works (percentages must sum to 100)

---

### Task 1.10: Create Database Views

```sql
-- Task: Create materialized views for reporting
-- Status: [ ] Not Started | [ ] In Progress | [ ] Completed

-- View 1: Bike Cost Summary (like summery.xlsx)
CREATE MATERIALIZED VIEW v_bike_cost_summary AS
SELECT
    b.id AS bicycle_id,
    b.license_plate AS bike_no,
    b.current_branch_id AS branch_id,
    o.name AS branch_name,
    b.current_stock_number,
    b.model_name,
    b.procurement_date AS received_date,
    b.base_purchase_price AS purchased_price,
    COALESCE(exp.total_branch_expenses, 0) AS branch_expenses,
    COALESCE(b.total_repair_cost, 0) AS garage_expenses,
    b.total_expenses,
    b.sold_date AS released_date,
    b.selling_price,
    b.profit_or_loss,
    CASE
        WHEN b.status = 'SOLD' THEN 'SOLD'
        WHEN b.status IN ('IN_STOCK', 'AVAILABLE') THEN 'IN_STOCK'
        WHEN b.status = 'MAINTENANCE' THEN 'IN_GARAGE'
        ELSE 'OTHER'
    END AS stock_status
FROM bicycles b
LEFT JOIN offices o ON b.current_branch_id = o.id
LEFT JOIN (
    SELECT bicycle_id, SUM(amount) AS total_branch_expenses
    FROM bicycle_branch_expenses
    GROUP BY bicycle_id
) exp ON b.id = exp.bicycle_id
WHERE b.business_model IN ('DIRECT_SALE', 'STOCK');

CREATE UNIQUE INDEX idx_v_bike_cost_summary_id ON v_bike_cost_summary(bicycle_id);
CREATE INDEX idx_v_bike_cost_summary_branch ON v_bike_cost_summary(branch_id);
CREATE INDEX idx_v_bike_cost_summary_status ON v_bike_cost_summary(stock_status);

-- View 2: Branch Stock Status
CREATE MATERIALIZED VIEW v_branch_stock_status AS
SELECT
    o.id AS branch_id,
    o.name AS branch_name,
    c.id AS company_id,
    c.name AS company_name,
    b.status,
    COUNT(*) AS bike_count,
    SUM(b.base_purchase_price) AS total_purchase_value,
    SUM(b.total_expenses) AS total_cost_value,
    AVG(b.total_expenses) AS avg_bike_cost
FROM bicycles b
JOIN offices o ON b.current_branch_id = o.id
JOIN companies c ON o.company_id = c.id
WHERE b.business_model IN ('DIRECT_SALE', 'STOCK')
GROUP BY o.id, o.name, c.id, c.name, b.status;

CREATE INDEX idx_v_branch_stock_status_branch ON v_branch_stock_status(branch_id);
CREATE INDEX idx_v_branch_stock_status_company ON v_branch_stock_status(company_id);

-- View 3: Commission Summary
CREATE MATERIALIZED VIEW v_commission_summary AS
SELECT
    bp.period_start,
    bp.period_end,
    bp.branch_id,
    o.name AS branch_name,
    bp.commission_type,
    COUNT(DISTINCT bp.bicycle_sale_id) AS sale_count,
    SUM(bp.amount) AS total_commission
FROM bonus_payments bp
JOIN offices o ON bp.branch_id = o.id
WHERE bp.bicycle_sale_id IS NOT NULL
GROUP BY bp.period_start, bp.period_end, bp.branch_id, o.name, bp.commission_type;

CREATE INDEX idx_v_commission_summary_branch ON v_commission_summary(branch_id);
CREATE INDEX idx_v_commission_summary_period ON v_commission_summary(period_start, period_end);

-- Refresh function (to be called after transactions)
CREATE OR REPLACE FUNCTION refresh_bike_materialized_views()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY v_bike_cost_summary;
    REFRESH MATERIALIZED VIEW CONCURRENTLY v_branch_stock_status;
    REFRESH MATERIALIZED VIEW CONCURRENTLY v_commission_summary;
END;
$$ LANGUAGE plpgsql;
```

**Checklist**:
- [ ] Create `v_bike_cost_summary` materialized view
- [ ] Create `v_branch_stock_status` materialized view
- [ ] Create `v_commission_summary` materialized view
- [ ] Create indexes on all views
- [ ] Create refresh function
- [ ] Test: Run refresh, verify data accuracy
- [ ] Schedule nightly refresh (cron or app-level)

---

### Task 1.11: Migration Testing & Validation

**Checklist**:
- [ ] Run migration script on dev database
- [ ] Verify all tables created successfully
- [ ] Check all indexes are in place
- [ ] Validate foreign key constraints
- [ ] Test triggers (insert/update records, check updated_at)
- [ ] Verify enums created correctly
- [ ] Check generated columns calculate properly
- [ ] Run `psql -d loan_manager -c "\d+ bicycles"` - verify structure
- [ ] Run `psql -d loan_manager -c "\dt"` - verify all new tables
- [ ] Document any issues in migration log

---

## Phase 2: Backend Models

**Duration**: 4-5 days
**Files**: `backend/app/models/*.py`

### Task 2.1: Create Company Model

```python
# File: backend/app/models/company.py
# Status: [ ] Not Started | [ ] In Progress | [ ] Completed

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base

if TYPE_CHECKING:
    from .office import Office
    from .bicycle import Bicycle

class Company(Base):
    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    district: Mapped[str] = mapped_column(String, nullable=False)
    contact_person: Mapped[Optional[str]] = mapped_column(String)
    contact_phone: Mapped[Optional[str]] = mapped_column(String)
    contact_email: Mapped[Optional[str]] = mapped_column(String)
    address: Mapped[Optional[dict]] = mapped_column(JSONB)
    tax_id: Mapped[Optional[str]] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default="NOW()"
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default="NOW()"
    )

    # Relationships
    offices: Mapped[list["Office"]] = relationship("Office", back_populates="company")
    bicycles: Mapped[list["Bicycle"]] = relationship("Bicycle", back_populates="company")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "district": self.district,
            "contact_person": self.contact_person,
            "contact_phone": self.contact_phone,
            "contact_email": self.contact_email,
            "address": self.address,
            "tax_id": self.tax_id,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
```

**Checklist**:
- [ ] Create `company.py` file
- [ ] Define Company model with all fields
- [ ] Add relationships to Office and Bicycle
- [ ] Implement `to_dict()` method
- [ ] Test: Import in Python REPL, verify no errors
- [ ] Test: Query companies, verify relationships work

---

### Task 2.2: Update Office Model

```python
# File: backend/app/models/office.py (MODIFY EXISTING)
# Status: [ ] Not Started | [ ] In Progress | [ ] Completed

# Add to existing Office class:

from typing import Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from .company import Company

class Office(Base):
    # ... existing fields ...

    # NEW FIELDS
    company_id: Mapped[str] = mapped_column(String, ForeignKey("companies.id"), nullable=False)
    is_repair_center: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # NEW RELATIONSHIP
    company: Mapped["Company"] = relationship("Company", back_populates="offices")

    # Update to_dict() to include new fields
    def to_dict(self) -> dict:
        result = {
            # ... existing fields ...
            "company_id": self.company_id,
            "is_repair_center": self.is_repair_center,
        }
        return result
```

**Checklist**:
- [ ] Add `company_id` field with FK
- [ ] Add `is_repair_center` field
- [ ] Add `company` relationship
- [ ] Update `to_dict()` method
- [ ] Update imports (TYPE_CHECKING)
- [ ] Test: Query office with company, verify relationship

---

### Task 2.3: Create Stock Number Models

```python
# File: backend/app/models/stock_number.py
# Status: [ ] Not Started | [ ] In Progress | [ ] Completed

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, TIMESTAMP, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base

class StockNumberSequence(Base):
    __tablename__ = "stock_number_sequences"

    company_id: Mapped[str] = mapped_column(
        String, ForeignKey("companies.id"), primary_key=True
    )
    branch_id: Mapped[str] = mapped_column(
        String, ForeignKey("offices.id"), primary_key=True
    )
    current_number: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_assigned_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default="NOW()"
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default="NOW()"
    )

    def to_dict(self) -> dict:
        return {
            "company_id": self.company_id,
            "branch_id": self.branch_id,
            "current_number": self.current_number,
            "last_assigned_at": self.last_assigned_at.isoformat() if self.last_assigned_at else None,
        }


class StockNumberAssignment(Base):
    __tablename__ = "stock_number_assignments"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    bicycle_id: Mapped[str] = mapped_column(
        String, ForeignKey("bicycles.id", ondelete="CASCADE"), nullable=False
    )
    company_id: Mapped[str] = mapped_column(
        String, ForeignKey("companies.id"), nullable=False
    )
    branch_id: Mapped[str] = mapped_column(
        String, ForeignKey("offices.id"), nullable=False
    )
    running_number: Mapped[int] = mapped_column(Integer, nullable=False)
    full_stock_number: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    assigned_date: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default="NOW()", nullable=False
    )
    released_date: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    assignment_reason: Mapped[str] = mapped_column(String, nullable=False)
    previous_assignment_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("stock_number_assignments.id")
    )
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default="NOW()"
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default="NOW()"
    )

    # Relationships
    bicycle: Mapped["Bicycle"] = relationship("Bicycle", back_populates="stock_assignments")
    company: Mapped["Company"] = relationship("Company")
    branch: Mapped["Office"] = relationship("Office")
    previous_assignment: Mapped[Optional["StockNumberAssignment"]] = relationship(
        "StockNumberAssignment", remote_side=[id]
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "bicycle_id": self.bicycle_id,
            "company_id": self.company_id,
            "branch_id": self.branch_id,
            "running_number": self.running_number,
            "full_stock_number": self.full_stock_number,
            "assigned_date": self.assigned_date.isoformat(),
            "released_date": self.released_date.isoformat() if self.released_date else None,
            "assignment_reason": self.assignment_reason,
            "previous_assignment_id": self.previous_assignment_id,
            "notes": self.notes,
        }

    @property
    def is_current(self) -> bool:
        """Check if this is the current assignment (not released)"""
        return self.released_date is None
```

**Checklist**:
- [ ] Create `stock_number.py` file
- [ ] Define `StockNumberSequence` model (composite PK)
- [ ] Define `StockNumberAssignment` model
- [ ] Add all relationships (bicycle, company, branch, previous_assignment)
- [ ] Implement `to_dict()` methods
- [ ] Add `is_current` property
- [ ] Test: Create sample assignment, verify relationships

---

### Task 2.4: Create Bicycle Transfer Model

```python
# File: backend/app/models/bicycle_transfer.py
# Status: [ ] Not Started | [ ] In Progress | [ ] Completed

from datetime import datetime
from typing import Optional
from enum import Enum
from sqlalchemy import String, TIMESTAMP, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base

class TransferStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    IN_TRANSIT = "IN_TRANSIT"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"

class BicycleTransfer(Base):
    __tablename__ = "bicycle_transfers"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    bicycle_id: Mapped[str] = mapped_column(
        String, ForeignKey("bicycles.id", ondelete="CASCADE"), nullable=False
    )
    from_branch_id: Mapped[str] = mapped_column(
        String, ForeignKey("offices.id"), nullable=False
    )
    to_branch_id: Mapped[str] = mapped_column(
        String, ForeignKey("offices.id"), nullable=False
    )
    from_stock_number: Mapped[Optional[str]] = mapped_column(String)
    to_stock_number: Mapped[Optional[str]] = mapped_column(String)
    status: Mapped[TransferStatus] = mapped_column(
        SQLEnum(TransferStatus), default=TransferStatus.PENDING, nullable=False
    )

    # Request details
    requested_by: Mapped[str] = mapped_column(String, nullable=False)
    requested_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default="NOW()", nullable=False
    )

    # Approval details
    approved_by: Mapped[Optional[str]] = mapped_column(String)
    approved_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))

    # Completion details
    completed_by: Mapped[Optional[str]] = mapped_column(String)
    completed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))

    # Rejection details
    rejected_by: Mapped[Optional[str]] = mapped_column(String)
    rejected_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text)

    # Additional info
    transfer_reason: Mapped[Optional[str]] = mapped_column(Text)
    reference_doc_number: Mapped[Optional[str]] = mapped_column(String)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default="NOW()"
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default="NOW()"
    )

    # Relationships
    bicycle: Mapped["Bicycle"] = relationship("Bicycle", back_populates="transfers")
    from_branch: Mapped["Office"] = relationship("Office", foreign_keys=[from_branch_id])
    to_branch: Mapped["Office"] = relationship("Office", foreign_keys=[to_branch_id])

    def approve(self, approved_by: str) -> None:
        """Approve the transfer"""
        if self.status != TransferStatus.PENDING:
            raise ValueError(f"Cannot approve transfer in status {self.status}")
        self.status = TransferStatus.APPROVED
        self.approved_by = approved_by
        self.approved_at = datetime.now()

    def complete(self, completed_by: str) -> None:
        """Mark transfer as completed"""
        if self.status != TransferStatus.APPROVED:
            raise ValueError(f"Cannot complete transfer in status {self.status}")
        self.status = TransferStatus.COMPLETED
        self.completed_by = completed_by
        self.completed_at = datetime.now()

    def reject(self, rejected_by: str, reason: str) -> None:
        """Reject the transfer"""
        if self.status not in [TransferStatus.PENDING, TransferStatus.APPROVED]:
            raise ValueError(f"Cannot reject transfer in status {self.status}")
        self.status = TransferStatus.REJECTED
        self.rejected_by = rejected_by
        self.rejected_at = datetime.now()
        self.rejection_reason = reason

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "bicycle_id": self.bicycle_id,
            "from_branch_id": self.from_branch_id,
            "to_branch_id": self.to_branch_id,
            "from_stock_number": self.from_stock_number,
            "to_stock_number": self.to_stock_number,
            "status": self.status.value,
            "requested_by": self.requested_by,
            "requested_at": self.requested_at.isoformat(),
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "completed_by": self.completed_by,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "rejected_by": self.rejected_by,
            "rejected_at": self.rejected_at.isoformat() if self.rejected_at else None,
            "rejection_reason": self.rejection_reason,
            "transfer_reason": self.transfer_reason,
            "reference_doc_number": self.reference_doc_number,
            "notes": self.notes,
        }
```

**Checklist**:
- [ ] Create `bicycle_transfer.py` file
- [ ] Define `TransferStatus` enum
- [ ] Define `BicycleTransfer` model
- [ ] Add all status tracking fields
- [ ] Add relationships (bicycle, from_branch, to_branch)
- [ ] Implement state change methods (approve, complete, reject)
- [ ] Implement `to_dict()` method
- [ ] Test: Create transfer, test state transitions

---

### Task 2.5: Create Bicycle Branch Expense Model

```python
# File: backend/app/models/bicycle_expense.py
# Status: [ ] Not Started | [ ] In Progress | [ ] Completed

from datetime import datetime, date
from typing import Optional
from enum import Enum
from decimal import Decimal
from sqlalchemy import String, TIMESTAMP, Date, ForeignKey, Text, Numeric, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base

class ExpenseCategory(str, Enum):
    TRANSPORT = "TRANSPORT"
    MINOR_REPAIR = "MINOR_REPAIR"
    LICENSE_RENEWAL = "LICENSE_RENEWAL"
    INSURANCE = "INSURANCE"
    CLEANING = "CLEANING"
    DOCUMENTATION = "DOCUMENTATION"
    STORAGE = "STORAGE"
    OTHER = "OTHER"

class BicycleBranchExpense(Base):
    __tablename__ = "bicycle_branch_expenses"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    bicycle_id: Mapped[str] = mapped_column(
        String, ForeignKey("bicycles.id", ondelete="CASCADE"), nullable=False
    )
    branch_id: Mapped[str] = mapped_column(
        String, ForeignKey("offices.id"), nullable=False
    )
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[ExpenseCategory] = mapped_column(
        SQLEnum(ExpenseCategory), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    invoice_number: Mapped[Optional[str]] = mapped_column(String)
    vendor_name: Mapped[Optional[str]] = mapped_column(String)
    recorded_by: Mapped[str] = mapped_column(String, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default="NOW()"
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default="NOW()"
    )

    # Relationships
    bicycle: Mapped["Bicycle"] = relationship("Bicycle", back_populates="branch_expenses")
    branch: Mapped["Office"] = relationship("Office")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "bicycle_id": self.bicycle_id,
            "branch_id": self.branch_id,
            "expense_date": self.expense_date.isoformat(),
            "description": self.description,
            "category": self.category.value,
            "amount": float(self.amount),
            "invoice_number": self.invoice_number,
            "vendor_name": self.vendor_name,
            "recorded_by": self.recorded_by,
            "notes": self.notes,
        }
```

**Checklist**:
- [ ] Create `bicycle_expense.py` file
- [ ] Define `ExpenseCategory` enum
- [ ] Define `BicycleBranchExpense` model
- [ ] Add all fields with proper types (Decimal for amount)
- [ ] Add relationships (bicycle, branch)
- [ ] Implement `to_dict()` method
- [ ] Test: Create expense, verify amount precision

---

### Task 2.6: Create Bicycle Sale Model

```python
# File: backend/app/models/bicycle_sale.py
# Status: [ ] Not Started | [ ] In Progress | [ ] Completed

from datetime import datetime, date
from typing import Optional
from enum import Enum
from decimal import Decimal
from sqlalchemy import (
    String, TIMESTAMP, Date, ForeignKey, Text, Numeric,
    Integer, Enum as SQLEnum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base

class SalePaymentMethod(str, Enum):
    CASH = "CASH"
    FINANCE = "FINANCE"
    TRADE_IN = "TRADE_IN"
    BANK_TRANSFER = "BANK_TRANSFER"
    MIXED = "MIXED"

class BicycleSale(Base):
    __tablename__ = "bicycle_sales"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    bicycle_id: Mapped[str] = mapped_column(
        String, ForeignKey("bicycles.id", ondelete="RESTRICT"), nullable=False, unique=True
    )
    selling_branch_id: Mapped[str] = mapped_column(
        String, ForeignKey("offices.id"), nullable=False
    )
    selling_company_id: Mapped[str] = mapped_column(
        String, ForeignKey("companies.id"), nullable=False
    )
    stock_number_at_sale: Mapped[Optional[str]] = mapped_column(String)
    sale_date: Mapped[date] = mapped_column(Date, nullable=False)
    selling_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    payment_method: Mapped[SalePaymentMethod] = mapped_column(
        SQLEnum(SalePaymentMethod), nullable=False
    )

    # Customer details
    customer_name: Mapped[Optional[str]] = mapped_column(String)
    customer_phone: Mapped[Optional[str]] = mapped_column(String)
    customer_email: Mapped[Optional[str]] = mapped_column(String)
    customer_address: Mapped[Optional[str]] = mapped_column(Text)
    customer_nic: Mapped[Optional[str]] = mapped_column(String)

    # Trade-in details
    trade_in_bicycle_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("bicycles.id")
    )
    trade_in_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))

    # Finance details
    finance_institution: Mapped[Optional[str]] = mapped_column(String)
    down_payment: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    financed_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))

    # Sale details
    sold_by: Mapped[str] = mapped_column(String, nullable=False)
    sale_invoice_number: Mapped[Optional[str]] = mapped_column(String)
    delivery_date: Mapped[Optional[date]] = mapped_column(Date)
    warranty_months: Mapped[Optional[int]] = mapped_column(Integer)

    # Computed fields (updated via trigger or app logic)
    total_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    profit_or_loss: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))

    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default="NOW()"
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default="NOW()"
    )

    # Relationships
    bicycle: Mapped["Bicycle"] = relationship(
        "Bicycle", back_populates="sale", foreign_keys=[bicycle_id]
    )
    selling_branch: Mapped["Office"] = relationship("Office")
    selling_company: Mapped["Company"] = relationship("Company")
    trade_in_bicycle: Mapped[Optional["Bicycle"]] = relationship(
        "Bicycle", foreign_keys=[trade_in_bicycle_id]
    )
    commissions: Mapped[list["BonusPayment"]] = relationship(
        "BonusPayment", back_populates="bicycle_sale"
    )

    def calculate_profit(self) -> Decimal:
        """Calculate profit or loss for this sale"""
        if not self.total_cost or not self.selling_price:
            return Decimal(0)
        return self.selling_price - self.total_cost

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "bicycle_id": self.bicycle_id,
            "selling_branch_id": self.selling_branch_id,
            "selling_company_id": self.selling_company_id,
            "stock_number_at_sale": self.stock_number_at_sale,
            "sale_date": self.sale_date.isoformat(),
            "selling_price": float(self.selling_price),
            "payment_method": self.payment_method.value,
            "customer_name": self.customer_name,
            "customer_phone": self.customer_phone,
            "customer_email": self.customer_email,
            "customer_address": self.customer_address,
            "customer_nic": self.customer_nic,
            "trade_in_bicycle_id": self.trade_in_bicycle_id,
            "trade_in_value": float(self.trade_in_value) if self.trade_in_value else None,
            "finance_institution": self.finance_institution,
            "down_payment": float(self.down_payment) if self.down_payment else None,
            "financed_amount": float(self.financed_amount) if self.financed_amount else None,
            "sold_by": self.sold_by,
            "sale_invoice_number": self.sale_invoice_number,
            "delivery_date": self.delivery_date.isoformat() if self.delivery_date else None,
            "warranty_months": self.warranty_months,
            "total_cost": float(self.total_cost) if self.total_cost else None,
            "profit_or_loss": float(self.profit_or_loss) if self.profit_or_loss else None,
            "notes": self.notes,
        }
```

**Checklist**:
- [ ] Create `bicycle_sale.py` file
- [ ] Define `SalePaymentMethod` enum
- [ ] Define `BicycleSale` model
- [ ] Add all sale fields (customer, trade-in, finance)
- [ ] Add computed fields (total_cost, profit_or_loss)
- [ ] Add relationships (bicycle, branch, company, trade_in, commissions)
- [ ] Implement `calculate_profit()` method
- [ ] Implement `to_dict()` method
- [ ] Test: Create sale, verify unique constraint on bicycle_id

---

### Task 2.7: Update Bicycle Model

```python
# File: backend/app/models/bicycle.py (MODIFY EXISTING)
# Status: [ ] Not Started | [ ] In Progress | [ ] Completed

# Add new imports
from typing import Optional, TYPE_CHECKING
from decimal import Decimal
from sqlalchemy import Numeric, Date

if TYPE_CHECKING:
    from .company import Company
    from .stock_number import StockNumberAssignment
    from .bicycle_transfer import BicycleTransfer
    from .bicycle_expense import BicycleBranchExpense
    from .bicycle_sale import BicycleSale

class Bicycle(Base):
    # ... existing fields ...

    # NEW FIELDS - Company and business model
    company_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("companies.id")
    )
    business_model: Mapped[str] = mapped_column(
        String, default="HIRE_PURCHASE", nullable=False
    )
    current_stock_number: Mapped[Optional[str]] = mapped_column(String)
    current_branch_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("offices.id")
    )

    # NEW FIELDS - Procurement details
    procurement_date: Mapped[Optional[date]] = mapped_column(Date)
    procurement_source: Mapped[Optional[str]] = mapped_column(String)
    bought_method: Mapped[Optional[str]] = mapped_column(String)
    hand_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    settlement_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    payment_branch_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("offices.id")
    )
    cr_location: Mapped[Optional[str]] = mapped_column(String)
    buyer_employee_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("staff.id")
    )

    # NEW FIELDS - Control flags
    first_od: Mapped[Optional[str]] = mapped_column(String)
    ldate: Mapped[Optional[date]] = mapped_column(Date)
    sk_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    ls_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    caller: Mapped[Optional[str]] = mapped_column(String)
    house_use: Mapped[bool] = mapped_column(Boolean, default=False)

    # NEW FIELDS - Cost tracking
    total_branch_expenses: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal(0)
    )
    # total_expenses is a GENERATED column in DB

    # NEW FIELDS - Sale tracking
    sold_date: Mapped[Optional[date]] = mapped_column(Date)
    selling_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    # profit_or_loss is a GENERATED column in DB

    # NEW RELATIONSHIPS
    company: Mapped[Optional["Company"]] = relationship(
        "Company", back_populates="bicycles"
    )
    stock_assignments: Mapped[list["StockNumberAssignment"]] = relationship(
        "StockNumberAssignment", back_populates="bicycle"
    )
    transfers: Mapped[list["BicycleTransfer"]] = relationship(
        "BicycleTransfer", back_populates="bicycle"
    )
    branch_expenses: Mapped[list["BicycleBranchExpense"]] = relationship(
        "BicycleBranchExpense", back_populates="bicycle"
    )
    sale: Mapped[Optional["BicycleSale"]] = relationship(
        "BicycleSale", back_populates="bicycle", uselist=False
    )
    buyer_employee: Mapped[Optional["Staff"]] = relationship(
        "Staff", foreign_keys=[buyer_employee_id]
    )

    # NEW PROPERTIES
    @property
    def get_current_stock_number(self) -> Optional[str]:
        """Get the current active stock number"""
        for assignment in self.stock_assignments:
            if assignment.is_current:
                return assignment.full_stock_number
        return None

    @property
    def get_total_branch_expenses(self) -> Decimal:
        """Calculate total branch expenses"""
        return sum(exp.amount for exp in self.branch_expenses)

    @property
    def get_total_expenses(self) -> Decimal:
        """Calculate total expenses (purchase + repair + branch)"""
        purchase = self.base_purchase_price or Decimal(0)
        repair = self.total_repair_cost or Decimal(0)
        branch = self.get_total_branch_expenses
        return purchase + repair + branch

    @property
    def get_profit_or_loss(self) -> Optional[Decimal]:
        """Calculate profit or loss if sold"""
        if not self.selling_price:
            return None
        return self.selling_price - self.get_total_expenses

    # Update to_dict() to include new fields
    def to_dict(self) -> dict:
        result = {
            # ... existing fields ...
            "company_id": self.company_id,
            "business_model": self.business_model,
            "current_stock_number": self.current_stock_number or self.get_current_stock_number,
            "current_branch_id": self.current_branch_id,
            "procurement_date": self.procurement_date.isoformat() if self.procurement_date else None,
            "procurement_source": self.procurement_source,
            "bought_method": self.bought_method,
            "hand_amount": float(self.hand_amount) if self.hand_amount else None,
            "settlement_amount": float(self.settlement_amount) if self.settlement_amount else None,
            "payment_branch_id": self.payment_branch_id,
            "cr_location": self.cr_location,
            "buyer_employee_id": self.buyer_employee_id,
            "first_od": self.first_od,
            "ldate": self.ldate.isoformat() if self.ldate else None,
            "sk_flag": self.sk_flag,
            "ls_flag": self.ls_flag,
            "caller": self.caller,
            "house_use": self.house_use,
            "total_branch_expenses": float(self.total_branch_expenses),
            "total_expenses": float(self.get_total_expenses),
            "sold_date": self.sold_date.isoformat() if self.sold_date else None,
            "selling_price": float(self.selling_price) if self.selling_price else None,
            "profit_or_loss": float(self.get_profit_or_loss) if self.get_profit_or_loss else None,
        }
        return result
```

**Checklist**:
- [ ] Add all new fields to Bicycle model
- [ ] Add new relationships (company, stock_assignments, transfers, branch_expenses, sale)
- [ ] Add properties (get_current_stock_number, get_total_branch_expenses, etc.)
- [ ] Update `to_dict()` method with new fields
- [ ] Update `BicycleStatus` enum if needed
- [ ] Test: Create bike with new fields, verify relationships work
- [ ] Test: Verify computed properties calculate correctly

---

### Task 2.8: Update Bonus System Models

```python
# File: backend/app/models/hr_bonus.py (MODIFY EXISTING)
# Status: [ ] Not Started | [ ] In Progress | [ ] Completed

# Update BonusRule class:
class BonusRule(Base):
    # ... existing fields ...

    # NEW FIELDS for bike sales
    applies_to_bike_sales: Mapped[bool] = mapped_column(Boolean, default=False)
    commission_base: Mapped[str] = mapped_column(
        String, default="PROFIT"
    )  # PROFIT or SALE_PRICE
    buyer_branch_percent: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    seller_branch_percent: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))

    def to_dict(self) -> dict:
        result = {
            # ... existing fields ...
            "applies_to_bike_sales": self.applies_to_bike_sales,
            "commission_base": self.commission_base,
            "buyer_branch_percent": float(self.buyer_branch_percent) if self.buyer_branch_percent else None,
            "seller_branch_percent": float(self.seller_branch_percent) if self.seller_branch_percent else None,
        }
        return result


# Update BonusPayment class:
class BonusPayment(Base):
    # ... existing fields ...

    # NEW FIELDS for bike sales
    bicycle_sale_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("bicycle_sales.id")
    )
    commission_type: Mapped[Optional[str]] = mapped_column(
        String
    )  # BUYER or SELLER

    # NEW RELATIONSHIP
    bicycle_sale: Mapped[Optional["BicycleSale"]] = relationship(
        "BicycleSale", back_populates="commissions"
    )

    def to_dict(self) -> dict:
        result = {
            # ... existing fields ...
            "bicycle_sale_id": self.bicycle_sale_id,
            "commission_type": self.commission_type,
        }
        return result
```

**Checklist**:
- [ ] Add bike sale fields to `BonusRule` model
- [ ] Add validation for percentage sum = 100
- [ ] Add `bicycle_sale_id` to `BonusPayment` model
- [ ] Add `commission_type` field
- [ ] Add `bicycle_sale` relationship
- [ ] Update `to_dict()` methods
- [ ] Test: Create bonus rule for bike sales
- [ ] Test: Create bonus payment linked to sale

---

### Task 2.9: Update Model Imports

```python
# File: backend/app/models/__init__.py (UPDATE)
# Status: [ ] Not Started | [ ] In Progress | [ ] Completed

# Add new model imports
from .company import Company
from .stock_number import StockNumberSequence, StockNumberAssignment
from .bicycle_transfer import BicycleTransfer, TransferStatus
from .bicycle_expense import BicycleBranchExpense, ExpenseCategory
from .bicycle_sale import BicycleSale, SalePaymentMethod

# Ensure all models are exported
__all__ = [
    # ... existing exports ...
    "Company",
    "StockNumberSequence",
    "StockNumberAssignment",
    "BicycleTransfer",
    "TransferStatus",
    "BicycleBranchExpense",
    "ExpenseCategory",
    "BicycleSale",
    "SalePaymentMethod",
]
```

**Checklist**:
- [ ] Import all new models
- [ ] Export in `__all__`
- [ ] Test: `from app.models import Company` works
- [ ] Test: No circular import errors

---

### Task 2.10: Model Testing

**Checklist**:
- [ ] Write unit test for Company model
- [ ] Write unit test for StockNumberAssignment model
- [ ] Write unit test for BicycleTransfer state transitions
- [ ] Write unit test for BicycleBranchExpense calculations
- [ ] Write unit test for BicycleSale profit calculations
- [ ] Write integration test for Bicycle with all relationships
- [ ] Test computed properties on Bicycle
- [ ] Test cascade deletes (bicycle → expenses, transfers)
- [ ] Run all model tests: `pytest tests/models/`

---

## Phase 3: Business Logic Services

**Duration**: 3-4 days
**Files**: `backend/app/services/*.py`

### Task 3.1: Stock Number Service

```python
# File: backend/app/services/stock_number_service.py
# Status: [ ] Not Started | [ ] In Progress | [ ] Completed

from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import secrets

from ..models import (
    StockNumberSequence, StockNumberAssignment,
    Bicycle, Company, Office
)

class StockNumberService:

    @staticmethod
    async def generate_stock_number(
        db: AsyncSession,
        company_id: str,
        branch_id: str
    ) -> tuple[int, str]:
        """
        Generate next stock number for company/branch.
        Returns: (running_number, full_stock_number)
        Example: (2066, "MA/WW/ST/2066")
        """
        # Get or create sequence
        result = await db.execute(
            select(StockNumberSequence).where(
                StockNumberSequence.company_id == company_id,
                StockNumberSequence.branch_id == branch_id
            )
        )
        sequence = result.scalar_one_or_none()

        if not sequence:
            # Create new sequence
            sequence = StockNumberSequence(
                company_id=company_id,
                branch_id=branch_id,
                current_number=0
            )
            db.add(sequence)
            await db.flush()

        # Increment counter
        next_number = sequence.current_number + 1
        sequence.current_number = next_number
        sequence.last_assigned_at = datetime.now()

        # Format: MA/WW/ST/2066
        full_stock_number = f"{company_id}/{branch_id}/ST/{next_number:04d}"

        return next_number, full_stock_number

    @staticmethod
    async def assign_stock_number(
        db: AsyncSession,
        bicycle_id: str,
        company_id: str,
        branch_id: str,
        reason: str,
        notes: str = None
    ) -> StockNumberAssignment:
        """
        Assign new stock number to bicycle.
        Releases previous assignment if exists.
        """
        # Release previous assignment
        await db.execute(
            update(StockNumberAssignment)
            .where(
                StockNumberAssignment.bicycle_id == bicycle_id,
                StockNumberAssignment.released_date.is_(None)
            )
            .values(released_date=datetime.now())
        )

        # Generate new stock number
        running_number, full_stock_number = await StockNumberService.generate_stock_number(
            db, company_id, branch_id
        )

        # Create assignment
        assignment_id = f"SNA-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"
        assignment = StockNumberAssignment(
            id=assignment_id,
            bicycle_id=bicycle_id,
            company_id=company_id,
            branch_id=branch_id,
            running_number=running_number,
            full_stock_number=full_stock_number,
            assigned_date=datetime.now(),
            assignment_reason=reason,
            notes=notes
        )
        db.add(assignment)

        # Update bicycle's cached stock number
        await db.execute(
            update(Bicycle)
            .where(Bicycle.id == bicycle_id)
            .values(
                current_stock_number=full_stock_number,
                current_branch_id=branch_id
            )
        )

        return assignment

    @staticmethod
    async def get_current_assignment(
        db: AsyncSession,
        bicycle_id: str
    ) -> StockNumberAssignment | None:
        """Get current active stock number assignment"""
        result = await db.execute(
            select(StockNumberAssignment)
            .where(
                StockNumberAssignment.bicycle_id == bicycle_id,
                StockNumberAssignment.released_date.is_(None)
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_assignment_history(
        db: AsyncSession,
        bicycle_id: str
    ) -> list[StockNumberAssignment]:
        """Get all stock number assignments for a bicycle"""
        result = await db.execute(
            select(StockNumberAssignment)
            .where(StockNumberAssignment.bicycle_id == bicycle_id)
            .order_by(StockNumberAssignment.assigned_date.desc())
        )
        return list(result.scalars().all())
```

**Checklist**:
- [ ] Create `stock_number_service.py`
- [ ] Implement `generate_stock_number()` with sequence increment
- [ ] Implement `assign_stock_number()` with auto-release
- [ ] Implement `get_current_assignment()`
- [ ] Implement `get_assignment_history()`
- [ ] Add error handling (company/branch not found)
- [ ] Test: Generate sequential numbers (2066, 2067, 2068)
- [ ] Test: Assignment auto-releases previous
- [ ] Test: Concurrent assignment (race conditions)

---

### Task 3.2: Bike Lifecycle Service

```python
# File: backend/app/services/bike_lifecycle_service.py
# Status: [ ] Not Started | [ ] In Progress | [ ] Completed

from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import secrets

from ..models import Bicycle, BicycleSale, Office, Company
from .stock_number_service import StockNumberService
from .commission_service import CommissionService

class BikeLifecycleService:

    @staticmethod
    async def procure_bike(
        db: AsyncSession,
        procurement_data: dict
    ) -> Bicycle:
        """
        Create new bike procurement record.
        Generates first stock number automatically.
        """
        # Generate bike ID
        bike_id = f"BK-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(4).upper()}"

        # Get company from branch
        result = await db.execute(
            select(Office).where(Office.id == procurement_data["branch_id"])
        )
        branch = result.scalar_one()
        company_id = branch.company_id

        # Create bicycle
        bicycle = Bicycle(
            id=bike_id,
            company_id=company_id,
            business_model=procurement_data.get("business_model", "STOCK"),
            license_plate=procurement_data["license_plate"],
            title=procurement_data["title"],
            model_name=procurement_data["model_name"],
            year=procurement_data.get("year"),
            condition=procurement_data.get("condition", "USED"),
            base_purchase_price=procurement_data["purchase_price"],
            status="IN_STOCK",

            # Procurement details
            procurement_date=procurement_data.get("procurement_date", date.today()),
            procurement_source=procurement_data.get("procurement_source"),
            bought_method=procurement_data.get("bought_method"),
            hand_amount=procurement_data.get("hand_amount"),
            settlement_amount=procurement_data.get("settlement_amount"),
            payment_branch_id=procurement_data.get("payment_branch_id"),
            cr_location=procurement_data.get("cr_location"),
            buyer_employee_id=procurement_data.get("buyer_employee_id"),

            # Control flags
            first_od=procurement_data.get("first_od"),
            ldate=procurement_data.get("ldate"),
            sk_flag=procurement_data.get("sk_flag", False),
            ls_flag=procurement_data.get("ls_flag", False),
            caller=procurement_data.get("caller"),
            house_use=procurement_data.get("house_use", False),
        )
        db.add(bicycle)
        await db.flush()

        # Assign first stock number
        await StockNumberService.assign_stock_number(
            db,
            bicycle_id=bike_id,
            company_id=company_id,
            branch_id=procurement_data["branch_id"],
            reason="PURCHASE",
            notes="Initial procurement"
        )

        return bicycle

    @staticmethod
    async def calculate_bike_cost_summary(
        db: AsyncSession,
        bicycle_id: str
    ) -> dict:
        """
        Calculate detailed cost breakdown for a bike.
        Returns dict like summery.xlsx row.
        """
        result = await db.execute(
            select(Bicycle).where(Bicycle.id == bicycle_id)
        )
        bike = result.scalar_one()

        purchase_price = bike.base_purchase_price or Decimal(0)
        branch_expenses = bike.get_total_branch_expenses
        garage_expenses = bike.total_repair_cost or Decimal(0)
        total_expenses = purchase_price + branch_expenses + garage_expenses

        selling_price = bike.selling_price or Decimal(0)
        profit_or_loss = selling_price - total_expenses if selling_price else None

        return {
            "bicycle_id": bike.id,
            "bike_no": bike.license_plate,
            "model": bike.model_name,
            "branch": bike.current_branch_id,
            "stock_number": bike.current_stock_number,
            "received_date": bike.procurement_date.isoformat() if bike.procurement_date else None,
            "purchased_price": float(purchase_price),
            "branch_expenses": float(branch_expenses),
            "garage_expenses": float(garage_expenses),
            "total_expenses": float(total_expenses),
            "released_date": bike.sold_date.isoformat() if bike.sold_date else None,
            "selling_price": float(selling_price) if selling_price else None,
            "profit_or_loss": float(profit_or_loss) if profit_or_loss else None,
        }

    @staticmethod
    async def sell_bike(
        db: AsyncSession,
        bicycle_id: str,
        sale_data: dict
    ) -> BicycleSale:
        """
        Record bike sale, update bike status, calculate P&L, trigger commission.
        """
        # Get bike
        result = await db.execute(
            select(Bicycle).where(Bicycle.id == bicycle_id)
        )
        bike = result.scalar_one()

        # Validate bike is sellable
        if bike.status == "SOLD":
            raise ValueError("Bicycle already sold")
        if bike.status not in ["IN_STOCK", "AVAILABLE"]:
            raise ValueError(f"Cannot sell bicycle in status {bike.status}")

        # Get current stock number
        current_assignment = await StockNumberService.get_current_assignment(db, bicycle_id)
        stock_number_at_sale = current_assignment.full_stock_number if current_assignment else None

        # Calculate costs
        cost_summary = await BikeLifecycleService.calculate_bike_cost_summary(db, bicycle_id)
        total_cost = Decimal(str(cost_summary["total_expenses"]))
        selling_price = Decimal(str(sale_data["selling_price"]))
        profit_or_loss = selling_price - total_cost

        # Get selling branch and company
        selling_branch_id = sale_data.get("selling_branch_id", bike.current_branch_id)
        result = await db.execute(
            select(Office).where(Office.id == selling_branch_id)
        )
        selling_branch = result.scalar_one()
        selling_company_id = selling_branch.company_id

        # Create sale record
        sale_id = f"SALE-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"
        sale = BicycleSale(
            id=sale_id,
            bicycle_id=bicycle_id,
            selling_branch_id=selling_branch_id,
            selling_company_id=selling_company_id,
            stock_number_at_sale=stock_number_at_sale,
            sale_date=sale_data.get("sale_date", date.today()),
            selling_price=selling_price,
            payment_method=sale_data["payment_method"],
            customer_name=sale_data.get("customer_name"),
            customer_phone=sale_data.get("customer_phone"),
            customer_email=sale_data.get("customer_email"),
            customer_address=sale_data.get("customer_address"),
            customer_nic=sale_data.get("customer_nic"),
            trade_in_bicycle_id=sale_data.get("trade_in_bicycle_id"),
            trade_in_value=sale_data.get("trade_in_value"),
            finance_institution=sale_data.get("finance_institution"),
            down_payment=sale_data.get("down_payment"),
            financed_amount=sale_data.get("financed_amount"),
            sold_by=sale_data["sold_by"],
            sale_invoice_number=sale_data.get("sale_invoice_number"),
            delivery_date=sale_data.get("delivery_date"),
            warranty_months=sale_data.get("warranty_months"),
            total_cost=total_cost,
            profit_or_loss=profit_or_loss,
            notes=sale_data.get("notes"),
        )
        db.add(sale)

        # Update bicycle status
        bike.status = "SOLD"
        bike.sold_date = sale.sale_date
        bike.selling_price = selling_price

        await db.flush()

        # Calculate and record commissions
        await CommissionService.calculate_bike_sale_commission(db, sale_id)

        return sale
```

**Checklist**:
- [ ] Create `bike_lifecycle_service.py`
- [ ] Implement `procure_bike()` with auto stock number
- [ ] Implement `calculate_bike_cost_summary()` (summery.xlsx format)
- [ ] Implement `sell_bike()` with P&L and commission trigger
- [ ] Add validation (bike status checks)
- [ ] Add error handling (branch not found, etc.)
- [ ] Test: Procure bike, verify stock number assigned
- [ ] Test: Calculate cost summary, verify amounts
- [ ] Test: Sell bike, verify status updated and commission created

---

### Task 3.3: Transfer Service

```python
# File: backend/app/services/transfer_service.py
# Status: [ ] Not Started | [ ] In Progress | [ ] Completed

from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import secrets

from ..models import Bicycle, BicycleTransfer, TransferStatus, Office
from .stock_number_service import StockNumberService

class TransferService:

    @staticmethod
    async def initiate_transfer(
        db: AsyncSession,
        bicycle_id: str,
        to_branch_id: str,
        requested_by: str,
        transfer_reason: str = None
    ) -> BicycleTransfer:
        """Create new transfer request"""
        # Get bike
        result = await db.execute(
            select(Bicycle).where(Bicycle.id == bicycle_id)
        )
        bike = result.scalar_one()

        # Validate
        if bike.status not in ["IN_STOCK", "AVAILABLE", "MAINTENANCE"]:
            raise ValueError(f"Cannot transfer bicycle in status {bike.status}")
        if bike.current_branch_id == to_branch_id:
            raise ValueError("Bike already at target branch")

        # Get current stock number
        current_assignment = await StockNumberService.get_current_assignment(db, bicycle_id)
        from_stock_number = current_assignment.full_stock_number if current_assignment else None

        # Create transfer
        transfer_id = f"TRF-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"
        transfer = BicycleTransfer(
            id=transfer_id,
            bicycle_id=bicycle_id,
            from_branch_id=bike.current_branch_id,
            to_branch_id=to_branch_id,
            from_stock_number=from_stock_number,
            status=TransferStatus.PENDING,
            requested_by=requested_by,
            transfer_reason=transfer_reason,
        )
        db.add(transfer)

        return transfer

    @staticmethod
    async def approve_transfer(
        db: AsyncSession,
        transfer_id: str,
        approved_by: str
    ) -> BicycleTransfer:
        """Approve transfer and assign new stock number"""
        # Get transfer
        result = await db.execute(
            select(BicycleTransfer).where(BicycleTransfer.id == transfer_id)
        )
        transfer = result.scalar_one()

        # Approve
        transfer.approve(approved_by)

        # Get target branch company
        result = await db.execute(
            select(Office).where(Office.id == transfer.to_branch_id)
        )
        to_branch = result.scalar_one()

        # Assign new stock number
        assignment = await StockNumberService.assign_stock_number(
            db,
            bicycle_id=transfer.bicycle_id,
            company_id=to_branch.company_id,
            branch_id=transfer.to_branch_id,
            reason="TRANSFER_IN",
            notes=f"Transfer from {transfer.from_branch_id}"
        )

        transfer.to_stock_number = assignment.full_stock_number
        transfer.status = TransferStatus.IN_TRANSIT

        return transfer

    @staticmethod
    async def complete_transfer(
        db: AsyncSession,
        transfer_id: str,
        completed_by: str
    ) -> BicycleTransfer:
        """Mark transfer as completed"""
        result = await db.execute(
            select(BicycleTransfer).where(BicycleTransfer.id == transfer_id)
        )
        transfer = result.scalar_one()

        transfer.complete(completed_by)

        return transfer

    @staticmethod
    async def reject_transfer(
        db: AsyncSession,
        transfer_id: str,
        rejected_by: str,
        reason: str
    ) -> BicycleTransfer:
        """Reject transfer request"""
        result = await db.execute(
            select(BicycleTransfer).where(BicycleTransfer.id == transfer_id)
        )
        transfer = result.scalar_one()

        transfer.reject(rejected_by, reason)

        return transfer
```

**Checklist**:
- [ ] Create `transfer_service.py`
- [ ] Implement `initiate_transfer()` with validation
- [ ] Implement `approve_transfer()` with stock number reassignment
- [ ] Implement `complete_transfer()`
- [ ] Implement `reject_transfer()`
- [ ] Add status transition validation
- [ ] Test: Full transfer workflow (initiate → approve → complete)
- [ ] Test: Rejection workflow
- [ ] Test: Verify stock number changes on approval

---

### Task 3.4: Commission Service

```python
# File: backend/app/services/commission_service.py
# Status: [ ] Not Started | [ ] In Progress | [ ] Completed

from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import secrets

from ..models import (
    BicycleSale, Bicycle, BonusRule, BonusPayment, Office
)

class CommissionService:

    @staticmethod
    async def calculate_bike_sale_commission(
        db: AsyncSession,
        sale_id: str
    ) -> list[BonusPayment]:
        """
        Calculate and create commission payments for bike sale.
        Returns list of bonus payments created.
        """
        # Get sale
        result = await db.execute(
            select(BicycleSale).where(BicycleSale.id == sale_id)
        )
        sale = result.scalar_one()

        # Get bike
        result = await db.execute(
            select(Bicycle).where(Bicycle.id == sale.bicycle_id)
        )
        bike = result.scalar_one()

        # Get applicable commission rule
        result = await db.execute(
            select(BonusRule)
            .where(
                BonusRule.applies_to_bike_sales == True,
                BonusRule.is_active == True,
                BonusRule.effective_from <= sale.sale_date
            )
            .order_by(BonusRule.effective_from.desc())
        )
        rule = result.first()

        if not rule:
            # No commission rule, skip
            return []

        rule = rule[0]

        # Calculate commission base
        if rule.commission_base == "SALE_PRICE":
            commission_base = sale.selling_price
        else:  # PROFIT
            if not sale.profit_or_loss or sale.profit_or_loss <= 0:
                # No profit, no commission
                return []
            commission_base = sale.profit_or_loss

        # Calculate buyer commission
        buyer_commission = commission_base * (rule.buyer_branch_percent / Decimal(100))
        buyer_branch_id = bike.current_branch_id  # Branch that purchased the bike

        # Calculate seller commission
        seller_commission = commission_base * (rule.seller_branch_percent / Decimal(100))
        seller_branch_id = sale.selling_branch_id

        # Create bonus payments
        payments = []

        # Buyer commission
        buyer_payment_id = f"BP-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"
        buyer_payment = BonusPayment(
            id=buyer_payment_id,
            branch_id=buyer_branch_id,
            period_start=date(sale.sale_date.year, sale.sale_date.month, 1),
            period_end=date(sale.sale_date.year, sale.sale_date.month, 28),  # Simplified
            amount=buyer_commission,
            calculation_details=f"Buyer commission for bike {bike.license_plate}",
            bicycle_sale_id=sale_id,
            commission_type="BUYER",
        )
        db.add(buyer_payment)
        payments.append(buyer_payment)

        # Seller commission (only if different branch)
        if seller_branch_id != buyer_branch_id:
            seller_payment_id = f"BP-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"
            seller_payment = BonusPayment(
                id=seller_payment_id,
                branch_id=seller_branch_id,
                period_start=date(sale.sale_date.year, sale.sale_date.month, 1),
                period_end=date(sale.sale_date.year, sale.sale_date.month, 28),
                amount=seller_commission,
                calculation_details=f"Seller commission for bike {bike.license_plate}",
                bicycle_sale_id=sale_id,
                commission_type="SELLER",
            )
            db.add(seller_payment)
            payments.append(seller_payment)

        return payments

    @staticmethod
    async def get_branch_commission_report(
        db: AsyncSession,
        branch_id: str,
        start_date: date,
        end_date: date
    ) -> dict:
        """Get commission summary for branch in date range"""
        result = await db.execute(
            select(BonusPayment)
            .where(
                BonusPayment.branch_id == branch_id,
                BonusPayment.bicycle_sale_id.isnot(None),
                BonusPayment.period_start >= start_date,
                BonusPayment.period_end <= end_date
            )
        )
        payments = list(result.scalars().all())

        buyer_commission = sum(
            p.amount for p in payments if p.commission_type == "BUYER"
        )
        seller_commission = sum(
            p.amount for p in payments if p.commission_type == "SELLER"
        )
        total_commission = buyer_commission + seller_commission

        return {
            "branch_id": branch_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "buyer_commission": float(buyer_commission),
            "seller_commission": float(seller_commission),
            "total_commission": float(total_commission),
            "sale_count": len(payments),
        }
```

**Checklist**:
- [ ] Create `commission_service.py`
- [ ] Implement `calculate_bike_sale_commission()`
- [ ] Handle PROFIT vs SALE_PRICE base calculation
- [ ] Handle zero/negative profit (no commission)
- [ ] Implement `get_branch_commission_report()`
- [ ] Test: Commission with profit base
- [ ] Test: Commission with sale price base
- [ ] Test: No commission when no profit
- [ ] Test: Branch commission report aggregation

---

### Task 3.5: Service Testing

**Checklist**:
- [ ] Write unit tests for StockNumberService
- [ ] Write unit tests for BikeLifecycleService
- [ ] Write unit tests for TransferService
- [ ] Write unit tests for CommissionService
- [ ] Write integration test: procure → transfer → sell → commission
- [ ] Test edge cases (concurrent stock number generation)
- [ ] Test error handling (invalid bike status, etc.)
- [ ] Run all service tests: `pytest tests/services/`

---

## Phase 4: API Endpoints

**Duration**: 5-6 days
**Files**: `backend/app/routers/*.py`

### Task 4.1: Companies Router

```python
# File: backend/app/routers/companies.py
# Status: [ ] Not Started | [ ] In Progress | [ ] Completed

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional

from ..db import get_db
from ..auth import get_current_user
from ..rbac import require_permission
from ..models import Company

router = APIRouter(prefix="/v1/companies", tags=["companies"])

# Pydantic models
class CompanyCreate(BaseModel):
    id: str
    name: str
    district: str
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    address: Optional[dict] = None
    tax_id: Optional[str] = None

class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    district: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    address: Optional[dict] = None
    tax_id: Optional[str] = None
    is_active: Optional[bool] = None

class CompanyOut(BaseModel):
    id: str
    name: str
    district: str
    contact_person: Optional[str]
    contact_phone: Optional[str]
    contact_email: Optional[str]
    address: Optional[dict]
    tax_id: Optional[str]
    is_active: bool
    created_at: str
    updated_at: str

class CompanyListResponse(BaseModel):
    items: list[CompanyOut]
    total: int

@router.get("", response_model=CompanyListResponse)
async def list_companies(
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List all companies"""
    query = select(Company)

    if is_active is not None:
        query = query.where(Company.is_active == is_active)

    result = await db.execute(query)
    companies = list(result.scalars().all())

    return {
        "items": [CompanyOut(**c.to_dict()) for c in companies],
        "total": len(companies),
    }

@router.post("", response_model=CompanyOut)
async def create_company(
    data: CompanyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create new company (admin only)"""
    require_permission(current_user, "companies:write")

    # Check if company ID already exists
    result = await db.execute(select(Company).where(Company.id == data.id))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Company ID already exists")

    company = Company(**data.model_dump())
    db.add(company)
    await db.commit()
    await db.refresh(company)

    return CompanyOut(**company.to_dict())

@router.get("/{company_id}", response_model=CompanyOut)
async def get_company(
    company_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get company details"""
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    return CompanyOut(**company.to_dict())

@router.put("/{company_id}", response_model=CompanyOut)
async def update_company(
    company_id: str,
    data: CompanyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Update company (admin only)"""
    require_permission(current_user, "companies:write")

    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(company, key, value)

    await db.commit()
    await db.refresh(company)

    return CompanyOut(**company.to_dict())
```

**Checklist**:
- [ ] Create `companies.py` router
- [ ] Define Pydantic models (Create, Update, Out)
- [ ] Implement GET /v1/companies (list with filters)
- [ ] Implement POST /v1/companies (admin only)
- [ ] Implement GET /v1/companies/{id}
- [ ] Implement PUT /v1/companies/{id}
- [ ] Add RBAC permission checks
- [ ] Register router in main.py
- [ ] Test all endpoints with curl/Postman

---

**(Continue with similar detailed tasks for all other routers...)**

Due to length constraints, I'll provide the **table of contents** for remaining API router tasks:

### Task 4.2: Bike Lifecycle Router
- [ ] POST /v1/bikes/procure
- [ ] GET /v1/bikes (with filters: company, branch, status, business_model)
- [ ] GET /v1/bikes/{id}
- [ ] GET /v1/bikes/{id}/cost-summary
- [ ] GET /v1/bikes/{id}/stock-history
- [ ] PUT /v1/bikes/{id}
- [ ] DELETE /v1/bikes/{id}

### Task 4.3: Bike Transfers Router
- [ ] POST /v1/bikes/{id}/transfers
- [ ] GET /v1/transfers (with status filter)
- [ ] GET /v1/transfers/{id}
- [ ] POST /v1/transfers/{id}/approve
- [ ] POST /v1/transfers/{id}/complete
- [ ] POST /v1/transfers/{id}/reject

### Task 4.4: Bike Sales Router
- [ ] POST /v1/bikes/{id}/sell
- [ ] GET /v1/sales
- [ ] GET /v1/sales/{id}
- [ ] GET /v1/sales/profit-report

### Task 4.5: Bike Expenses Router
- [ ] POST /v1/bikes/{id}/expenses
- [ ] GET /v1/bikes/{id}/expenses
- [ ] PUT /v1/expenses/{id}
- [ ] DELETE /v1/expenses/{id}

### Task 4.6: Reports Router
- [ ] GET /v1/reports/acquisition-ledger
- [ ] GET /v1/reports/cost-summary
- [ ] GET /v1/reports/branch-commissions
- [ ] GET /v1/reports/garage-productivity

### Task 4.7: Extend Existing Routers
- [ ] Update bicycles.py (add company, stock number)
- [ ] Update workshop_jobs.py (link to bikes)
- [ ] Update hr_bonus.py (commission endpoints)

### Task 4.8: API Testing
- [ ] Write integration tests for all endpoints
- [ ] Test RBAC permissions
- [ ] Test branch isolation
- [ ] Test error responses

---

## Phase 5: Frontend UI

**Duration**: 7-8 days
**Files**: `frontend/src/app/**` and `frontend/src/components/**`

### Task 5.1: Generate API Types
- [ ] Run `npm run generate:api` to update TypeScript types
- [ ] Verify all new endpoints have types

### Task 5.2: Bike Acquisition Page
- [ ] Create `/bikes/acquisition/page.tsx`
- [ ] Build `BikeAcquisitionForm` component
- [ ] Add all fields from November notebook
- [ ] Add validation (required fields, formats)
- [ ] Submit handler with success/error toast

### Task 5.3: Bike Inventory Dashboard
- [ ] Create `/bikes/inventory/page.tsx`
- [ ] Build filter panel (company, branch, status, date range)
- [ ] Build bike list table with pagination
- [ ] Add action buttons (Transfer, Sell, View)
- [ ] Add export to Excel button

### Task 5.4: Bike Detail Page
- [ ] Create `/bikes/[id]/page.tsx`
- [ ] Build overview section (basic info, current location)
- [ ] Build cost summary section (like summery.xlsx)
- [ ] Build stock history timeline
- [ ] Build transfer history list
- [ ] Build repair jobs list with links

### Task 5.5: Transfer Management Pages
- [ ] Create `/bikes/transfers/page.tsx`
- [ ] Build pending transfers tab
- [ ] Build in-transit tab
- [ ] Build history tab
- [ ] Build transfer request modal
- [ ] Build approve/reject modal

### Task 5.6: Sales Page
- [ ] Create `/bikes/sales/page.tsx`
- [ ] Build recent sales list
- [ ] Build sale form modal
- [ ] Add P&L preview calculator
- [ ] Add customer details section
- [ ] Add payment method selection

### Task 5.7: Reports Dashboard
- [ ] Create `/bikes/reports/page.tsx`
- [ ] Build acquisition ledger view
- [ ] Build cost summary view (summery.xlsx replica)
- [ ] Build commission report
- [ ] Build garage productivity report
- [ ] Add date range filters and export

### Task 5.8: Reusable Components
- [ ] Create `BikeStockCard.tsx`
- [ ] Create `BikeCostSummary.tsx`
- [ ] Create `BikeTransferFlow.tsx`
- [ ] Create `BikeSaleForm.tsx`
- [ ] Create `StockNumberBadge.tsx`
- [ ] Create `BikeStatusBadge.tsx`
- [ ] Create `BikeLifecycleTimeline.tsx`

### Task 5.9: Extend Existing Pages
- [ ] Update `/workshop/jobs` to show bike stock numbers
- [ ] Update `/reference/offices` to show company
- [ ] Add bike lifecycle menu items to navigation

### Task 5.10: Frontend Testing
- [ ] Test all forms with validation
- [ ] Test all workflows (procure → transfer → sell)
- [ ] Test responsive design
- [ ] Test role-based access (hide actions for non-authorized users)

---

## Phase 6: Reports & Analytics

**Duration**: 3-4 days

### Task 6.1: Materialized View Refresh
- [ ] Create cron job or scheduled task to refresh views nightly
- [ ] Add manual refresh endpoint for admins
- [ ] Monitor refresh performance

### Task 6.2: Report Optimization
- [ ] Add indexes for common filter combinations
- [ ] Optimize query performance (EXPLAIN ANALYZE)
- [ ] Add caching for frequently accessed reports

### Task 6.3: Export Functionality
- [ ] Implement Excel export for acquisition ledger
- [ ] Implement Excel export for cost summary
- [ ] Implement PDF export for commission reports
- [ ] Match Excel formatting to current summery.xlsx

---

## Phase 7: Data Migration

**Duration**: 4-5 days

### Task 7.1: Historical Data Import
- [ ] Export summery.xlsx to CSV
- [ ] Write `scripts/import_summery.py`
- [ ] Map Excel columns to database fields
- [ ] Handle missing/invalid data
- [ ] Run import on test database
- [ ] Verify imported data accuracy

### Task 7.2: Notebook Import
- [ ] Manually transcribe November notebook to CSV
- [ ] Write `scripts/import_notebook.py`
- [ ] Import procurement records
- [ ] Backfill stock numbers
- [ ] Verify against physical notebook

### Task 7.3: BRC Cost Reconciliation
- [ ] Export BRC Excel to CSV
- [ ] Write `scripts/reconcile_brc.py`
- [ ] Match to existing repair_jobs
- [ ] Create missing repair jobs
- [ ] Verify cost totals match

---

## Phase 8: Testing & Deployment

**Duration**: 5-6 days

### Task 8.1: Integration Testing
- [ ] Test full workflow: procure → repair → transfer → sell → commission
- [ ] Test concurrent operations (race conditions)
- [ ] Test rollback scenarios (failed transfers, sales)
- [ ] Test branch isolation (branch managers can't see other branches)

### Task 8.2: Performance Testing
- [ ] Load test with 1000+ bikes
- [ ] Test report generation with large datasets
- [ ] Optimize slow queries
- [ ] Add database indexes as needed

### Task 8.3: User Acceptance Testing
- [ ] Train pilot users (1-2 branches)
- [ ] Gather feedback on UI/UX
- [ ] Identify bugs and edge cases
- [ ] Iterate on feedback

### Task 8.4: Documentation
- [ ] Write user manual (PDF)
- [ ] Create video tutorials
- [ ] Document API endpoints (Swagger/OpenAPI)
- [ ] Write deployment guide

### Task 8.5: Production Deployment
- [ ] Run migration on production database (with backup)
- [ ] Deploy backend to production
- [ ] Deploy frontend to production
- [ ] Verify all integrations working
- [ ] Monitor logs for errors

### Task 8.6: Training & Rollout
- [ ] Conduct training sessions for all branches
- [ ] Provide printed user guides
- [ ] Set up support channel (phone/email)
- [ ] Monitor adoption rates
- [ ] Collect feedback for improvements

---

## Appendix: Technical References

### ID Generation Pattern
```python
import secrets
from datetime import datetime

def generate_id(prefix: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = secrets.token_hex(3).upper()
    return f"{prefix}-{timestamp}-{random_suffix}"
```

### Stock Number Format
```
{company_id}/{branch_id}/ST/{running_number:04d}

Examples:
- MA/WW/ST/2066
- IN/HP/ST/0312
- MA/BRC/ST/0001
```

### Status Enums

**BicycleStatus**:
- `AVAILABLE` - Ready for hire purchase
- `RESERVED` - Reserved by customer
- `SOLD` - Sold (hire purchase or direct)
- `MAINTENANCE` - In workshop
- `IN_STOCK` - Available for sale (second-hand)
- `ALLOCATED` - Allocated to branch (not yet transferred)
- `IN_TRANSIT` - Being transferred
- `WRITTEN_OFF` - Removed from inventory

**TransferStatus**:
- `PENDING` - Awaiting approval
- `APPROVED` - Approved, stock number assigned
- `IN_TRANSIT` - Physically moving
- `COMPLETED` - Received at destination
- `REJECTED` - Rejected
- `CANCELLED` - Cancelled by requester

**ExpenseCategory**:
- `TRANSPORT` - Transport/delivery costs
- `MINOR_REPAIR` - Small repairs at branch
- `LICENSE_RENEWAL` - License/registration renewal
- `INSURANCE` - Insurance costs
- `CLEANING` - Cleaning/detailing
- `DOCUMENTATION` - Document processing fees
- `STORAGE` - Storage costs
- `OTHER` - Other miscellaneous

**SalePaymentMethod**:
- `CASH` - Full cash payment
- `FINANCE` - Financed by institution
- `TRADE_IN` - Trade-in for another bike
- `BANK_TRANSFER` - Bank transfer
- `MIXED` - Multiple payment methods

### Database Indexing Strategy

**High-priority indexes**:
```sql
-- Bike lookups
CREATE INDEX idx_bicycles_company_branch ON bicycles(company_id, current_branch_id);
CREATE INDEX idx_bicycles_status_model ON bicycles(status, business_model);
CREATE INDEX idx_bicycles_stock_number ON bicycles(current_stock_number);

-- Stock number lookups
CREATE INDEX idx_stock_assignments_current ON stock_number_assignments(bicycle_id, released_date)
    WHERE released_date IS NULL;

-- Transfer workflows
CREATE INDEX idx_transfers_status_branch ON bicycle_transfers(status, to_branch_id);

-- Sales reporting
CREATE INDEX idx_sales_date_branch ON bicycle_sales(sale_date, selling_branch_id);

-- Commission reporting
CREATE INDEX idx_bonus_payments_sale ON bonus_payments(bicycle_sale_id)
    WHERE bicycle_sale_id IS NOT NULL;
```

### Permission Matrix

| Role | Companies | Bikes | Transfers | Sales | Expenses | Reports |
|------|-----------|-------|-----------|-------|----------|---------|
| Admin | Full | Full | Full | Full | Full | Full |
| Branch Manager | Read | Branch only | Branch only | Branch only | Branch only | Branch only |
| Inventory Manager | Read | Full | Approve | Read | Read | Full |
| Finance Officer | Read | Read | Read | Full | Full | Full |
| Sales Agent | Read | Read | Request | Create | Read | Read |

---

## Progress Tracking

### Week 1-2: Database & Models ✅❌
- [ ] Phase 1: Database Schema (10 tasks)
- [ ] Phase 2: Backend Models (10 tasks)

### Week 3: Backend API ✅❌
- [ ] Phase 3: Business Logic (5 tasks)
- [ ] Phase 4: API Endpoints (8 tasks - partial)

### Week 4: Backend Completion ✅❌
- [ ] Phase 4: API Endpoints (complete)
- [ ] API Testing

### Week 5: Frontend Core ✅❌
- [ ] Phase 5: Frontend UI (tasks 1-4)

### Week 6: Frontend Advanced ✅❌
- [ ] Phase 5: Frontend UI (tasks 5-10)
- [ ] Phase 6: Reports (3 tasks)

### Week 7: Integration & Migration ✅❌
- [ ] Phase 7: Data Migration (3 tasks)
- [ ] Integration testing

### Week 8: Deployment ✅❌
- [ ] Phase 8: Testing & Deployment (6 tasks)

---

## Notes & Decisions Log

**Date**: 2025-11-18
**Decision**: Use exact stock number format `MA/WW/ST/2066`, separate from database IDs.
**Rationale**: Matches existing business process and documentation.

**Date**: 2025-11-18
**Decision**: Extend existing `bicycles` table rather than create separate table.
**Rationale**: Unified bike inventory, reuses existing workshop integration.

**Date**: 2025-11-18
**Decision**: Companies own branches (add company_id to offices).
**Rationale**: Matches MA (Monaragala) and IN (Badulla) district structure from spec.

**Date**: 2025-11-18
**Decision**: Integrate commissions with HR bonus system.
**Rationale**: Unified payroll/commission reporting, reuses existing infrastructure.

---

## Support & Resources

- **Database Design**: See migration 0008
- **API Documentation**: http://localhost:8000/docs (after deployment)
- **Frontend**: http://localhost:3000
- **Code Repository**: [Insert Git URL]
- **Slack Channel**: #bike-lifecycle-project
- **Project Manager**: [Name]
- **Technical Lead**: [Name]

---

**END OF IMPLEMENTATION GUIDE**