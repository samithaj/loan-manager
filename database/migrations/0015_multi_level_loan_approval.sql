-- ============================================================================
-- Migration: Multi-Level Loan Approval System
-- Version: 0015
-- Description: Adds approval level hierarchy with threshold-based routing
--              for loan applications
-- ============================================================================

-- ============================================================================
-- 1. CREATE LOAN APPROVAL THRESHOLDS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS loan_approval_thresholds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id TEXT NOT NULL REFERENCES companies(id),

    -- Threshold range
    min_amount DECIMAL(15,2) NOT NULL,
    max_amount DECIMAL(15,2), -- NULL means unlimited

    -- Approval level configuration
    approval_level INTEGER NOT NULL CHECK (approval_level >= 0),
    approver_role TEXT NOT NULL, -- e.g., 'LOAN_MANAGER', 'CREDIT_OFFICER_L1', 'CREDIT_OFFICER_L2'
    approver_permission TEXT NOT NULL, -- e.g., 'loans:approve:level1', 'loans:approve:level2'

    -- Sequential enforcement
    requires_previous_levels BOOLEAN DEFAULT TRUE,

    -- Metadata
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by TEXT,

    -- Ensure no overlapping thresholds for same company and level
    CONSTRAINT valid_threshold_range CHECK (
        min_amount >= 0 AND
        (max_amount IS NULL OR max_amount > min_amount)
    )
);

-- Indexes for threshold lookups
CREATE INDEX idx_thresholds_company_active
    ON loan_approval_thresholds(company_id, is_active);

CREATE INDEX idx_thresholds_amount_range
    ON loan_approval_thresholds(company_id, approval_level, min_amount, max_amount)
    WHERE is_active = TRUE;

-- Comments
COMMENT ON TABLE loan_approval_thresholds IS
    'Defines loan amount thresholds and required approval levels';
COMMENT ON COLUMN loan_approval_thresholds.approval_level IS
    'Approval hierarchy level (0=initial review, 1=first approval, 2=second approval, etc.)';
COMMENT ON COLUMN loan_approval_thresholds.requires_previous_levels IS
    'If true, all lower approval levels must be completed first';

-- ============================================================================
-- 2. ENHANCE LOAN APPLICATION DECISIONS TABLE
-- ============================================================================

-- Add approval level tracking
ALTER TABLE loan_application_decisions
    ADD COLUMN IF NOT EXISTS approval_level INTEGER,
    ADD COLUMN IF NOT EXISTS is_auto_routed BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS threshold_id UUID REFERENCES loan_approval_thresholds(id);

-- Add index for approval level queries
CREATE INDEX IF NOT EXISTS idx_decisions_approval_level
    ON loan_application_decisions(application_id, approval_level, decision);

-- Comments
COMMENT ON COLUMN loan_application_decisions.approval_level IS
    'The approval level this decision belongs to (matches threshold)';
COMMENT ON COLUMN loan_application_decisions.is_auto_routed IS
    'True if this decision was created by automatic threshold routing';
COMMENT ON COLUMN loan_application_decisions.threshold_id IS
    'Reference to the threshold rule that triggered this approval level';

-- ============================================================================
-- 3. ENHANCE LOAN APPLICATIONS TABLE
-- ============================================================================

-- Add current approval level tracking
ALTER TABLE loan_applications
    ADD COLUMN IF NOT EXISTS current_approval_level INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS required_approval_level INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS approval_progress JSONB DEFAULT '[]'::jsonb;

-- Add index for approval tracking
CREATE INDEX IF NOT EXISTS idx_applications_approval_level
    ON loan_applications(status, current_approval_level, required_approval_level);

-- Comments
COMMENT ON COLUMN loan_applications.current_approval_level IS
    'Current approval level in the workflow (0=initial review, 1+=credit officer levels)';
COMMENT ON COLUMN loan_applications.required_approval_level IS
    'Highest approval level required based on loan amount (determined by thresholds)';
COMMENT ON COLUMN loan_applications.approval_progress IS
    'JSON array tracking approval progress: [{level: 0, status: "APPROVED", by: "user_id", at: "timestamp"}]';

-- ============================================================================
-- 4. CREATE DEFAULT THRESHOLD CONFIGURATION
-- ============================================================================

-- Insert sample thresholds (adjust amounts based on your business rules)
-- These are examples - adjust for production

-- Level 0: Loan Manager - Initial Review (all applications)
INSERT INTO loan_approval_thresholds
    (company_id, min_amount, max_amount, approval_level, approver_role, approver_permission, description, created_by)
SELECT DISTINCT
    id,
    0,
    NULL, -- Covers all amounts
    0,
    'LOAN_MANAGER',
    'loans:review',
    'Initial review by Loan Manager - applies to all loan applications',
    'system'
FROM companies
ON CONFLICT DO NOTHING;

-- Level 1: Credit Officer L1 - For amounts > 100,000
INSERT INTO loan_approval_thresholds
    (company_id, min_amount, max_amount, approval_level, approver_role, approver_permission, description, requires_previous_levels, created_by)
SELECT DISTINCT
    id,
    100000,
    500000,
    1,
    'CREDIT_OFFICER_L1',
    'loans:approve:level1',
    'Credit Officer Level 1 approval required for loans 100K-500K',
    TRUE,
    'system'
FROM companies
ON CONFLICT DO NOTHING;

-- Level 2: Credit Officer L2 - For amounts > 500,000
INSERT INTO loan_approval_thresholds
    (company_id, min_amount, max_amount, approval_level, approver_role, approver_permission, description, requires_previous_levels, created_by)
