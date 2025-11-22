-- ============================================================================
-- Migration: Enhanced Leave Management System with Multi-Level Approval
-- Version: 0011
-- Description: Adds multi-level approval workflow, audit trails, and policies
-- ============================================================================

-- ============================================================================
-- 1. Enums
-- ============================================================================

-- Create leave status enum (extend existing)
DO $$ BEGIN
    CREATE TYPE leave_status_enum AS ENUM (
        'DRAFT',
        'PENDING',
        'APPROVED_BRANCH',
        'APPROVED_HO',
        'APPROVED',
        'REJECTED',
        'CANCELLED',
        'NEEDS_INFO'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create approval decision enum
DO $$ BEGIN
    CREATE TYPE approval_decision_enum AS ENUM (
        'APPROVED',
        'REJECTED',
        'NEEDS_INFO'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create approver role enum
DO $$ BEGIN
    CREATE TYPE approver_role_enum AS ENUM (
        'BRANCH_MANAGER',
        'HEAD_MANAGER',
        'ADMIN'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;


-- ============================================================================
-- 2. Alter Existing Tables
-- ============================================================================

-- Enhance leave_types table
ALTER TABLE leave_types
    ADD COLUMN IF NOT EXISTS requires_ho_approval BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS max_days_per_request INTEGER,
    ADD COLUMN IF NOT EXISTS code VARCHAR(20) UNIQUE;

COMMENT ON COLUMN leave_types.requires_ho_approval IS 'Whether this leave type requires Head Office approval';
COMMENT ON COLUMN leave_types.max_days_per_request IS 'Maximum days that can be requested at once';
COMMENT ON COLUMN leave_types.code IS 'Short code for leave type (e.g., ANNUAL, CASUAL, SICK)';

-- Update existing leave types with codes
UPDATE leave_types SET code = 'ANNUAL' WHERE LOWER(name) LIKE '%annual%' AND code IS NULL;
UPDATE leave_types SET code = 'CASUAL' WHERE LOWER(name) LIKE '%casual%' AND code IS NULL;
UPDATE leave_types SET code = 'SICK' WHERE LOWER(name) LIKE '%sick%' AND code IS NULL;
UPDATE leave_types SET code = 'MEDICAL' WHERE LOWER(name) LIKE '%medical%' AND code IS NULL;


-- Enhance leave_applications table
ALTER TABLE leave_applications
    ADD COLUMN IF NOT EXISTS branch_id UUID,
    ADD COLUMN IF NOT EXISTS branch_approver_id UUID,
    ADD COLUMN IF NOT EXISTS branch_approved_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS ho_approver_id UUID,
    ADD COLUMN IF NOT EXISTS ho_approved_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS cancelled_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS is_half_day BOOLEAN NOT NULL DEFAULT FALSE;

COMMENT ON COLUMN leave_applications.branch_id IS 'Employee branch (for routing)';
COMMENT ON COLUMN leave_applications.branch_approver_id IS 'Branch manager who approved';
COMMENT ON COLUMN leave_applications.branch_approved_at IS 'Branch approval timestamp';
COMMENT ON COLUMN leave_applications.ho_approver_id IS 'Head Office manager who approved';
COMMENT ON COLUMN leave_applications.ho_approved_at IS 'Head Office approval timestamp';
COMMENT ON COLUMN leave_applications.cancelled_at IS 'Cancellation timestamp';
COMMENT ON COLUMN leave_applications.is_half_day IS 'Whether this is a half-day leave';

-- Update status column type if needed (may fail if already correct type, that's ok)
DO $$
BEGIN
    ALTER TABLE leave_applications
        ALTER COLUMN status TYPE VARCHAR(20);
EXCEPTION
    WHEN others THEN null;
END $$;


-- ============================================================================
-- 3. Create New Tables
-- ============================================================================

-- Leave Approvals Table
CREATE TABLE IF NOT EXISTS leave_approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    leave_request_id VARCHAR(50) NOT NULL,
    approver_id UUID NOT NULL,
    approver_role approver_role_enum NOT NULL,
    decision approval_decision_enum NOT NULL,
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_leave_approvals_leave FOREIGN KEY (leave_request_id)
        REFERENCES leave_applications(id) ON DELETE CASCADE,
    CONSTRAINT fk_leave_approvals_approver FOREIGN KEY (approver_id)
        REFERENCES users(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_leave_approvals_leave_id ON leave_approvals(leave_request_id);
CREATE INDEX IF NOT EXISTS idx_leave_approvals_approver ON leave_approvals(approver_id);
CREATE INDEX IF NOT EXISTS idx_leave_approvals_decision ON leave_approvals(decision);
CREATE INDEX IF NOT EXISTS idx_leave_approvals_created ON leave_approvals(created_at DESC);

COMMENT ON TABLE leave_approvals IS 'Tracks individual approval decisions in the workflow';
COMMENT ON COLUMN leave_approvals.approver_role IS 'Role of the approver (Branch Manager, Head Manager, Admin)';
COMMENT ON COLUMN leave_approvals.decision IS 'Approval decision (APPROVED, REJECTED, NEEDS_INFO)';


-- Leave Audit Logs Table
CREATE TABLE IF NOT EXISTS leave_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    leave_request_id VARCHAR(50) NOT NULL,
    actor_id UUID NOT NULL,
    action VARCHAR(50) NOT NULL,
    old_status VARCHAR(20),
    new_status VARCHAR(20),
    payload_json JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_leave_audit_leave FOREIGN KEY (leave_request_id)
        REFERENCES leave_applications(id) ON DELETE CASCADE,
    CONSTRAINT fk_leave_audit_actor FOREIGN KEY (actor_id)
        REFERENCES users(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_leave_audit_leave_id ON leave_audit_logs(leave_request_id);
CREATE INDEX IF NOT EXISTS idx_leave_audit_actor ON leave_audit_logs(actor_id);
CREATE INDEX IF NOT EXISTS idx_leave_audit_created ON leave_audit_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_leave_audit_action ON leave_audit_logs(action);

COMMENT ON TABLE leave_audit_logs IS 'Immutable audit trail of all leave application state changes';
COMMENT ON COLUMN leave_audit_logs.action IS 'Action performed (SUBMITTED, APPROVED_BRANCH, APPROVED_HO, REJECTED, etc.)';
COMMENT ON COLUMN leave_audit_logs.payload_json IS 'Additional data (notes, metadata)';


-- Leave Policies Table
CREATE TABLE IF NOT EXISTS leave_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    leave_type_id VARCHAR(50) NOT NULL,
    branch_id UUID,  -- NULL = global policy
    requires_branch_approval BOOLEAN NOT NULL DEFAULT TRUE,
    requires_ho_approval BOOLEAN NOT NULL DEFAULT FALSE,
    auto_approve_days_threshold INTEGER,
    branch_approval_sla_hours INTEGER,
    ho_approval_sla_hours INTEGER,
    min_notice_days INTEGER NOT NULL DEFAULT 1,
    max_days_per_request INTEGER,
    allow_half_day BOOLEAN NOT NULL DEFAULT TRUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_leave_policies_leave_type FOREIGN KEY (leave_type_id)
        REFERENCES leave_types(id) ON DELETE CASCADE,
    CONSTRAINT fk_leave_policies_branch FOREIGN KEY (branch_id)
        REFERENCES branches(id) ON DELETE CASCADE,
    CONSTRAINT chk_auto_approve_threshold CHECK (auto_approve_days_threshold IS NULL OR auto_approve_days_threshold >= 0),
    CONSTRAINT chk_branch_sla CHECK (branch_approval_sla_hours IS NULL OR branch_approval_sla_hours > 0),
    CONSTRAINT chk_ho_sla CHECK (ho_approval_sla_hours IS NULL OR ho_approval_sla_hours > 0),
    CONSTRAINT chk_min_notice CHECK (min_notice_days >= 0),
    CONSTRAINT chk_max_days CHECK (max_days_per_request IS NULL OR max_days_per_request > 0),
    -- Only one active policy per leave_type + branch combination
    CONSTRAINT uk_leave_policies_type_branch UNIQUE (leave_type_id, branch_id, is_active)
);

CREATE INDEX IF NOT EXISTS idx_leave_policies_leave_type ON leave_policies(leave_type_id);
CREATE INDEX IF NOT EXISTS idx_leave_policies_branch ON leave_policies(branch_id);
CREATE INDEX IF NOT EXISTS idx_leave_policies_active ON leave_policies(is_active) WHERE is_active = TRUE;

COMMENT ON TABLE leave_policies IS 'Configurable approval policies per leave type and branch';
COMMENT ON COLUMN leave_policies.branch_id IS 'NULL = global policy, otherwise branch-specific';
COMMENT ON COLUMN leave_policies.auto_approve_days_threshold IS 'Auto-approve if days <= threshold';
COMMENT ON COLUMN leave_policies.branch_approval_sla_hours IS 'SLA for branch manager approval (hours)';
COMMENT ON COLUMN leave_policies.ho_approval_sla_hours IS 'SLA for Head Office approval (hours)';
COMMENT ON COLUMN leave_policies.min_notice_days IS 'Minimum days notice required before leave starts';


-- ============================================================================
-- 4. Add Foreign Keys and Indexes
-- ============================================================================

-- Add foreign keys for new columns in leave_applications (if not exists)
DO $$
BEGIN
    -- Branch FK
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_leave_applications_branch'
    ) THEN
        ALTER TABLE leave_applications
            ADD CONSTRAINT fk_leave_applications_branch
            FOREIGN KEY (branch_id) REFERENCES branches(id) ON DELETE SET NULL;
    END IF;

    -- Branch approver FK
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_leave_applications_branch_approver'
    ) THEN
        ALTER TABLE leave_applications
            ADD CONSTRAINT fk_leave_applications_branch_approver
            FOREIGN KEY (branch_approver_id) REFERENCES users(id) ON DELETE SET NULL;
    END IF;

    -- HO approver FK
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_leave_applications_ho_approver'
    ) THEN
        ALTER TABLE leave_applications
            ADD CONSTRAINT fk_leave_applications_ho_approver
            FOREIGN KEY (ho_approver_id) REFERENCES users(id) ON DELETE SET NULL;
    END IF;
END $$;

-- Add indexes for new columns
CREATE INDEX IF NOT EXISTS idx_leave_applications_branch ON leave_applications(branch_id);
CREATE INDEX IF NOT EXISTS idx_leave_applications_branch_approver ON leave_applications(branch_approver_id);
CREATE INDEX IF NOT EXISTS idx_leave_applications_ho_approver ON leave_applications(ho_approver_id);
CREATE INDEX IF NOT EXISTS idx_leave_applications_status_created ON leave_applications(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_leave_applications_branch_status ON leave_applications(branch_id, status) WHERE branch_id IS NOT NULL;


-- ============================================================================
-- 5. Seed Default Data
-- ============================================================================

-- Seed global leave policies (only if no policies exist)
DO $$
DECLARE
    v_annual_leave_id VARCHAR(50);
    v_casual_leave_id VARCHAR(50);
    v_sick_leave_id VARCHAR(50);
BEGIN
    -- Get leave type IDs
    SELECT id INTO v_annual_leave_id FROM leave_types WHERE code = 'ANNUAL' LIMIT 1;
    SELECT id INTO v_casual_leave_id FROM leave_types WHERE code = 'CASUAL' LIMIT 1;
    SELECT id INTO v_sick_leave_id FROM leave_types WHERE code = 'SICK' LIMIT 1;

    -- Annual Leave Policy (requires HO approval for > 5 days)
    IF v_annual_leave_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM leave_policies WHERE leave_type_id = v_annual_leave_id AND branch_id IS NULL
    ) THEN
        INSERT INTO leave_policies (
            leave_type_id, branch_id, requires_branch_approval, requires_ho_approval,
            auto_approve_days_threshold, branch_approval_sla_hours, ho_approval_sla_hours,
            min_notice_days, max_days_per_request, allow_half_day, is_active
        ) VALUES (
            v_annual_leave_id, NULL, TRUE, FALSE,
            5, 24, 48,  -- Auto-approve <= 5 days, 24h branch SLA, 48h HO SLA
            7, 30, TRUE, TRUE  -- 7 days notice, max 30 days per request, allow half-day
        );
    END IF;

    -- Casual Leave Policy (branch approval only, quick approval)
    IF v_casual_leave_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM leave_policies WHERE leave_type_id = v_casual_leave_id AND branch_id IS NULL
    ) THEN
        INSERT INTO leave_policies (
            leave_type_id, branch_id, requires_branch_approval, requires_ho_approval,
            auto_approve_days_threshold, branch_approval_sla_hours, ho_approval_sla_hours,
            min_notice_days, max_days_per_request, allow_half_day, is_active
        ) VALUES (
            v_casual_leave_id, NULL, TRUE, FALSE,
            2, 12, NULL,  -- Auto-approve <= 2 days, 12h branch SLA
            1, 5, TRUE, TRUE  -- 1 day notice, max 5 days per request
        );
    END IF;

    -- Sick Leave Policy (may require documentation, quick approval)
    IF v_sick_leave_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM leave_policies WHERE leave_type_id = v_sick_leave_id AND branch_id IS NULL
    ) THEN
        INSERT INTO leave_policies (
            leave_type_id, branch_id, requires_branch_approval, requires_ho_approval,
            auto_approve_days_threshold, branch_approval_sla_hours, ho_approval_sla_hours,
            min_notice_days, max_days_per_request, allow_half_day, is_active
        ) VALUES (
            v_sick_leave_id, NULL, TRUE, FALSE,
            NULL, 8, NULL,  -- No auto-approve, 8h branch SLA
            0, 14, TRUE, TRUE  -- No notice required (emergency), max 14 days per request
        );
    END IF;
