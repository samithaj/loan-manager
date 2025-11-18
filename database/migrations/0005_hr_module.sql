-- Migration: HR Module - Leave Management, Attendance, and Performance Bonuses
-- Version: 0005_hr_module.sql
-- Description: Adds comprehensive HR functionality including leave management,
--              attendance tracking, and performance-based bonus payments

-- ============================================================================
-- 1. LEAVE MANAGEMENT
-- ============================================================================

-- Leave Types (Annual, Sick, Unpaid, etc.)
CREATE TABLE IF NOT EXISTS leave_types (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    default_days_per_year INTEGER NOT NULL DEFAULT 0,
    requires_approval BOOLEAN NOT NULL DEFAULT TRUE,
    requires_documentation BOOLEAN NOT NULL DEFAULT FALSE,
    max_consecutive_days INTEGER,
    is_paid BOOLEAN NOT NULL DEFAULT TRUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Leave Balances (per employee, per year)
CREATE TABLE IF NOT EXISTS leave_balances (
    id TEXT PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    leave_type_id TEXT NOT NULL REFERENCES leave_types(id),
    year INTEGER NOT NULL,
    entitled_days NUMERIC(5,2) NOT NULL DEFAULT 0,
    used_days NUMERIC(5,2) NOT NULL DEFAULT 0,
    pending_days NUMERIC(5,2) NOT NULL DEFAULT 0,
    remaining_days NUMERIC(5,2) GENERATED ALWAYS AS (entitled_days - used_days - pending_days) STORED,
    carried_forward_days NUMERIC(5,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, leave_type_id, year)
);

-- Leave Applications
CREATE TABLE IF NOT EXISTS leave_applications (
    id TEXT PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    leave_type_id TEXT NOT NULL REFERENCES leave_types(id),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    total_days NUMERIC(5,2) NOT NULL,
    reason TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED', 'CANCELLED')),
    approver_id UUID REFERENCES users(id),
    approved_at TIMESTAMPTZ,
    approver_notes TEXT,
    document_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- 2. ATTENDANCE TRACKING
-- ============================================================================

-- Attendance Records (daily attendance with clock in/out)
CREATE TABLE IF NOT EXISTS attendance_records (
    id TEXT PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    clock_in TIMESTAMPTZ,
    clock_out TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'ABSENT' CHECK (status IN ('PRESENT', 'ABSENT', 'LATE', 'HALF_DAY', 'ON_LEAVE', 'HOLIDAY', 'WEEKEND')),
    work_hours NUMERIC(5,2),
    overtime_hours NUMERIC(5,2) DEFAULT 0,
    notes TEXT,
    location TEXT,
    ip_address TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, date)
);

-- Work Schedules (defines expected work hours)
CREATE TABLE IF NOT EXISTS work_schedules (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    monday_start TIME,
    monday_end TIME,
    tuesday_start TIME,
    tuesday_end TIME,
    wednesday_start TIME,
    wednesday_end TIME,
    thursday_start TIME,
    thursday_end TIME,
    friday_start TIME,
    friday_end TIME,
    saturday_start TIME,
    saturday_end TIME,
    sunday_start TIME,
    sunday_end TIME,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- User Work Schedule Assignment
CREATE TABLE IF NOT EXISTS user_work_schedules (
    id TEXT PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    schedule_id TEXT NOT NULL REFERENCES work_schedules(id),
    effective_from DATE NOT NULL,
    effective_to DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, effective_from)
);

-- ============================================================================
-- 3. PERFORMANCE & BONUS MANAGEMENT
-- ============================================================================

-- Sales Targets (monthly/quarterly targets for staff)
CREATE TABLE IF NOT EXISTS sales_targets (
    id TEXT PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    target_type TEXT NOT NULL CHECK (target_type IN ('MONTHLY', 'QUARTERLY', 'YEARLY')),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    target_loans INTEGER NOT NULL DEFAULT 0,
    target_loan_amount NUMERIC(15,2) NOT NULL DEFAULT 0,
    target_bicycles INTEGER NOT NULL DEFAULT 0,
    target_bicycle_revenue NUMERIC(15,2) NOT NULL DEFAULT 0,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, period_start, period_end)
);

-- Performance Metrics (actual vs target)
CREATE TABLE IF NOT EXISTS performance_metrics (
    id TEXT PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    actual_loans INTEGER NOT NULL DEFAULT 0,
    actual_loan_amount NUMERIC(15,2) NOT NULL DEFAULT 0,
    actual_bicycles INTEGER NOT NULL DEFAULT 0,
    actual_bicycle_revenue NUMERIC(15,2) NOT NULL DEFAULT 0,
    achievement_percentage NUMERIC(5,2) NOT NULL DEFAULT 0,
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, period_start, period_end)
);

