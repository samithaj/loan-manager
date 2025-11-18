-- Migration: 0008_bike_lifecycle_system.sql
-- Description: Complete bike lifecycle management system
-- Implements: Second-hand bike tracking, stock numbers, transfers, expenses, sales, commissions
-- Run: psql "$DATABASE_URL" -f database/migrations/0008_bike_lifecycle_system.sql
-- Author: Claude
-- Date: 2025-11-18

-- ============================================================================
-- PHASE 1: DATABASE SCHEMA
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Task 1.1: Create Companies Table
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS companies (
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

-- Seed data for two companies
INSERT INTO companies (id, name, district) VALUES
    ('MA', 'SK Management', 'Monaragala'),
    ('IN', 'SK Investment', 'Badulla')
ON CONFLICT (id) DO NOTHING;

-- Index on is_active for filtering
CREATE INDEX IF NOT EXISTS idx_companies_is_active ON companies(is_active);

-- Trigger for updated_at
DROP TRIGGER IF EXISTS update_companies_updated_at ON companies;
CREATE TRIGGER update_companies_updated_at
    BEFORE UPDATE ON companies
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ----------------------------------------------------------------------------
-- Task 1.2: Extend Offices Table (Add Company Relationship)
-- ----------------------------------------------------------------------------

-- Add company_id to offices (nullable initially for data migration)
ALTER TABLE offices
    ADD COLUMN IF NOT EXISTS company_id TEXT REFERENCES companies(id);

-- Add repair center flag
ALTER TABLE offices
    ADD COLUMN IF NOT EXISTS is_repair_center BOOLEAN NOT NULL DEFAULT FALSE;

-- Create index on company_id
CREATE INDEX IF NOT EXISTS idx_offices_company_id ON offices(company_id);

-- ----------------------------------------------------------------------------
-- IMPORTANT: MANUAL DATA MAPPING REQUIRED
-- ----------------------------------------------------------------------------
-- You must map each branch/office to the correct company based on your data.
-- Example mapping (update these with actual office IDs from your database):
--
-- Monaragala branches (MA):
-- UPDATE offices SET company_id = 'MA' WHERE id IN ('WW', 'BK', 'BT', 'MO', 'HP', 'BW', ...);
--
-- Badulla branches (IN):
-- UPDATE offices SET company_id = 'IN' WHERE id IN (...);
--
-- Mark repair centers:
-- UPDATE offices SET is_repair_center = TRUE WHERE id IN ('BRC', ...);
--
-- After mapping all offices, uncomment the line below to enforce NOT NULL:
-- ALTER TABLE offices ALTER COLUMN company_id SET NOT NULL;
-- ----------------------------------------------------------------------------

-- ----------------------------------------------------------------------------
-- Task 1.3: Create Stock Number Tables
-- ----------------------------------------------------------------------------

-- Sequence tracking per company/branch combination
CREATE TABLE IF NOT EXISTS stock_number_sequences (
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
WHERE c.is_active = TRUE
ON CONFLICT (company_id, branch_id) DO NOTHING;

-- Stock number assignment history
CREATE TABLE IF NOT EXISTS stock_number_assignments (
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

-- Indexes for stock number assignments
CREATE INDEX IF NOT EXISTS idx_stock_assignments_bicycle ON stock_number_assignments(bicycle_id);
CREATE INDEX IF NOT EXISTS idx_stock_assignments_current ON stock_number_assignments(bicycle_id, released_date)
    WHERE released_date IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_stock_assignments_unique_current ON stock_number_assignments(bicycle_id)
    WHERE released_date IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_stock_number_unique ON stock_number_assignments(full_stock_number);

-- Triggers for updated_at
DROP TRIGGER IF EXISTS update_stock_number_sequences_updated_at ON stock_number_sequences;
CREATE TRIGGER update_stock_number_sequences_updated_at
    BEFORE UPDATE ON stock_number_sequences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_stock_number_assignments_updated_at ON stock_number_assignments;
CREATE TRIGGER update_stock_number_assignments_updated_at
    BEFORE UPDATE ON stock_number_assignments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ----------------------------------------------------------------------------
-- Task 1.4: Create Bicycle Transfer Table
-- ----------------------------------------------------------------------------

-- Create transfer status enum if it doesn't exist
DO $$ BEGIN
    CREATE TYPE transfer_status AS ENUM (
        'PENDING', 'APPROVED', 'IN_TRANSIT', 'COMPLETED', 'REJECTED', 'CANCELLED'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Bicycle transfers between branches
CREATE TABLE IF NOT EXISTS bicycle_transfers (
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

-- Indexes for bicycle transfers
CREATE INDEX IF NOT EXISTS idx_transfers_bicycle ON bicycle_transfers(bicycle_id);
CREATE INDEX IF NOT EXISTS idx_transfers_status ON bicycle_transfers(status);
CREATE INDEX IF NOT EXISTS idx_transfers_from_branch ON bicycle_transfers(from_branch_id);
CREATE INDEX IF NOT EXISTS idx_transfers_to_branch ON bicycle_transfers(to_branch_id);

-- Trigger for updated_at
DROP TRIGGER IF EXISTS update_bicycle_transfers_updated_at ON bicycle_transfers;
CREATE TRIGGER update_bicycle_transfers_updated_at
    BEFORE UPDATE ON bicycle_transfers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ----------------------------------------------------------------------------
-- Task 1.5: Create Bicycle Branch Expenses Table
-- ----------------------------------------------------------------------------

-- Create expense category enum if it doesn't exist
DO $$ BEGIN
    CREATE TYPE expense_category AS ENUM (
        'TRANSPORT', 'MINOR_REPAIR', 'LICENSE_RENEWAL', 'INSURANCE',
        'CLEANING', 'DOCUMENTATION', 'STORAGE', 'OTHER'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Branch-level expenses per bicycle
CREATE TABLE IF NOT EXISTS bicycle_branch_expenses (
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

-- Indexes for branch expenses
CREATE INDEX IF NOT EXISTS idx_branch_expenses_bicycle ON bicycle_branch_expenses(bicycle_id);
CREATE INDEX IF NOT EXISTS idx_branch_expenses_branch ON bicycle_branch_expenses(branch_id);
CREATE INDEX IF NOT EXISTS idx_branch_expenses_date ON bicycle_branch_expenses(expense_date);

-- Trigger for updated_at
DROP TRIGGER IF EXISTS update_bicycle_branch_expenses_updated_at ON bicycle_branch_expenses;
CREATE TRIGGER update_bicycle_branch_expenses_updated_at
    BEFORE UPDATE ON bicycle_branch_expenses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ----------------------------------------------------------------------------
-- Task 1.6: Create Bicycle Sales Table
-- ----------------------------------------------------------------------------

-- Create payment method enum if it doesn't exist
DO $$ BEGIN
    CREATE TYPE sale_payment_method AS ENUM (
        'CASH', 'FINANCE', 'TRADE_IN', 'BANK_TRANSFER', 'MIXED'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Bicycle sale transactions
CREATE TABLE IF NOT EXISTS bicycle_sales (
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

    -- Computed fields (updated by trigger or application logic)
    total_cost DECIMAL(12, 2),  -- Purchase + branch expenses + garage
    profit_or_loss DECIMAL(12, 2),  -- Selling price - total cost

    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT positive_selling_price CHECK (selling_price > 0),
    CONSTRAINT valid_trade_in CHECK (
        (payment_method = 'TRADE_IN' AND trade_in_bicycle_id IS NOT NULL) OR
        (payment_method != 'TRADE_IN')
    )
);

-- Indexes for bicycle sales
CREATE UNIQUE INDEX IF NOT EXISTS idx_sales_bicycle ON bicycle_sales(bicycle_id);  -- One sale per bike
CREATE INDEX IF NOT EXISTS idx_sales_branch ON bicycle_sales(selling_branch_id);
CREATE INDEX IF NOT EXISTS idx_sales_company ON bicycle_sales(selling_company_id);
CREATE INDEX IF NOT EXISTS idx_sales_date ON bicycle_sales(sale_date);
CREATE INDEX IF NOT EXISTS idx_sales_customer_phone ON bicycle_sales(customer_phone);

-- Trigger for updated_at
DROP TRIGGER IF EXISTS update_bicycle_sales_updated_at ON bicycle_sales;
CREATE TRIGGER update_bicycle_sales_updated_at
    BEFORE UPDATE ON bicycle_sales
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ----------------------------------------------------------------------------
-- Task 1.7: Extend Bicycles Table
-- ----------------------------------------------------------------------------

-- Add company and business model fields
ALTER TABLE bicycles
    ADD COLUMN IF NOT EXISTS company_id TEXT REFERENCES companies(id);

ALTER TABLE bicycles
    ADD COLUMN IF NOT EXISTS business_model TEXT NOT NULL DEFAULT 'HIRE_PURCHASE';

ALTER TABLE bicycles
    ADD COLUMN IF NOT EXISTS current_stock_number TEXT;

ALTER TABLE bicycles
    ADD COLUMN IF NOT EXISTS current_branch_id TEXT REFERENCES offices(id);

-- Add procurement details (from November notebook)
ALTER TABLE bicycles
    ADD COLUMN IF NOT EXISTS procurement_date DATE;

ALTER TABLE bicycles
    ADD COLUMN IF NOT EXISTS procurement_source TEXT;

ALTER TABLE bicycles
    ADD COLUMN IF NOT EXISTS bought_method TEXT;

ALTER TABLE bicycles
    ADD COLUMN IF NOT EXISTS hand_amount DECIMAL(12, 2);

ALTER TABLE bicycles
    ADD COLUMN IF NOT EXISTS settlement_amount DECIMAL(12, 2);

ALTER TABLE bicycles
    ADD COLUMN IF NOT EXISTS payment_branch_id TEXT REFERENCES offices(id);

ALTER TABLE bicycles
    ADD COLUMN IF NOT EXISTS cr_location TEXT;

ALTER TABLE bicycles
    ADD COLUMN IF NOT EXISTS buyer_employee_id TEXT REFERENCES staff(id);

-- Add control flags (from notebook)
ALTER TABLE bicycles
    ADD COLUMN IF NOT EXISTS first_od TEXT;

ALTER TABLE bicycles
    ADD COLUMN IF NOT EXISTS ldate DATE;

ALTER TABLE bicycles
    ADD COLUMN IF NOT EXISTS sk_flag BOOLEAN DEFAULT FALSE;

ALTER TABLE bicycles
    ADD COLUMN IF NOT EXISTS ls_flag BOOLEAN DEFAULT FALSE;

ALTER TABLE bicycles
    ADD COLUMN IF NOT EXISTS caller TEXT;

ALTER TABLE bicycles
    ADD COLUMN IF NOT EXISTS house_use BOOLEAN DEFAULT FALSE;

-- Add cost tracking field
ALTER TABLE bicycles
    ADD COLUMN IF NOT EXISTS total_branch_expenses DECIMAL(12, 2) DEFAULT 0;

-- Add generated column for total expenses (only if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'bicycles' AND column_name = 'total_expenses'
    ) THEN
        ALTER TABLE bicycles
            ADD COLUMN total_expenses DECIMAL(12, 2) GENERATED ALWAYS AS (
                COALESCE(base_purchase_price, 0) +
                COALESCE(total_repair_cost, 0) +
                COALESCE(total_branch_expenses, 0)
            ) STORED;
    END IF;
END $$;

-- Add sale tracking fields
ALTER TABLE bicycles
    ADD COLUMN IF NOT EXISTS sold_date DATE;

ALTER TABLE bicycles
    ADD COLUMN IF NOT EXISTS selling_price DECIMAL(12, 2);

-- Add generated column for profit/loss (only if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'bicycles' AND column_name = 'profit_or_loss'
    ) THEN
        ALTER TABLE bicycles
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
    END IF;
END $$;

-- Extend bicycle_status enum with new values
DO $$
BEGIN
    -- Check if we need to update the enum
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum e
        JOIN pg_type t ON e.enumtypid = t.oid
        WHERE t.typname = 'bicycle_status' AND e.enumlabel = 'IN_STOCK'
    ) THEN
        -- Add new values to existing enum
        ALTER TYPE bicycle_status ADD VALUE IF NOT EXISTS 'IN_STOCK';
        ALTER TYPE bicycle_status ADD VALUE IF NOT EXISTS 'ALLOCATED';
        ALTER TYPE bicycle_status ADD VALUE IF NOT EXISTS 'IN_TRANSIT';
        ALTER TYPE bicycle_status ADD VALUE IF NOT EXISTS 'WRITTEN_OFF';
    END IF;
END $$;

-- Create new indexes
CREATE INDEX IF NOT EXISTS idx_bicycles_company ON bicycles(company_id);
CREATE INDEX IF NOT EXISTS idx_bicycles_business_model ON bicycles(business_model);
CREATE INDEX IF NOT EXISTS idx_bicycles_current_stock_number ON bicycles(current_stock_number);
CREATE INDEX IF NOT EXISTS idx_bicycles_current_branch ON bicycles(current_branch_id);
CREATE INDEX IF NOT EXISTS idx_bicycles_procurement_date ON bicycles(procurement_date);
CREATE INDEX IF NOT EXISTS idx_bicycles_sold_date ON bicycles(sold_date);

-- Add constraints (using DO blocks to avoid errors if they already exist)
DO $$
BEGIN
    ALTER TABLE bicycles
        ADD CONSTRAINT valid_business_model
            CHECK (business_model IN ('HIRE_PURCHASE', 'DIRECT_SALE', 'STOCK'));
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$
BEGIN
    ALTER TABLE bicycles
        ADD CONSTRAINT valid_procurement_source
            CHECK (procurement_source IN ('CUSTOMER', 'AUCTION', 'DEALER', 'TRADE_IN', 'OTHER'));
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- ----------------------------------------------------------------------------
-- Task 1.8: Extend Repair Jobs Table
-- ----------------------------------------------------------------------------

-- Add job category column
ALTER TABLE repair_jobs
    ADD COLUMN IF NOT EXISTS job_category TEXT DEFAULT 'CUSTOMER_REPAIR';

-- Add constraint
DO $$
BEGIN
    ALTER TABLE repair_jobs
        ADD CONSTRAINT valid_job_category
            CHECK (job_category IN ('PRE_SALE_PREP', 'CUSTOMER_REPAIR', 'WARRANTY', 'MAINTENANCE'));
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create index
CREATE INDEX IF NOT EXISTS idx_repair_jobs_category ON repair_jobs(job_category);

-- Update existing FULL_OVERHAUL_BEFORE_SALE jobs to PRE_SALE_PREP category
UPDATE repair_jobs
SET job_category = 'PRE_SALE_PREP'
WHERE job_type = 'FULL_OVERHAUL_BEFORE_SALE' AND job_category = 'CUSTOMER_REPAIR';

-- ----------------------------------------------------------------------------
-- Task 1.9: Extend Bonus System for Commissions
-- ----------------------------------------------------------------------------

-- Add bike-specific fields to bonus_rules
ALTER TABLE bonus_rules
    ADD COLUMN IF NOT EXISTS applies_to_bike_sales BOOLEAN DEFAULT FALSE;

ALTER TABLE bonus_rules
    ADD COLUMN IF NOT EXISTS commission_base TEXT DEFAULT 'PROFIT';

ALTER TABLE bonus_rules
    ADD COLUMN IF NOT EXISTS buyer_branch_percent DECIMAL(5, 2);

ALTER TABLE bonus_rules
    ADD COLUMN IF NOT EXISTS seller_branch_percent DECIMAL(5, 2);

-- Add constraints for commission rules
DO $$
BEGIN
    ALTER TABLE bonus_rules
        ADD CONSTRAINT valid_commission_base
            CHECK (commission_base IN ('PROFIT', 'SALE_PRICE'));
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$
BEGIN
    ALTER TABLE bonus_rules
        ADD CONSTRAINT valid_commission_percentages
            CHECK (
                (applies_to_bike_sales = FALSE) OR
                (buyer_branch_percent >= 0 AND seller_branch_percent >= 0 AND
                 buyer_branch_percent + seller_branch_percent = 100)
            );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Add bike sale reference to bonus_payments
ALTER TABLE bonus_payments
    ADD COLUMN IF NOT EXISTS bicycle_sale_id TEXT REFERENCES bicycle_sales(id);

ALTER TABLE bonus_payments
    ADD COLUMN IF NOT EXISTS commission_type TEXT;

-- Add constraint for commission type
DO $$
BEGIN
    ALTER TABLE bonus_payments
        ADD CONSTRAINT valid_commission_type
            CHECK (commission_type IN ('BUYER', 'SELLER', NULL));
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create index on bicycle_sale_id
CREATE INDEX IF NOT EXISTS idx_bonus_payments_bike_sale ON bonus_payments(bicycle_sale_id);

-- Insert default bike commission rule
INSERT INTO bonus_rules (
    id, name, description, rule_type, applies_to_roles, applies_to_bike_sales,
    commission_base, buyer_branch_percent, seller_branch_percent,
    min_achievement_percentage, is_active, effective_from
) VALUES (
    'BIKE-COMM-001',
    'Default Bike Sale Commission',
    'Standard commission split for bike sales between buyer and seller branches',
    'COMMISSION',
    ARRAY['BRANCH_MANAGER', 'SALES_STAFF']::TEXT[],
    TRUE,
    'PROFIT',
    40.00,  -- 40% to buyer branch
    60.00,  -- 60% to seller branch
    0.00,
    TRUE,
    CURRENT_DATE
) ON CONFLICT (id) DO NOTHING;

-- ----------------------------------------------------------------------------
-- Task 1.10: Create Database Views
-- ----------------------------------------------------------------------------

-- View 1: Bike Cost Summary (like summery.xlsx)
CREATE MATERIALIZED VIEW IF NOT EXISTS v_bike_cost_summary AS
SELECT
    b.id AS bicycle_id,
    b.license_plate AS bike_no,
    b.current_branch_id AS branch_id,
    o.name AS branch_name,
    b.current_stock_number,
    b.model AS model_name,
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

-- Indexes for v_bike_cost_summary
CREATE UNIQUE INDEX IF NOT EXISTS idx_v_bike_cost_summary_id ON v_bike_cost_summary(bicycle_id);
CREATE INDEX IF NOT EXISTS idx_v_bike_cost_summary_branch ON v_bike_cost_summary(branch_id);
CREATE INDEX IF NOT EXISTS idx_v_bike_cost_summary_status ON v_bike_cost_summary(stock_status);

-- View 2: Branch Stock Status
CREATE MATERIALIZED VIEW IF NOT EXISTS v_branch_stock_status AS
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
LEFT JOIN companies c ON o.company_id = c.id
WHERE b.business_model IN ('DIRECT_SALE', 'STOCK')
GROUP BY o.id, o.name, c.id, c.name, b.status;

-- Indexes for v_branch_stock_status
CREATE INDEX IF NOT EXISTS idx_v_branch_stock_status_branch ON v_branch_stock_status(branch_id);
CREATE INDEX IF NOT EXISTS idx_v_branch_stock_status_company ON v_branch_stock_status(company_id);

-- View 3: Sale Commission Summary
-- Note: This view joins with bicycle_sales to get branch information since bonus_payments
-- doesn't directly have branch_id, we derive it from the sale record
CREATE MATERIALIZED VIEW IF NOT EXISTS v_commission_summary AS
SELECT
    bp.period_start,
    bp.period_end,
    CASE
        WHEN bp.commission_type = 'SELLER' THEN bs.selling_branch_id
        ELSE NULL  -- Buyer branch would need to be tracked separately
    END AS branch_id,
    o.name AS branch_name,
    bp.commission_type,
    COUNT(DISTINCT bp.bicycle_sale_id) AS sale_count,
    SUM(bp.bonus_amount) AS total_commission
FROM bonus_payments bp
JOIN bicycle_sales bs ON bp.bicycle_sale_id = bs.id
LEFT JOIN offices o ON (
    CASE
        WHEN bp.commission_type = 'SELLER' THEN bs.selling_branch_id
        ELSE NULL
    END
) = o.id
WHERE bp.bicycle_sale_id IS NOT NULL
GROUP BY bp.period_start, bp.period_end, branch_id, o.name, bp.commission_type;

-- Indexes for v_commission_summary
CREATE INDEX IF NOT EXISTS idx_v_commission_summary_branch ON v_commission_summary(branch_id);
CREATE INDEX IF NOT EXISTS idx_v_commission_summary_period ON v_commission_summary(period_start, period_end);

-- Refresh function for all materialized views
CREATE OR REPLACE FUNCTION refresh_bike_materialized_views()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY v_bike_cost_summary;
    REFRESH MATERIALIZED VIEW CONCURRENTLY v_branch_stock_status;
    REFRESH MATERIALIZED VIEW CONCURRENTLY v_commission_summary;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- To verify the migration, run:
-- psql -d loan_manager -c "\dt" - verify all new tables
-- psql -d loan_manager -c "\d+ bicycles" - verify bicycle extensions
-- psql -d loan_manager -c "SELECT * FROM companies" - verify seed data
-- psql -d loan_manager -c "\dT" - verify new enums

-- IMPORTANT NEXT STEPS:
-- 1. Map all offices to companies by updating offices.company_id
-- 2. Set offices.company_id to NOT NULL after mapping
-- 3. Update existing bicycles with company_id based on branch_id
-- 4. Run: SELECT refresh_bike_materialized_views(); to populate views
