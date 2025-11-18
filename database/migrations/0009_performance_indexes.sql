-- Migration 0009: Performance Indexes for Bike Lifecycle System
-- Adds indexes for common query patterns and filter combinations
-- Duration: ~1-2 minutes on a database with 1000+ bikes
-- Idempotent: Can be run multiple times safely

-- ============================================================================
-- BIKE LOOKUPS
-- ============================================================================

-- Company and branch filtering (very common in reports)
CREATE INDEX IF NOT EXISTS idx_bicycles_company_branch
ON bicycles(company_id, current_branch_id)
WHERE company_id IS NOT NULL;

-- Status and business model filtering (inventory queries)
CREATE INDEX IF NOT EXISTS idx_bicycles_status_model
ON bicycles(status, business_model)
WHERE status IS NOT NULL;

-- Stock number lookup (frequent for transfers and sales)
CREATE INDEX IF NOT EXISTS idx_bicycles_stock_number
ON bicycles(current_stock_number)
WHERE current_stock_number IS NOT NULL;

-- Procurement date range queries (acquisition ledger)
CREATE INDEX IF NOT EXISTS idx_bicycles_procurement_date
ON bicycles(procurement_date DESC)
WHERE procurement_date IS NOT NULL;

-- Sold bikes queries
CREATE INDEX IF NOT EXISTS idx_bicycles_sold_status
ON bicycles(status, selling_date DESC)
WHERE status = 'SOLD';

-- ============================================================================
-- STOCK NUMBER ASSIGNMENTS
-- ============================================================================

-- Current stock number lookups (most common query)
CREATE INDEX IF NOT EXISTS idx_stock_assignments_current
ON stock_number_assignments(bicycle_id, released_date)
WHERE released_date IS NULL;

-- Stock number history by branch
CREATE INDEX IF NOT EXISTS idx_stock_assignments_branch
ON stock_number_assignments(branch_id, assigned_date DESC);

-- Stock number sequence tracking
CREATE INDEX IF NOT EXISTS idx_stock_sequence_company_branch
ON stock_number_sequences(company_id, branch_id);

-- ============================================================================
-- TRANSFERS
-- ============================================================================

-- Pending transfers by destination branch
CREATE INDEX IF NOT EXISTS idx_transfers_status_to_branch
ON bicycle_transfers(status, to_branch_id, requested_at DESC)
WHERE status IN ('PENDING', 'APPROVED', 'IN_TRANSIT');

-- Transfer history by bike
CREATE INDEX IF NOT EXISTS idx_transfers_bicycle
ON bicycle_transfers(bicycle_id, requested_at DESC);

-- Transfers by requesting user (for user dashboards)
CREATE INDEX IF NOT EXISTS idx_transfers_requested_by
ON bicycle_transfers(requested_by, requested_at DESC);

-- ============================================================================
-- SALES
-- ============================================================================

-- Sales by date range and branch (most common report query)
CREATE INDEX IF NOT EXISTS idx_sales_date_branch
ON bicycle_sales(sale_date DESC, selling_branch_id)
WHERE sale_date IS NOT NULL;

-- Sales by bike
CREATE INDEX IF NOT EXISTS idx_sales_bicycle
ON bicycle_sales(bicycle_id);

-- Profitable sales queries
CREATE INDEX IF NOT EXISTS idx_sales_profit
ON bicycle_sales(profit_or_loss DESC)
WHERE profit_or_loss IS NOT NULL;

-- ============================================================================
-- EXPENSES
-- ============================================================================

-- Expenses by bike and category
CREATE INDEX IF NOT EXISTS idx_expenses_bicycle_category
ON bicycle_branch_expenses(bicycle_id, category, expense_date DESC);

-- Expenses by branch and date
CREATE INDEX IF NOT EXISTS idx_expenses_branch_date
ON bicycle_branch_expenses(branch_id, expense_date DESC)
WHERE branch_id IS NOT NULL;

-- ============================================================================
-- COMMISSIONS (BONUS PAYMENTS)
-- ============================================================================

-- Commission payments by sale
CREATE INDEX IF NOT EXISTS idx_bonus_payments_sale
ON bonus_payments(bicycle_sale_id, created_at DESC)
WHERE bicycle_sale_id IS NOT NULL;

-- Commission payments by branch and date (for branch reports)
CREATE INDEX IF NOT EXISTS idx_bonus_payments_branch_date
ON bonus_payments(branch_id, created_at DESC)
WHERE branch_id IS NOT NULL AND bicycle_sale_id IS NOT NULL;

-- ============================================================================
-- COMPOSITE INDEXES FOR COMPLEX QUERIES
-- ============================================================================

-- Cost summary queries (bikes with expenses and status)
CREATE INDEX IF NOT EXISTS idx_bicycles_cost_analysis
ON bicycles(company_id, current_branch_id, status, base_purchase_price)
WHERE base_purchase_price IS NOT NULL;

-- Sale profit analysis (sold bikes with profit)
CREATE INDEX IF NOT EXISTS idx_bicycles_profit_analysis
ON bicycles(company_id, current_branch_id, selling_date, profit_or_loss)
WHERE status = 'SOLD' AND profit_or_loss IS NOT NULL;

-- ============================================================================
-- TEXT SEARCH INDEXES (for bike search functionality)
-- ============================================================================

-- Full-text search on bike title, brand, model
-- CREATE INDEX IF NOT EXISTS idx_bicycles_search
-- ON bicycles USING gin(to_tsvector('english', title || ' ' || brand || ' ' || model));
-- Note: Commented out - enable if full-text search is needed

-- ============================================================================
-- ANALYZE TABLES (update statistics for query planner)
-- ============================================================================

ANALYZE bicycles;
ANALYZE stock_number_assignments;
ANALYZE stock_number_sequences;
ANALYZE bicycle_transfers;
ANALYZE bicycle_sales;
ANALYZE bicycle_branch_expenses;
ANALYZE bonus_payments;
ANALYZE companies;
ANALYZE offices;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Show index sizes for monitoring
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_indexes
LEFT JOIN pg_stat_user_indexes USING (schemaname, tablename, indexname)
WHERE schemaname = 'public'
  AND (
      tablename LIKE 'bicycle%'
      OR tablename = 'stock_number%'
      OR tablename = 'bonus_payments'
  )
ORDER BY tablename, indexname;

-- Show table sizes for comparison
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) AS indexes_size
FROM pg_tables
WHERE schemaname = 'public'
  AND (
      tablename LIKE 'bicycle%'
      OR tablename LIKE 'stock_number%'
      OR tablename = 'bonus_payments'
  )
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