-- Bonus Rules (defines how bonuses are calculated)
CREATE TABLE IF NOT EXISTS bonus_rules (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    rule_type TEXT NOT NULL CHECK (rule_type IN ('FIXED', 'PERCENTAGE', 'TIERED', 'COMMISSION')),
    applies_to_roles TEXT[] NOT NULL,
    min_achievement_percentage NUMERIC(5,2) NOT NULL DEFAULT 0,
    base_amount NUMERIC(12,2),
    percentage_rate NUMERIC(5,2),
    commission_rate NUMERIC(5,2),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    effective_from DATE NOT NULL,
    effective_to DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Bonus Tiers (for tiered bonus structures)
CREATE TABLE IF NOT EXISTS bonus_tiers (
    id TEXT PRIMARY KEY,
    bonus_rule_id TEXT NOT NULL REFERENCES bonus_rules(id) ON DELETE CASCADE,
    tier_order INTEGER NOT NULL,
    achievement_from NUMERIC(5,2) NOT NULL,
    achievement_to NUMERIC(5,2) NOT NULL,
    bonus_amount NUMERIC(12,2),
    bonus_percentage NUMERIC(5,2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Bonus Payments (actual bonus payment records)
CREATE TABLE IF NOT EXISTS bonus_payments (
    id TEXT PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    bonus_rule_id TEXT REFERENCES bonus_rules(id),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    target_amount NUMERIC(15,2),
    actual_amount NUMERIC(15,2),
    achievement_percentage NUMERIC(5,2),
    bonus_amount NUMERIC(12,2) NOT NULL,
    calculation_details JSONB,
    status TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'APPROVED', 'PAID', 'REJECTED')),
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMPTZ,
    paid_at TIMESTAMPTZ,
    payment_reference TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- 4. INDEXES FOR PERFORMANCE
-- ============================================================================

-- Leave Management Indexes
CREATE INDEX IF NOT EXISTS idx_leave_balances_user_year ON leave_balances(user_id, year);
CREATE INDEX IF NOT EXISTS idx_leave_applications_user ON leave_applications(user_id);
CREATE INDEX IF NOT EXISTS idx_leave_applications_status ON leave_applications(status);
CREATE INDEX IF NOT EXISTS idx_leave_applications_dates ON leave_applications(start_date, end_date);

-- Attendance Indexes
CREATE INDEX IF NOT EXISTS idx_attendance_user_date ON attendance_records(user_id, date);
CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance_records(date);
CREATE INDEX IF NOT EXISTS idx_attendance_status ON attendance_records(status);

-- Performance & Bonus Indexes
CREATE INDEX IF NOT EXISTS idx_sales_targets_user ON sales_targets(user_id);
CREATE INDEX IF NOT EXISTS idx_sales_targets_period ON sales_targets(period_start, period_end);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_user ON performance_metrics(user_id);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_period ON performance_metrics(period_start, period_end);
CREATE INDEX IF NOT EXISTS idx_bonus_payments_user ON bonus_payments(user_id);
CREATE INDEX IF NOT EXISTS idx_bonus_payments_status ON bonus_payments(status);
CREATE INDEX IF NOT EXISTS idx_bonus_payments_period ON bonus_payments(period_start, period_end);

-- ============================================================================
-- 5. SEED DATA - LEAVE TYPES
-- ============================================================================

INSERT INTO leave_types (id, name, description, default_days_per_year, requires_approval, requires_documentation, is_paid) VALUES
    ('ANNUAL', 'Annual Leave', 'Paid annual vacation leave', 20, TRUE, FALSE, TRUE),
    ('SICK', 'Sick Leave', 'Paid sick leave', 12, TRUE, TRUE, TRUE),
    ('UNPAID', 'Unpaid Leave', 'Leave without pay', 0, TRUE, FALSE, FALSE),
    ('EMERGENCY', 'Emergency Leave', 'Emergency personal leave', 3, TRUE, FALSE, TRUE),
    ('MATERNITY', 'Maternity Leave', 'Maternity leave for mothers', 90, TRUE, TRUE, TRUE),
    ('PATERNITY', 'Paternity Leave', 'Paternity leave for fathers', 7, TRUE, TRUE, TRUE),
    ('STUDY', 'Study Leave', 'Leave for educational purposes', 0, TRUE, TRUE, FALSE),
    ('BEREAVEMENT', 'Bereavement Leave', 'Leave for family bereavement', 5, TRUE, FALSE, TRUE)
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- 6. SEED DATA - DEFAULT WORK SCHEDULE
-- ============================================================================

INSERT INTO work_schedules (id, name, description, is_default,
    monday_start, monday_end, tuesday_start, tuesday_end, wednesday_start, wednesday_end,
    thursday_start, thursday_end, friday_start, friday_end, saturday_start, saturday_end) VALUES
    ('STANDARD', 'Standard Office Hours', '9 AM to 5 PM, Monday to Saturday', TRUE,
    '09:00', '17:00', '09:00', '17:00', '09:00', '17:00',
    '09:00', '17:00', '09:00', '17:00', '09:00', '13:00')
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- 7. SEED DATA - BONUS RULES
-- ============================================================================

-- Sales Agent Commission (5% of bicycle sales revenue)
INSERT INTO bonus_rules (id, name, description, rule_type, applies_to_roles, commission_rate, is_active, effective_from) VALUES
    ('BICYCLE_COMMISSION', 'Bicycle Sales Commission', 'Commission on bicycle hire purchase sales', 'COMMISSION',
    ARRAY['sales_agent', 'branch_manager'], 5.0, TRUE, '2025-01-01')
ON CONFLICT (id) DO NOTHING;

-- Branch Manager Performance Bonus (tiered based on achievement)
INSERT INTO bonus_rules (id, name, description, rule_type, applies_to_roles, min_achievement_percentage, is_active, effective_from) VALUES
    ('BRANCH_MANAGER_TIER', 'Branch Manager Performance Bonus', 'Tiered bonus based on target achievement', 'TIERED',
    ARRAY['branch_manager'], 80.0, TRUE, '2025-01-01')
ON CONFLICT (id) DO NOTHING;

-- Bonus Tiers for Branch Manager
INSERT INTO bonus_tiers (id, bonus_rule_id, tier_order, achievement_from, achievement_to, bonus_amount) VALUES
    ('TIER1', 'BRANCH_MANAGER_TIER', 1, 80.0, 89.99, 500000),
    ('TIER2', 'BRANCH_MANAGER_TIER', 2, 90.0, 99.99, 1000000),
    ('TIER3', 'BRANCH_MANAGER_TIER', 3, 100.0, 119.99, 2000000),
    ('TIER4', 'BRANCH_MANAGER_TIER', 4, 120.0, 999.99, 3000000)
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
