-- Migration: Loan Approval System
-- Description: Creates tables for loan application workflow with state machine
-- Date: 2025-11-22

-- ============================================================================
-- 1. Branches Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS branches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    region VARCHAR(100),
    address VARCHAR(500),
    phone VARCHAR(20),
    email VARCHAR(100),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_branches_code ON branches(code);
CREATE INDEX IF NOT EXISTS idx_branches_is_active ON branches(is_active);

COMMENT ON TABLE branches IS 'Branch offices for loan applications';
COMMENT ON COLUMN branches.code IS 'Unique branch code';
COMMENT ON COLUMN branches.name IS 'Branch display name';
COMMENT ON COLUMN branches.region IS 'Geographic region of branch';

-- ============================================================================
-- 2. Application Status Enum
-- ============================================================================

DO $$ BEGIN
    CREATE TYPE application_status AS ENUM (
        'DRAFT',
        'SUBMITTED',
        'UNDER_REVIEW',
        'NEEDS_MORE_INFO',
        'APPROVED',
        'REJECTED',
        'CANCELLED'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

COMMENT ON TYPE application_status IS 'Loan application workflow states';

-- ============================================================================
-- 3. Loan Applications Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS loan_applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_no VARCHAR(50) NOT NULL UNIQUE,
    lmo_user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    branch_id UUID NOT NULL REFERENCES branches(id) ON DELETE RESTRICT,
    requested_amount NUMERIC(12, 2) NOT NULL CHECK (requested_amount > 0),
    tenure_months INTEGER NOT NULL CHECK (tenure_months > 0 AND tenure_months <= 120),
    status application_status NOT NULL DEFAULT 'DRAFT',
    lmo_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    submitted_at TIMESTAMP WITH TIME ZONE,
    reviewed_at TIMESTAMP WITH TIME ZONE,
    decided_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_loan_applications_application_no ON loan_applications(application_no);
CREATE INDEX IF NOT EXISTS idx_loan_applications_lmo_user_id ON loan_applications(lmo_user_id);
CREATE INDEX IF NOT EXISTS idx_loan_applications_branch_id ON loan_applications(branch_id);
CREATE INDEX IF NOT EXISTS idx_loan_applications_status ON loan_applications(status);
CREATE INDEX IF NOT EXISTS idx_loan_applications_created_at ON loan_applications(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_loan_applications_submitted_at ON loan_applications(submitted_at DESC) WHERE submitted_at IS NOT NULL;

COMMENT ON TABLE loan_applications IS 'Loan applications with state machine workflow';
COMMENT ON COLUMN loan_applications.application_no IS 'Human-readable application number (LA-YYYY-NNNN)';
COMMENT ON COLUMN loan_applications.lmo_user_id IS 'Loan Management Officer who created the application';
COMMENT ON COLUMN loan_applications.status IS 'Current workflow status';

-- ============================================================================
-- 4. Loan Application Customers Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS loan_application_customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL UNIQUE REFERENCES loan_applications(id) ON DELETE CASCADE,
    nic VARCHAR(20) NOT NULL,
    full_name VARCHAR(200) NOT NULL,
    dob DATE,
    address VARCHAR(500) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_loan_application_customers_application_id ON loan_application_customers(application_id);
CREATE INDEX IF NOT EXISTS idx_loan_application_customers_nic ON loan_application_customers(nic);

COMMENT ON TABLE loan_application_customers IS 'Customer details for loan applications';
COMMENT ON COLUMN loan_application_customers.nic IS 'National Identity Card number';

-- ============================================================================
-- 5. Loan Application Vehicles Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS loan_application_vehicles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL UNIQUE REFERENCES loan_applications(id) ON DELETE CASCADE,
    chassis_no VARCHAR(50) NOT NULL,
    engine_no VARCHAR(50),
    make VARCHAR(100) NOT NULL,
    model VARCHAR(100) NOT NULL,
    year INTEGER,
    color VARCHAR(50),
    registration_no VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_loan_application_vehicles_application_id ON loan_application_vehicles(application_id);
CREATE INDEX IF NOT EXISTS idx_loan_application_vehicles_chassis_no ON loan_application_vehicles(chassis_no);
CREATE INDEX IF NOT EXISTS idx_loan_application_vehicles_registration_no ON loan_application_vehicles(registration_no) WHERE registration_no IS NOT NULL;

COMMENT ON TABLE loan_application_vehicles IS 'Vehicle details for loan applications';
COMMENT ON COLUMN loan_application_vehicles.chassis_no IS 'Vehicle chassis number';

-- ============================================================================
-- 6. Document Type Enum
-- ============================================================================

DO $$ BEGIN
    CREATE TYPE loan_document_type AS ENUM (
        'NIC_FRONT',
        'NIC_BACK',
        'CUSTOMER_PHOTO',
        'CUSTOMER_SELFIE',
        'PROOF_OF_ADDRESS',
        'CERTIFICATE_OF_REGISTRATION',
        'VEHICLE_PHOTO_FRONT',
        'VEHICLE_PHOTO_BACK',
        'VEHICLE_PHOTO_SIDE',
        'VEHICLE_PHOTO_DASHBOARD',
        'VEHICLE_PHOTO_ENGINE',
        'BANK_STATEMENT',
        'SALARY_SLIP',
        'OTHER'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

COMMENT ON TYPE loan_document_type IS 'Types of documents for loan applications';

-- ============================================================================
-- 7. Loan Application Documents Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS loan_application_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES loan_applications(id) ON DELETE CASCADE,
    uploaded_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    doc_type loan_document_type NOT NULL,
    file_url VARCHAR(1000) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_size INTEGER NOT NULL CHECK (file_size > 0),
    file_hash VARCHAR(64),
    mime_type VARCHAR(100) NOT NULL,
    meta_json JSONB DEFAULT '{}'::jsonb,
    uploaded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_loan_application_documents_application_id ON loan_application_documents(application_id);
CREATE INDEX IF NOT EXISTS idx_loan_application_documents_doc_type ON loan_application_documents(doc_type);
CREATE INDEX IF NOT EXISTS idx_loan_application_documents_uploaded_at ON loan_application_documents(uploaded_at DESC);

COMMENT ON TABLE loan_application_documents IS 'Uploaded documents for loan applications';
COMMENT ON COLUMN loan_application_documents.file_hash IS 'SHA-256 hash of file content';
COMMENT ON COLUMN loan_application_documents.meta_json IS 'Additional metadata (dimensions, OCR status, etc.)';

-- ============================================================================
-- 8. Decision Type Enum
-- ============================================================================

DO $$ BEGIN
    CREATE TYPE loan_decision_type AS ENUM (
        'APPROVED',
        'REJECTED',
        'NEEDS_MORE_INFO'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

COMMENT ON TYPE loan_decision_type IS 'Types of decisions for loan applications';

-- ============================================================================
-- 9. Loan Application Decisions Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS loan_application_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES loan_applications(id) ON DELETE CASCADE,
    officer_user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    decision loan_decision_type NOT NULL,
    notes TEXT NOT NULL,
    decided_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_loan_application_decisions_application_id ON loan_application_decisions(application_id);
CREATE INDEX IF NOT EXISTS idx_loan_application_decisions_officer_user_id ON loan_application_decisions(officer_user_id);
CREATE INDEX IF NOT EXISTS idx_loan_application_decisions_decision ON loan_application_decisions(decision);
CREATE INDEX IF NOT EXISTS idx_loan_application_decisions_decided_at ON loan_application_decisions(decided_at DESC);

COMMENT ON TABLE loan_application_decisions IS 'Decision history for loan applications';
COMMENT ON COLUMN loan_application_decisions.officer_user_id IS 'Loan Officer who made the decision';

-- ============================================================================
-- 10. Loan Application Audit Logs Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS loan_application_audits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES loan_applications(id) ON DELETE CASCADE,
    actor_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    from_status VARCHAR(50),
    to_status VARCHAR(50),
    payload_json JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_loan_application_audits_application_id ON loan_application_audits(application_id);
CREATE INDEX IF NOT EXISTS idx_loan_application_audits_action ON loan_application_audits(action);
CREATE INDEX IF NOT EXISTS idx_loan_application_audits_created_at ON loan_application_audits(created_at DESC);

COMMENT ON TABLE loan_application_audits IS 'Immutable audit trail for loan applications';
COMMENT ON COLUMN loan_application_audits.action IS 'Action performed (CREATED, SUBMITTED, APPROVED, etc.)';
COMMENT ON COLUMN loan_application_audits.payload_json IS 'Additional context for the action';

-- ============================================================================
-- 11. Updated At Triggers
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_branches_updated_at
    BEFORE UPDATE ON branches
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_loan_applications_updated_at
    BEFORE UPDATE ON loan_applications
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_loan_application_customers_updated_at
    BEFORE UPDATE ON loan_application_customers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_loan_application_vehicles_updated_at
    BEFORE UPDATE ON loan_application_vehicles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 12. Sample Data (Optional - for testing)
-- ============================================================================

-- Insert sample branches
INSERT INTO branches (code, name, region, is_active)
VALUES
    ('BR001', 'Colombo Main Branch', 'Western', TRUE),
    ('BR002', 'Kandy Branch', 'Central', TRUE),
    ('BR003', 'Galle Branch', 'Southern', TRUE)
ON CONFLICT (code) DO NOTHING;

-- ============================================================================
-- Migration Complete
-- ============================================================================

COMMENT ON SCHEMA public IS 'Loan Approval System migration 0010 completed';
