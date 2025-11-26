-- ============================================================================
-- Migration: Commission System Enhancements
-- Version: 0016
-- Description: Adds garage incentive and sales officer individual commission
--              to the bike sales commission system
-- ============================================================================

-- ============================================================================
-- 1. ENHANCE BONUS_RULES TABLE
-- ============================================================================

-- Add garage and sales officer commission percentages
ALTER TABLE bonus_rules
    ADD COLUMN IF NOT EXISTS garage_percent DECIMAL(5,2),
    ADD COLUMN IF NOT EXISTS sales_officer_percent DECIMAL(5,2),
    ADD COLUMN IF NOT EXISTS garage_commission_type VARCHAR(20) DEFAULT 'PERCENTAGE';

-- Add check constraint for commission_type values
ALTER TABLE bonus_rules
    ADD CONSTRAINT check_garage_commission_type
    CHECK (garage_commission_type IN ('PERCENTAGE', 'FIXED', 'NONE'));

-- Comments
COMMENT ON COLUMN bonus_rules.garage_percent IS
    'Percentage or fixed amount for garage/workshop incentive when bike has repairs';
COMMENT ON COLUMN bonus_rules.sales_officer_percent IS
    'Percentage for individual sales officer commission';
COMMENT ON COLUMN bonus_rules.garage_commission_type IS
    'Type of garage commission: PERCENTAGE (of sale/profit), FIXED (per sale), or NONE';

-- ============================================================================
-- 2. ENHANCE BONUS_PAYMENTS TABLE
-- ============================================================================

-- Add garage_branch_id and sales_officer_id for tracking
ALTER TABLE bonus_payments
    ADD COLUMN IF NOT EXISTS garage_branch_id TEXT REFERENCES offices(id),
    ADD COLUMN IF NOT EXISTS sales_officer_id UUID REFERENCES users(id);

-- Update commission_type to support new types
COMMENT ON COLUMN bonus_payments.commission_type IS
    'Type of commission: BUYER, SELLER, GARAGE, SALES_OFFICER';

-- Add index for garage and officer lookup
CREATE INDEX IF NOT EXISTS idx_bonus_payments_garage
    ON bonus_payments(garage_branch_id, status)
    WHERE garage_branch_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_bonus_payments_officer
    ON bonus_payments(sales_officer_id, status)
    WHERE sales_officer_id IS NOT NULL;

-- ============================================================================
-- 3. UPDATE EXISTING COMMISSION RULES
-- ============================================================================

-- Update existing bike sales commission rules with default values
UPDATE bonus_rules
SET
    garage_percent = 10,  -- Default 10% garage incentive
    sales_officer_percent = 5,  -- Default 5% sales officer commission
    garage_commission_type = 'PERCENTAGE'
WHERE applies_to_bike_sales = TRUE
    AND is_active = TRUE;

-- ============================================================================
-- 4. CREATE ENHANCED COMMISSION VIEWS
-- ============================================================================

-- View: Commission breakdown by type
CREATE OR REPLACE VIEW commission_breakdown_view AS
SELECT
    bp.id AS payment_id,
    bp.bicycle_sale_id AS sale_id,
    bp.commission_type,
    bp.bonus_amount,
    bp.status,
    bp.created_at,
    bp.approved_at,
    bp.paid_at,

    -- Branch information
    CASE
        WHEN bp.commission_type = 'BUYER' THEN
            (bp.calculation_details->>'branch_id')::text
        WHEN bp.commission_type = 'SELLER' THEN
            (bp.calculation_details->>'branch_id')::text
        WHEN bp.commission_type = 'GARAGE' THEN
            bp.garage_branch_id
        ELSE NULL
    END AS branch_id,

    -- Sales officer information
    CASE
        WHEN bp.commission_type = 'SALES_OFFICER' THEN
            bp.sales_officer_id
        ELSE NULL
    END AS officer_id,

    -- Sale details
    bs.sale_date,
    bs.selling_price,
    bs.profit_or_loss,
    b.license_plate AS bike_no,
    b.brand,
    b.model

FROM bonus_payments bp
LEFT JOIN bicycle_sales bs ON bp.bicycle_sale_id = bs.id
LEFT JOIN bicycles b ON bs.bicycle_id = b.id
WHERE bp.bicycle_sale_id IS NOT NULL;

COMMENT ON VIEW commission_breakdown_view IS
    'Detailed commission breakdown showing all commission types per sale';

