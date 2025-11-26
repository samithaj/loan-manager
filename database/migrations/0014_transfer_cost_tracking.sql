-- ============================================================================
-- Migration: Transfer Cost Tracking
-- Version: 0014
-- Description: Adds transfer cost fields to bicycle_transfers and integrates
--              with vehicle cost ledger for proper cost tracking
-- ============================================================================

-- ============================================================================
-- 1. ADD TRANSFER COST FIELDS TO BICYCLE_TRANSFERS
-- ============================================================================

-- Add transfer_cost column
ALTER TABLE bicycle_transfers
    ADD COLUMN IF NOT EXISTS transfer_cost DECIMAL(12,2) DEFAULT 0
        CONSTRAINT positive_transfer_cost CHECK (transfer_cost >= 0);

-- Add cost_breakdown JSONB for detailed cost tracking
ALTER TABLE bicycle_transfers
    ADD COLUMN IF NOT EXISTS cost_breakdown JSONB DEFAULT '{}'::jsonb;

-- Example cost_breakdown structure:
-- {
--   "transport_fee": 5000.00,
--   "handling_charge": 500.00,
--   "insurance": 1000.00,
--   "road_permits": 200.00,
--   "fuel": 300.00,
--   "other": 150.00
-- }

-- Add index for transfers with costs
CREATE INDEX IF NOT EXISTS idx_transfers_with_cost
    ON bicycle_transfers(bicycle_id, transfer_cost)
    WHERE transfer_cost > 0;

-- ============================================================================
-- 2. ADD COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON COLUMN bicycle_transfers.transfer_cost IS
    'Total cost of transfer including transport, insurance, permits, etc.';

COMMENT ON COLUMN bicycle_transfers.cost_breakdown IS
    'JSON breakdown of transfer costs by category (transport_fee, handling_charge, insurance, etc.)';

-- ============================================================================
-- 3. CREATE VIEW FOR TRANSFER COST ANALYTICS
-- ============================================================================

CREATE OR REPLACE VIEW transfer_cost_summary AS
SELECT
    t.id as transfer_id,
    t.bicycle_id,
    t.from_branch_id,
    t.to_branch_id,
    t.status,
    t.transfer_cost,
    t.cost_breakdown,
    t.completed_at,
    b.brand,
    b.model,
    b.current_stock_number,
    fb.name as from_branch_name,
    tb.name as to_branch_name
FROM bicycle_transfers t
JOIN bicycles b ON t.bicycle_id = b.id
JOIN offices fb ON t.from_branch_id = fb.id
JOIN offices tb ON t.to_branch_id = tb.id
WHERE t.status = 'COMPLETED'
  AND t.transfer_cost > 0;

COMMENT ON VIEW transfer_cost_summary IS
    'Summary of completed transfers with costs for analytics and reporting';

-- ============================================================================
-- 4. EXAMPLE DATA FOR TESTING (OPTIONAL - COMMENT OUT FOR PRODUCTION)
-- ============================================================================

-- Update existing transfers with sample cost data (if needed)
-- UPDATE bicycle_transfers
-- SET
--     transfer_cost = 2000.00,
--     cost_breakdown = jsonb_build_object(
--         'transport_fee', 1500.00,
--         'handling_charge', 300.00,
--         'insurance', 200.00
--     )
-- WHERE status = 'COMPLETED'
--   AND transfer_cost = 0
--   LIMIT 5;

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
