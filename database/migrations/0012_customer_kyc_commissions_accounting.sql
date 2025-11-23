-- ============================================================================
-- Migration: Customer KYC, Commissions, and Accounting Modules
-- Version: 0012
-- Description: Adds Customer KYC (guarantors, employment, bank accounts),
--              Commission calculation engine, and Accounting system
--              (chart of accounts, journal entries, petty cash)
-- ============================================================================

-- ============================================================================
-- 1. Enums
-- ============================================================================

-- Employment Type enum
DO $$ BEGIN
    CREATE TYPE employment_type_enum AS ENUM (
        'PERMANENT',
        'CONTRACT',
        'SELF_EMPLOYED',
        'BUSINESS_OWNER',
        'RETIRED',
        'UNEMPLOYED'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Income Frequency enum
DO $$ BEGIN
    CREATE TYPE income_frequency_enum AS ENUM (
        'DAILY',
        'WEEKLY',
        'MONTHLY',
        'ANNUAL'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Bank Account Type enum
DO $$ BEGIN
    CREATE TYPE bank_account_type_enum AS ENUM (
        'SAVINGS',
        'CURRENT',
        'FIXED_DEPOSIT',
        'SALARY'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Bank Account Status enum
DO $$ BEGIN
    CREATE TYPE bank_account_status_enum AS ENUM (
        'ACTIVE',
        'INACTIVE',
        'CLOSED'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Commission Type enum
DO $$ BEGIN
    CREATE TYPE commission_type_enum AS ENUM (
        'VEHICLE_SALE',
        'LOAN_ORIGINATION',
        'INSURANCE_SALE',
        'SERVICE'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Formula Type enum
DO $$ BEGIN
    CREATE TYPE formula_type_enum AS ENUM (
        'FLAT_RATE',
        'PERCENTAGE_OF_SALE',
        'PERCENTAGE_OF_PROFIT',
        'TIERED'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Tier Basis enum
DO $$ BEGIN
    CREATE TYPE tier_basis_enum AS ENUM (
        'SALE_AMOUNT',
        'PROFIT_AMOUNT',
        'UNIT_COUNT'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Account Category enum
DO $$ BEGIN
    CREATE TYPE account_category_enum AS ENUM (
        'ASSET',
        'LIABILITY',
        'EQUITY',
        'REVENUE',
        'EXPENSE'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Chart Account Type enum
DO $$ BEGIN
    CREATE TYPE chart_account_type_enum AS ENUM (
        'CURRENT_ASSET',
        'FIXED_ASSET',
        'CURRENT_LIABILITY',
        'LONG_TERM_LIABILITY',
        'EQUITY',
        'OPERATING_REVENUE',
        'NON_OPERATING_REVENUE',
        'OPERATING_EXPENSE',
        'NON_OPERATING_EXPENSE',
        'COST_OF_GOODS_SOLD',
        'INVENTORY',
        'ACCOUNTS_RECEIVABLE',
        'ACCOUNTS_PAYABLE',
        'CASH',
        'BANK'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Journal Entry Type enum
DO $$ BEGIN
    CREATE TYPE journal_entry_type_enum AS ENUM (
        'GENERAL',
        'VEHICLE_PURCHASE',
        'VEHICLE_SALE',
        'REPAIR_EXPENSE',
        'PETTY_CASH',
        'COMMISSION_PAYMENT',
        'SALARY_PAYMENT',
        'LOAN_DISBURSEMENT',
        'LOAN_REPAYMENT',
        'DEPRECIATION',
        'ADJUSTMENT'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Journal Entry Status enum
DO $$ BEGIN
    CREATE TYPE journal_entry_status_enum AS ENUM (
        'DRAFT',
        'POSTED',
        'VOID'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Voucher Type enum
DO $$ BEGIN
    CREATE TYPE voucher_type_enum AS ENUM (
        'RECEIPT',
        'DISBURSEMENT'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Voucher Status enum
DO $$ BEGIN
    CREATE TYPE voucher_status_enum AS ENUM (
        'DRAFT',
        'APPROVED',
        'REJECTED',
        'POSTED',
        'VOID'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- ============================================================================
-- 2. Customer KYC Tables
-- ============================================================================

-- Customer Guarantors Table
CREATE TABLE IF NOT EXISTS customer_guarantors (
    id VARCHAR(36) PRIMARY KEY,
    customer_id VARCHAR(36) NOT NULL,

    -- Personal Information
    full_name VARCHAR(200) NOT NULL,
    nic VARCHAR(20) NOT NULL,
    date_of_birth DATE NOT NULL,
    mobile VARCHAR(15) NOT NULL,
    email VARCHAR(100),

    -- Address
    address_line1 VARCHAR(200) NOT NULL,
    address_line2 VARCHAR(200),
    city VARCHAR(100) NOT NULL,
    province VARCHAR(100),
    postal_code VARCHAR(10),

    -- Employment & Income
    employer_name VARCHAR(200),
    job_title VARCHAR(100),
    employment_type employment_type_enum,
    monthly_income DECIMAL(15, 2),
    years_employed DECIMAL(5, 2),

    -- Relationship
    relationship VARCHAR(100) NOT NULL,
    is_primary BOOLEAN DEFAULT FALSE,

    -- Verification
    is_verified BOOLEAN DEFAULT FALSE,
    verified_at TIMESTAMP,
    verified_by VARCHAR(100),

    -- Documents
    nic_document_url VARCHAR(500),
    salary_slip_url VARCHAR(500),

    -- Metadata
    notes TEXT,
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_guarantor_customer FOREIGN KEY (customer_id) REFERENCES clients(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_customer_guarantors_customer_id ON customer_guarantors(customer_id);
CREATE INDEX IF NOT EXISTS idx_customer_guarantors_nic ON customer_guarantors(nic);
CREATE INDEX IF NOT EXISTS idx_customer_guarantors_is_primary ON customer_guarantors(customer_id, is_primary) WHERE is_primary = TRUE;

-- Customer Employment Table
CREATE TABLE IF NOT EXISTS customer_employment (
    id VARCHAR(36) PRIMARY KEY,
    customer_id VARCHAR(36) NOT NULL,

    -- Employment Details
    employer_name VARCHAR(200) NOT NULL,
    job_title VARCHAR(100) NOT NULL,
    employment_type employment_type_enum NOT NULL,
    industry VARCHAR(100),

    -- Employment Period
    start_date DATE NOT NULL,
    end_date DATE,
    is_current BOOLEAN DEFAULT TRUE,

    -- Income
    gross_income DECIMAL(15, 2) NOT NULL,
    income_frequency income_frequency_enum NOT NULL,
    monthly_income DECIMAL(15, 2) NOT NULL,

    -- Contact Information
    employer_phone VARCHAR(15),
    employer_email VARCHAR(100),
    employer_address TEXT,

    -- Verification
    is_verified BOOLEAN DEFAULT FALSE,
    verified_at TIMESTAMP,
    verified_by VARCHAR(100),
    verification_method VARCHAR(50),

    -- Documents
    employment_letter_url VARCHAR(500),
    salary_slip_url VARCHAR(500),

    -- Metadata
    notes TEXT,
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_employment_customer FOREIGN KEY (customer_id) REFERENCES clients(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_customer_employment_customer_id ON customer_employment(customer_id);
CREATE INDEX IF NOT EXISTS idx_customer_employment_is_current ON customer_employment(customer_id, is_current) WHERE is_current = TRUE;

-- Customer Bank Accounts Table
CREATE TABLE IF NOT EXISTS customer_bank_accounts (
    id VARCHAR(36) PRIMARY KEY,
    customer_id VARCHAR(36) NOT NULL,

    -- Bank Details
    bank_name VARCHAR(100) NOT NULL,
    branch_name VARCHAR(100),
    account_number VARCHAR(50) NOT NULL,
    account_type bank_account_type_enum NOT NULL,
    account_holder_name VARCHAR(200) NOT NULL,

    -- Status
    status bank_account_status_enum DEFAULT 'ACTIVE',
    is_primary BOOLEAN DEFAULT FALSE,
    is_salary_account BOOLEAN DEFAULT FALSE,

    -- Verification
    is_verified BOOLEAN DEFAULT FALSE,
    verified_at TIMESTAMP,
    verified_by VARCHAR(100),
    verification_method VARCHAR(50),

    -- Documents
    bank_statement_url VARCHAR(500),

    -- Metadata
    notes TEXT,
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_bank_account_customer FOREIGN KEY (customer_id) REFERENCES clients(id) ON DELETE CASCADE,
    CONSTRAINT unique_customer_account_number UNIQUE (customer_id, account_number)
);

CREATE INDEX IF NOT EXISTS idx_customer_bank_accounts_customer_id ON customer_bank_accounts(customer_id);
CREATE INDEX IF NOT EXISTS idx_customer_bank_accounts_is_primary ON customer_bank_accounts(customer_id, is_primary) WHERE is_primary = TRUE;

-- ============================================================================
-- 3. Commission Tables
-- ============================================================================

-- Commission Rules Table
CREATE TABLE IF NOT EXISTS commission_rules (
    id VARCHAR(36) PRIMARY KEY,

    -- Rule Identification
    rule_name VARCHAR(200) NOT NULL,
    commission_type commission_type_enum NOT NULL,
    description TEXT,

    -- Formula Configuration
    formula_type formula_type_enum NOT NULL,
    rate DECIMAL(10, 4),
    tier_basis tier_basis_enum,
    tier_configuration JSONB,

    -- Constraints
    min_amount DECIMAL(15, 2),
    max_amount DECIMAL(15, 2),

    -- Applicability
    applicable_roles JSONB NOT NULL DEFAULT '[]'::jsonb,
    branch_id VARCHAR(36),
    vehicle_condition VARCHAR(20),

    -- Effective Dates
    effective_from DATE NOT NULL,
    effective_until DATE,

    -- Status & Priority
    is_active BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 0,

    -- Metadata
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_commission_rules_type ON commission_rules(commission_type);
CREATE INDEX IF NOT EXISTS idx_commission_rules_active ON commission_rules(is_active, effective_from, effective_until);
CREATE INDEX IF NOT EXISTS idx_commission_rules_roles ON commission_rules USING gin(applicable_roles);
CREATE INDEX IF NOT EXISTS idx_commission_rules_priority ON commission_rules(priority DESC);

-- ============================================================================
-- 4. Accounting Tables
-- ============================================================================

-- Chart of Accounts Table
CREATE TABLE IF NOT EXISTS chart_of_accounts (
    id VARCHAR(36) PRIMARY KEY,

    -- Account Identification
    account_code VARCHAR(20) NOT NULL UNIQUE,
    account_name VARCHAR(200) NOT NULL,
    description TEXT,

    -- Classification
    category account_category_enum NOT NULL,
    account_type chart_account_type_enum NOT NULL,
    normal_balance VARCHAR(10) NOT NULL CHECK (normal_balance IN ('DEBIT', 'CREDIT')),

    -- Hierarchy
    parent_account_id VARCHAR(36),
    level INTEGER DEFAULT 0,
    is_header BOOLEAN DEFAULT FALSE,

    -- Status & Flags
    is_active BOOLEAN DEFAULT TRUE,
    is_system BOOLEAN DEFAULT FALSE,

    -- Branch Assignment
    branch_id VARCHAR(36),

    -- Metadata
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_coa_parent FOREIGN KEY (parent_account_id) REFERENCES chart_of_accounts(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_coa_code ON chart_of_accounts(account_code);
CREATE INDEX IF NOT EXISTS idx_coa_category ON chart_of_accounts(category);
CREATE INDEX IF NOT EXISTS idx_coa_parent ON chart_of_accounts(parent_account_id);
CREATE INDEX IF NOT EXISTS idx_coa_active ON chart_of_accounts(is_active);

-- Journal Entries Table
CREATE TABLE IF NOT EXISTS journal_entries (
    id VARCHAR(36) PRIMARY KEY,

    -- Entry Identification
    entry_number VARCHAR(50) NOT NULL UNIQUE,
    entry_date DATE NOT NULL,
    entry_type journal_entry_type_enum NOT NULL,

    -- Description & Reference
    description TEXT NOT NULL,
    reference_number VARCHAR(100),
    reference_type VARCHAR(50),
    reference_id VARCHAR(36),

    -- Branch Assignment
    branch_id VARCHAR(36),

    -- Totals
    total_debit DECIMAL(15, 2) NOT NULL,
    total_credit DECIMAL(15, 2) NOT NULL,

    -- Status
    status journal_entry_status_enum DEFAULT 'DRAFT',

    -- Posting Information
    posted_at TIMESTAMP,
    posted_by VARCHAR(100),

    -- Void Information
    voided_at TIMESTAMP,
    voided_by VARCHAR(100),
    void_reason TEXT,

    -- Metadata
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT check_balanced_entry CHECK (ABS(total_debit - total_credit) < 0.01)
);

CREATE INDEX IF NOT EXISTS idx_je_number ON journal_entries(entry_number);
CREATE INDEX IF NOT EXISTS idx_je_date ON journal_entries(entry_date);
CREATE INDEX IF NOT EXISTS idx_je_type ON journal_entries(entry_type);
CREATE INDEX IF NOT EXISTS idx_je_status ON journal_entries(status);
CREATE INDEX IF NOT EXISTS idx_je_reference ON journal_entries(reference_type, reference_id);

-- Journal Entry Lines Table
CREATE TABLE IF NOT EXISTS journal_entry_lines (
    id VARCHAR(36) PRIMARY KEY,
    journal_entry_id VARCHAR(36) NOT NULL,
    account_id VARCHAR(36) NOT NULL,

    -- Line Details
    description TEXT,
    debit_amount DECIMAL(15, 2),
    credit_amount DECIMAL(15, 2),

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_jel_entry FOREIGN KEY (journal_entry_id) REFERENCES journal_entries(id) ON DELETE CASCADE,
    CONSTRAINT fk_jel_account FOREIGN KEY (account_id) REFERENCES chart_of_accounts(id) ON DELETE RESTRICT,
    CONSTRAINT check_debit_or_credit CHECK (
        (debit_amount IS NOT NULL AND credit_amount IS NULL) OR
        (debit_amount IS NULL AND credit_amount IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_jel_entry ON journal_entry_lines(journal_entry_id);
CREATE INDEX IF NOT EXISTS idx_jel_account ON journal_entry_lines(account_id);

-- ============================================================================
-- 5. Petty Cash Tables
-- ============================================================================

-- Petty Cash Float Table
CREATE TABLE IF NOT EXISTS petty_cash_floats (
    id VARCHAR(36) PRIMARY KEY,

    -- Float Identification
    float_name VARCHAR(100) NOT NULL,
    branch_id VARCHAR(36) NOT NULL,

    -- Custodian
    custodian_id VARCHAR(36) NOT NULL,
    custodian_name VARCHAR(200) NOT NULL,

    -- Balances
    opening_balance DECIMAL(15, 2) NOT NULL,
    current_balance DECIMAL(15, 2) NOT NULL,
    reconciled_balance DECIMAL(15, 2),

    -- Reconciliation
    reconciled_at TIMESTAMP,
    reconciled_by VARCHAR(100),
    reconciliation_notes TEXT,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,

    -- Metadata
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pcf_branch ON petty_cash_floats(branch_id);
CREATE INDEX IF NOT EXISTS idx_pcf_custodian ON petty_cash_floats(custodian_id);
CREATE INDEX IF NOT EXISTS idx_pcf_active ON petty_cash_floats(is_active);

-- Petty Cash Vouchers Table
CREATE TABLE IF NOT EXISTS petty_cash_vouchers (
    id VARCHAR(36) PRIMARY KEY,
    petty_cash_float_id VARCHAR(36) NOT NULL,

    -- Voucher Identification
    voucher_number VARCHAR(50) NOT NULL UNIQUE,
    voucher_date DATE NOT NULL,
    voucher_type voucher_type_enum NOT NULL,

    -- Amount & Details
    amount DECIMAL(15, 2) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(100),

    -- Payee/Payer
    payee_name VARCHAR(200),
    payee_contact VARCHAR(100),

    -- Branch Assignment
    branch_id VARCHAR(36) NOT NULL,

    -- Approval
    status voucher_status_enum DEFAULT 'DRAFT',
    approved_at TIMESTAMP,
    approved_by VARCHAR(100),
    rejected_at TIMESTAMP,
    rejected_by VARCHAR(100),
    rejection_reason TEXT,

    -- Journal Entry Link
    journal_entry_id VARCHAR(36),

    -- Documents
    receipt_url VARCHAR(500),

    -- Metadata
    notes TEXT,
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_pcv_float FOREIGN KEY (petty_cash_float_id) REFERENCES petty_cash_floats(id) ON DELETE RESTRICT,
    CONSTRAINT fk_pcv_journal FOREIGN KEY (journal_entry_id) REFERENCES journal_entries(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_pcv_float ON petty_cash_vouchers(petty_cash_float_id);
CREATE INDEX IF NOT EXISTS idx_pcv_number ON petty_cash_vouchers(voucher_number);
CREATE INDEX IF NOT EXISTS idx_pcv_date ON petty_cash_vouchers(voucher_date);
CREATE INDEX IF NOT EXISTS idx_pcv_status ON petty_cash_vouchers(status);
CREATE INDEX IF NOT EXISTS idx_pcv_branch ON petty_cash_vouchers(branch_id);

-- ============================================================================
-- 6. Update Triggers
-- ============================================================================

-- Update timestamp trigger function (reuse existing if available)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to all tables
DROP TRIGGER IF EXISTS update_customer_guarantors_updated_at ON customer_guarantors;
CREATE TRIGGER update_customer_guarantors_updated_at BEFORE UPDATE ON customer_guarantors FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_customer_employment_updated_at ON customer_employment;
CREATE TRIGGER update_customer_employment_updated_at BEFORE UPDATE ON customer_employment FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_customer_bank_accounts_updated_at ON customer_bank_accounts;
CREATE TRIGGER update_customer_bank_accounts_updated_at BEFORE UPDATE ON customer_bank_accounts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_commission_rules_updated_at ON commission_rules;
CREATE TRIGGER update_commission_rules_updated_at BEFORE UPDATE ON commission_rules FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_chart_of_accounts_updated_at ON chart_of_accounts;
CREATE TRIGGER update_chart_of_accounts_updated_at BEFORE UPDATE ON chart_of_accounts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_journal_entries_updated_at ON journal_entries;
CREATE TRIGGER update_journal_entries_updated_at BEFORE UPDATE ON journal_entries FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_petty_cash_floats_updated_at ON petty_cash_floats;
CREATE TRIGGER update_petty_cash_floats_updated_at BEFORE UPDATE ON petty_cash_floats FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_petty_cash_vouchers_updated_at ON petty_cash_vouchers;
CREATE TRIGGER update_petty_cash_vouchers_updated_at BEFORE UPDATE ON petty_cash_vouchers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Migration Complete
-- ============================================================================