-- View: Sales officer commission summary
CREATE OR REPLACE VIEW sales_officer_commission_summary AS
SELECT
    bp.sales_officer_id AS officer_id,
    u.username AS officer_name,
    DATE_TRUNC('month', bp.period_start) AS month,
    COUNT(DISTINCT bp.bicycle_sale_id) AS sales_count,
    SUM(bp.bonus_amount) AS total_commission,
    AVG(bp.bonus_amount) AS avg_commission_per_sale,
    SUM(CASE WHEN bp.status = 'PAID' THEN bp.bonus_amount ELSE 0 END) AS paid_amount,
    SUM(CASE WHEN bp.status = 'PENDING' THEN bp.bonus_amount ELSE 0 END) AS pending_amount,
    SUM(CASE WHEN bp.status = 'APPROVED' THEN bp.bonus_amount ELSE 0 END) AS approved_amount
FROM bonus_payments bp
JOIN users u ON bp.sales_officer_id = u.id
WHERE bp.commission_type = 'SALES_OFFICER'
    AND bp.sales_officer_id IS NOT NULL
GROUP BY bp.sales_officer_id, u.username, DATE_TRUNC('month', bp.period_start)
ORDER BY month DESC, total_commission DESC;

COMMENT ON VIEW sales_officer_commission_summary IS
    'Monthly commission summary for individual sales officers';

-- View: Garage commission summary
CREATE OR REPLACE VIEW garage_commission_summary AS
SELECT
    bp.garage_branch_id,
    o.name AS garage_name,
    DATE_TRUNC('month', bp.period_start) AS month,
    COUNT(DISTINCT bp.bicycle_sale_id) AS sales_with_repairs,
    SUM(bp.bonus_amount) AS total_commission,
    AVG(bp.bonus_amount) AS avg_commission_per_sale,
    SUM(CASE WHEN bp.status = 'PAID' THEN bp.bonus_amount ELSE 0 END) AS paid_amount,
    SUM(CASE WHEN bp.status = 'PENDING' THEN bp.bonus_amount ELSE 0 END) AS pending_amount
FROM bonus_payments bp
JOIN offices o ON bp.garage_branch_id = o.id
WHERE bp.commission_type = 'GARAGE'
    AND bp.garage_branch_id IS NOT NULL
GROUP BY bp.garage_branch_id, o.name, DATE_TRUNC('month', bp.period_start)
ORDER BY month DESC, total_commission DESC;

COMMENT ON VIEW garage_commission_summary IS
    'Monthly commission summary for garage/workshop branches';

-- ============================================================================
-- 5. CREATE SAMPLE COMMISSION RULE WITH ALL COMPONENTS
-- ============================================================================

-- Insert enhanced commission rule (example - adjust for production)
INSERT INTO bonus_rules (
    id,
    name,
    description,
    rule_type,
    applies_to_roles,
    min_achievement_percentage,
    is_active,
    effective_from,
    applies_to_bike_sales,
    commission_base,
    buyer_branch_percent,
    seller_branch_percent,
    garage_percent,
    sales_officer_percent,
    garage_commission_type
)
VALUES (
    'BR-BIKE-COMMISSION-ENHANCED',
    'Enhanced Bike Sales Commission - All Components',
    'Comprehensive commission split: Buyer branch (30%), Seller branch (50%), Garage (10%), Sales Officer (10%)',
    'COMMISSION',
    ARRAY['SALES_OFFICER', 'LOAN_MANAGER'],
    0,
    FALSE,  -- Set to TRUE in production after testing
    CURRENT_DATE,
    TRUE,
    'PROFIT',  -- Base commission on profit
    30,  -- Buyer branch: 30%
    50,  -- Seller branch: 50%
    10,  -- Garage: 10%
    10,  -- Sales officer: 10%
    'PERCENTAGE'
)
ON CONFLICT (id) DO UPDATE SET
    description = EXCLUDED.description,
    buyer_branch_percent = EXCLUDED.buyer_branch_percent,
    seller_branch_percent = EXCLUDED.seller_branch_percent,
    garage_percent = EXCLUDED.garage_percent,
    sales_officer_percent = EXCLUDED.sales_officer_percent,
    garage_commission_type = EXCLUDED.garage_commission_type;

-- ============================================================================
-- 6. ADD HELPER FUNCTION FOR TOTAL COMMISSION PERCENTAGE
-- ============================================================================

CREATE OR REPLACE FUNCTION get_total_commission_percentage(rule_id TEXT)
RETURNS DECIMAL(5,2)
LANGUAGE plpgsql
AS $$
DECLARE
    total_percent DECIMAL(5,2);
BEGIN
    SELECT
        COALESCE(buyer_branch_percent, 0) +
        COALESCE(seller_branch_percent, 0) +
        COALESCE(
            CASE
                WHEN garage_commission_type = 'PERCENTAGE'
                THEN garage_percent
                ELSE 0
            END, 0
        ) +
        COALESCE(sales_officer_percent, 0)
    INTO total_percent
    FROM bonus_rules
    WHERE id = rule_id;

    RETURN total_percent;
END;
$$;

COMMENT ON FUNCTION get_total_commission_percentage IS
    'Calculates total commission percentage for a bonus rule (excluding fixed garage amounts)';

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