END $$;


-- ============================================================================
-- 6. Update Triggers
-- ============================================================================

-- Trigger to update updated_at on leave_policies
CREATE OR REPLACE FUNCTION update_leave_policies_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_leave_policies_updated_at ON leave_policies;
CREATE TRIGGER trg_leave_policies_updated_at
    BEFORE UPDATE ON leave_policies
    FOR EACH ROW
    EXECUTE FUNCTION update_leave_policies_updated_at();


-- ============================================================================
-- 7. Grants (ensure proper permissions)
-- ============================================================================

-- Grant permissions on new tables
GRANT SELECT, INSERT, UPDATE ON leave_approvals TO PUBLIC;
GRANT SELECT, INSERT ON leave_audit_logs TO PUBLIC;  -- Audit logs are append-only
GRANT SELECT, INSERT, UPDATE ON leave_policies TO PUBLIC;

-- Grant sequence permissions
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO PUBLIC;


-- ============================================================================
-- 8. Migration Metadata
-- ============================================================================

-- Insert migration record (if you have a migrations tracking table)
-- INSERT INTO schema_migrations (version, description, applied_at)
-- VALUES ('0011', 'Enhanced Leave Management System with Multi-Level Approval', NOW())
-- ON CONFLICT (version) DO NOTHING;


-- ============================================================================
-- END OF MIGRATION
-- ============================================================================

-- Verify migration
DO $$
DECLARE
    v_count INTEGER;
BEGIN
    -- Check that new tables exist
    SELECT COUNT(*) INTO v_count FROM information_schema.tables
    WHERE table_schema = 'public' AND table_name IN ('leave_approvals', 'leave_audit_logs', 'leave_policies');

    IF v_count = 3 THEN
        RAISE NOTICE 'Migration 0011 completed successfully. All tables created.';
    ELSE
        RAISE WARNING 'Migration 0011 incomplete. Expected 3 new tables, found %', v_count;
    END IF;

    -- Check that enhanced columns exist in leave_applications
    SELECT COUNT(*) INTO v_count FROM information_schema.columns
    WHERE table_name = 'leave_applications' AND column_name IN ('branch_id', 'branch_approver_id', 'ho_approver_id', 'is_half_day');

    IF v_count = 4 THEN
        RAISE NOTICE 'Migration 0011: leave_applications enhanced successfully';
    ELSE
        RAISE WARNING 'Migration 0011: leave_applications enhancement incomplete. Expected 4 new columns, found %', v_count;
    END IF;
END $$;