SELECT DISTINCT
    id,
    500000,
    1000000,
    2,
    'CREDIT_OFFICER_L2',
    'loans:approve:level2',
    'Credit Officer Level 2 approval required for loans 500K-1M',
    TRUE,
    'system'
FROM companies
ON CONFLICT DO NOTHING;

-- Level 3: Senior Management - For amounts > 1,000,000
INSERT INTO loan_approval_thresholds
    (company_id, min_amount, max_amount, approval_level, approver_role, approver_permission, description, requires_previous_levels, created_by)
SELECT DISTINCT
    id,
    1000000,
    NULL, -- No upper limit
    3,
    'SENIOR_MANAGEMENT',
    'loans:approve:level3',
    'Senior Management approval required for loans over 1M',
    TRUE,
    'system'
FROM companies
ON CONFLICT DO NOTHING;

-- ============================================================================
-- 5. CREATE HELPER VIEWS
-- ============================================================================

-- View: Approval Progress Summary
CREATE OR REPLACE VIEW loan_approval_progress_view AS
SELECT
    la.id AS application_id,
    la.application_no,
    la.requested_amount,
    la.status,
    la.current_approval_level,
    la.required_approval_level,
    la.branch_id,

    -- Approval progress
    CASE
        WHEN la.required_approval_level = 0 THEN 'NO_APPROVAL_NEEDED'
        WHEN la.current_approval_level >= la.required_approval_level THEN 'FULLY_APPROVED'
        WHEN la.current_approval_level > 0 THEN 'PARTIALLY_APPROVED'
        ELSE 'PENDING'
    END AS approval_status,

    -- Next required approver
    (
        SELECT lat.approver_role
        FROM loan_approval_thresholds lat
        WHERE lat.company_id = (SELECT company_id FROM branches WHERE id = la.branch_id)
            AND lat.approval_level = la.current_approval_level + 1
            AND lat.is_active = TRUE
            AND la.requested_amount >= lat.min_amount
            AND (lat.max_amount IS NULL OR la.requested_amount < lat.max_amount)
        LIMIT 1
    ) AS next_approver_role,

    -- Count of decisions at each level
    (
        SELECT COUNT(*)
        FROM loan_application_decisions
        WHERE application_id = la.id
            AND decision = 'APPROVED'
    ) AS approvals_count,

    (
        SELECT COUNT(*)
        FROM loan_application_decisions
        WHERE application_id = la.id
            AND decision = 'REJECTED'
    ) AS rejections_count,

    la.created_at,
    la.submitted_at,
    la.decided_at

FROM loan_applications la;

COMMENT ON VIEW loan_approval_progress_view IS
    'Summary view showing approval progress and next required approver for each application';

-- ============================================================================
-- 6. CREATE FUNCTION: Determine Required Approval Level
-- ============================================================================

CREATE OR REPLACE FUNCTION determine_required_approval_level(
    p_company_id TEXT,
    p_loan_amount DECIMAL
)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_max_level INTEGER;
BEGIN
    -- Get the highest approval level required based on thresholds
    SELECT COALESCE(MAX(approval_level), 0)
    INTO v_max_level
    FROM loan_approval_thresholds
    WHERE company_id = p_company_id
        AND is_active = TRUE
        AND p_loan_amount >= min_amount
        AND (max_amount IS NULL OR p_loan_amount < max_amount);

    RETURN v_max_level;
END;
$$;

COMMENT ON FUNCTION determine_required_approval_level IS
    'Determines the highest approval level required for a given loan amount';

-- ============================================================================
-- 7. CREATE FUNCTION: Get Next Approval Threshold
-- ============================================================================

CREATE OR REPLACE FUNCTION get_next_approval_threshold(
    p_company_id TEXT,
    p_loan_amount DECIMAL,
    p_current_level INTEGER
)
RETURNS TABLE(
    threshold_id UUID,
    approval_level INTEGER,
    approver_role TEXT,
    approver_permission TEXT,
    min_amount DECIMAL,
    max_amount DECIMAL
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        lat.id,
        lat.approval_level,
        lat.approver_role,
        lat.approver_permission,
        lat.min_amount,
        lat.max_amount
    FROM loan_approval_thresholds lat
    WHERE lat.company_id = p_company_id
        AND lat.is_active = TRUE
        AND lat.approval_level = p_current_level + 1
        AND p_loan_amount >= lat.min_amount
        AND (lat.max_amount IS NULL OR p_loan_amount < lat.max_amount)
    ORDER BY lat.approval_level
    LIMIT 1;
END;
$$;

COMMENT ON FUNCTION get_next_approval_threshold IS
    'Returns the next approval threshold for a loan application';

-- ============================================================================
-- 8. CREATE TRIGGER: Auto-set Required Approval Level
-- ============================================================================

CREATE OR REPLACE FUNCTION trigger_set_required_approval_level()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_company_id TEXT;
    v_required_level INTEGER;
BEGIN
    -- Get company_id from branch
    SELECT company_id INTO v_company_id
    FROM branches
    WHERE id = NEW.branch_id;

    -- Determine required approval level
    v_required_level := determine_required_approval_level(v_company_id, NEW.requested_amount);

    -- Set on the application
    NEW.required_approval_level := v_required_level;

    RETURN NEW;
END;
$$;

-- Create trigger on INSERT and UPDATE
DROP TRIGGER IF EXISTS trg_set_required_approval_level ON loan_applications;
CREATE TRIGGER trg_set_required_approval_level
    BEFORE INSERT OR UPDATE OF requested_amount
    ON loan_applications
    FOR EACH ROW
    EXECUTE FUNCTION trigger_set_required_approval_level();

COMMENT ON FUNCTION trigger_set_required_approval_level IS
    'Automatically sets required_approval_level when loan application is created or amount is updated';

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
