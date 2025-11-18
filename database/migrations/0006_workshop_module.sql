-- ============================================================================
-- Workshop & Spare Parts Module Migration
-- Version: 0006
-- Description: Multi-batch inventory tracking, repair jobs, costing & markup
-- ============================================================================

-- ============================================================================
-- 1. SPARE PARTS MASTER DATA
-- ============================================================================

-- Part categories enum
CREATE TYPE part_category_enum AS ENUM (
    'ENGINE',
    'BRAKE',
    'TYRE',
    'ELECTRICAL',
    'SUSPENSION',
    'TRANSMISSION',
    'EXHAUST',
    'BODY',
    'ACCESSORIES',
    'FLUIDS',
    'CONSUMABLES',
    'OTHER'
);

-- Parts master table
CREATE TABLE IF NOT EXISTS parts (
    id TEXT PRIMARY KEY,
    part_code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    category part_category_enum NOT NULL,
    brand TEXT,
    unit TEXT NOT NULL DEFAULT 'pcs', -- pcs, set, litre, kg, etc.
    is_universal BOOLEAN NOT NULL DEFAULT FALSE,
    bike_model_compatibility JSONB, -- List of compatible bike models
    minimum_stock_level NUMERIC(10,2) DEFAULT 0,
    reorder_point NUMERIC(10,2) DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Stock batch table (each purchase with its own cost)
CREATE TABLE IF NOT EXISTS part_stock_batches (
    id TEXT PRIMARY KEY,
    part_id TEXT NOT NULL REFERENCES parts(id) ON DELETE RESTRICT,
    supplier_id TEXT, -- Could be FK to suppliers table
    branch_id TEXT NOT NULL,
    purchase_date DATE NOT NULL,
    purchase_price_per_unit NUMERIC(15,2) NOT NULL,
    quantity_received NUMERIC(10,2) NOT NULL,
    quantity_available NUMERIC(10,2) NOT NULL,
    expiry_date DATE, -- For oils, fluids, etc.
    invoice_no TEXT,
    grn_no TEXT, -- Goods Receipt Note
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT positive_quantities CHECK (quantity_received >= 0 AND quantity_available >= 0),
    CONSTRAINT available_lte_received CHECK (quantity_available <= quantity_received)
);

-- Stock movement audit log
CREATE TYPE stock_movement_type AS ENUM (
    'PURCHASE',
    'ADJUSTMENT',
    'TRANSFER_IN',
    'TRANSFER_OUT',
    'REPAIR_USAGE',
    'RETURN',
    'WRITE_OFF'
);

CREATE TABLE IF NOT EXISTS part_stock_movements (
    id TEXT PRIMARY KEY,
    part_id TEXT NOT NULL REFERENCES parts(id) ON DELETE RESTRICT,
    batch_id TEXT REFERENCES part_stock_batches(id) ON DELETE SET NULL,
    branch_id TEXT NOT NULL,
    movement_type stock_movement_type NOT NULL,
    quantity NUMERIC(10,2) NOT NULL, -- Positive or negative
    unit_cost NUMERIC(15,2), -- Cost at time of movement
    total_cost NUMERIC(15,2), -- quantity * unit_cost
    related_doc_type TEXT, -- 'PO', 'WORK_ORDER', 'TRANSFER', etc.
    related_doc_id TEXT,
    notes TEXT,
    created_by TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- 2. REPAIR JOBS / WORK ORDERS
-- ============================================================================

-- Job types
CREATE TYPE repair_job_type AS ENUM (
    'SERVICE',
    'ACCIDENT_REPAIR',
    'FULL_OVERHAUL_BEFORE_SALE',
    'MAINTENANCE',
    'CUSTOM_WORK',
    'WARRANTY_REPAIR'
);

-- Job status
CREATE TYPE repair_job_status AS ENUM (
    'OPEN',
    'IN_PROGRESS',
    'COMPLETED',
    'INVOICED',
    'CANCELLED'
);

-- Main repair job table
CREATE TABLE IF NOT EXISTS repair_jobs (
    id TEXT PRIMARY KEY,
    job_number TEXT NOT NULL UNIQUE,
    bicycle_id TEXT NOT NULL, -- FK to bicycles table
    branch_id TEXT NOT NULL,
    job_type repair_job_type NOT NULL,
    status repair_job_status NOT NULL DEFAULT 'OPEN',
    opened_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,
    odometer INTEGER, -- Current mileage
    customer_complaint TEXT,
    diagnosis TEXT,
    work_performed TEXT,
    mechanic_id TEXT, -- FK to users table
    created_by TEXT,

    -- Costing summary (calculated)
    total_parts_cost NUMERIC(15,2) DEFAULT 0,
    total_labour_cost NUMERIC(15,2) DEFAULT 0,
    total_overhead_cost NUMERIC(15,2) DEFAULT 0,
    total_cost NUMERIC(15,2) DEFAULT 0,

    -- Customer pricing (with markup)
    total_parts_price NUMERIC(15,2) DEFAULT 0,
    total_labour_price NUMERIC(15,2) DEFAULT 0,
    total_overhead_price NUMERIC(15,2) DEFAULT 0,
    total_price NUMERIC(15,2) DEFAULT 0,

    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Parts used in repair jobs
CREATE TABLE IF NOT EXISTS repair_job_parts (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL REFERENCES repair_jobs(id) ON DELETE CASCADE,
    part_id TEXT NOT NULL REFERENCES parts(id) ON DELETE RESTRICT,
    batch_id TEXT REFERENCES part_stock_batches(id) ON DELETE SET NULL,
    quantity_used NUMERIC(10,2) NOT NULL,
    unit_cost NUMERIC(15,2) NOT NULL, -- Booked cost for this job line
    total_cost NUMERIC(15,2) NOT NULL, -- quantity * unit_cost
    unit_price_to_customer NUMERIC(15,2), -- After markup
    total_price_to_customer NUMERIC(15,2),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT positive_quantity CHECK (quantity_used > 0)
);

-- Labour charges for repair jobs
CREATE TABLE IF NOT EXISTS repair_job_labour (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL REFERENCES repair_jobs(id) ON DELETE CASCADE,
    labour_code TEXT,
    description TEXT NOT NULL,
    mechanic_id TEXT, -- FK to users table
    hours NUMERIC(10,2) NOT NULL,
    hourly_rate_cost NUMERIC(15,2) NOT NULL, -- Internal cost rate
    labour_cost NUMERIC(15,2) NOT NULL, -- hours * hourly_rate_cost
    hourly_rate_customer NUMERIC(15,2), -- Customer billing rate
    labour_price_to_customer NUMERIC(15,2),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT positive_hours CHECK (hours > 0)
);

-- Overhead charges (consumables, shop supplies, etc.)
CREATE TABLE IF NOT EXISTS repair_job_overheads (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL REFERENCES repair_jobs(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    cost NUMERIC(15,2) NOT NULL,
    price_to_customer NUMERIC(15,2),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- 3. MARKUP RULES FOR PRICING
-- ============================================================================

CREATE TYPE markup_target_type AS ENUM (
    'PART_CATEGORY',
    'LABOUR',
    'OVERHEAD',
    'BIKE_SALE',
    'DEFAULT'
);

CREATE TYPE markup_type AS ENUM (
    'PERCENTAGE',
    'FIXED_AMOUNT'
);

CREATE TABLE IF NOT EXISTS markup_rules (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    target_type markup_target_type NOT NULL,
    target_value TEXT, -- e.g., 'ENGINE', 'BRAKE', 'DEFAULT'
    markup_type markup_type NOT NULL,
    markup_value NUMERIC(10,2) NOT NULL, -- 25 for 25%, or fixed amount
    applies_to_branches TEXT[], -- List of branch IDs, NULL = all branches
    effective_from DATE NOT NULL,
    effective_to DATE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    priority INTEGER DEFAULT 0, -- Higher priority rules override lower
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- 4. BICYCLE COST TRACKING (Extensions to existing bicycle table)
-- ============================================================================

-- Add repair cost tracking columns to bicycles table
ALTER TABLE bicycles
ADD COLUMN IF NOT EXISTS base_purchase_price NUMERIC(15,2),
ADD COLUMN IF NOT EXISTS total_repair_cost NUMERIC(15,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS total_cost_for_sale NUMERIC(15,2) GENERATED ALWAYS AS (
    COALESCE(base_purchase_price, 0) + COALESCE(total_repair_cost, 0)
) STORED,
ADD COLUMN IF NOT EXISTS configured_markup_percent NUMERIC(5,2),
ADD COLUMN IF NOT EXISTS recommended_sale_price NUMERIC(15,2);

-- ============================================================================
-- 5. INDEXES FOR PERFORMANCE
-- ============================================================================

-- Parts indexes
CREATE INDEX IF NOT EXISTS idx_parts_part_code ON parts(part_code);
CREATE INDEX IF NOT EXISTS idx_parts_category ON parts(category);
CREATE INDEX IF NOT EXISTS idx_parts_is_active ON parts(is_active);

-- Stock batches indexes
CREATE INDEX IF NOT EXISTS idx_part_stock_batches_part_id ON part_stock_batches(part_id);
CREATE INDEX IF NOT EXISTS idx_part_stock_batches_branch_id ON part_stock_batches(branch_id);
CREATE INDEX IF NOT EXISTS idx_part_stock_batches_purchase_date ON part_stock_batches(purchase_date);
CREATE INDEX IF NOT EXISTS idx_part_stock_batches_expiry_date ON part_stock_batches(expiry_date)
    WHERE expiry_date IS NOT NULL;

-- Stock movements indexes
CREATE INDEX IF NOT EXISTS idx_part_stock_movements_part_id ON part_stock_movements(part_id);
CREATE INDEX IF NOT EXISTS idx_part_stock_movements_batch_id ON part_stock_movements(batch_id);
CREATE INDEX IF NOT EXISTS idx_part_stock_movements_branch_id ON part_stock_movements(branch_id);
CREATE INDEX IF NOT EXISTS idx_part_stock_movements_type ON part_stock_movements(movement_type);
CREATE INDEX IF NOT EXISTS idx_part_stock_movements_doc ON part_stock_movements(related_doc_type, related_doc_id);
CREATE INDEX IF NOT EXISTS idx_part_stock_movements_created_at ON part_stock_movements(created_at);

-- Repair jobs indexes
CREATE INDEX IF NOT EXISTS idx_repair_jobs_job_number ON repair_jobs(job_number);
CREATE INDEX IF NOT EXISTS idx_repair_jobs_bicycle_id ON repair_jobs(bicycle_id);
CREATE INDEX IF NOT EXISTS idx_repair_jobs_branch_id ON repair_jobs(branch_id);
CREATE INDEX IF NOT EXISTS idx_repair_jobs_status ON repair_jobs(status);
CREATE INDEX IF NOT EXISTS idx_repair_jobs_job_type ON repair_jobs(job_type);
CREATE INDEX IF NOT EXISTS idx_repair_jobs_mechanic_id ON repair_jobs(mechanic_id);
CREATE INDEX IF NOT EXISTS idx_repair_jobs_opened_at ON repair_jobs(opened_at);

-- Repair job parts indexes
CREATE INDEX IF NOT EXISTS idx_repair_job_parts_job_id ON repair_job_parts(job_id);
CREATE INDEX IF NOT EXISTS idx_repair_job_parts_part_id ON repair_job_parts(part_id);
CREATE INDEX IF NOT EXISTS idx_repair_job_parts_batch_id ON repair_job_parts(batch_id);

-- Repair job labour indexes
CREATE INDEX IF NOT EXISTS idx_repair_job_labour_job_id ON repair_job_labour(job_id);
CREATE INDEX IF NOT EXISTS idx_repair_job_labour_mechanic_id ON repair_job_labour(mechanic_id);

-- Repair job overheads indexes
CREATE INDEX IF NOT EXISTS idx_repair_job_overheads_job_id ON repair_job_overheads(job_id);

-- Markup rules indexes
CREATE INDEX IF NOT EXISTS idx_markup_rules_target ON markup_rules(target_type, target_value);
CREATE INDEX IF NOT EXISTS idx_markup_rules_is_active ON markup_rules(is_active);

-- ============================================================================
-- 6. SEED DATA
-- ============================================================================

-- Default markup rules
INSERT INTO markup_rules (id, name, target_type, target_value, markup_type, markup_value, effective_from, is_active, priority) VALUES
('MR-DEFAULT-PARTS', 'Default Parts Markup', 'PART_CATEGORY', 'DEFAULT', 'PERCENTAGE', 20.00, '2024-01-01', TRUE, 0),
('MR-ENGINE-PARTS', 'Engine Parts Markup', 'PART_CATEGORY', 'ENGINE', 'PERCENTAGE', 25.00, '2024-01-01', TRUE, 1),
('MR-BRAKE-PARTS', 'Brake Parts Markup', 'PART_CATEGORY', 'BRAKE', 'PERCENTAGE', 22.00, '2024-01-01', TRUE, 1),
('MR-DEFAULT-LABOUR', 'Default Labour Markup', 'LABOUR', 'DEFAULT', 'PERCENTAGE', 40.00, '2024-01-01', TRUE, 0),
('MR-DEFAULT-OVERHEAD', 'Default Overhead Markup', 'OVERHEAD', 'DEFAULT', 'PERCENTAGE', 15.00, '2024-01-01', TRUE, 0),
('MR-BIKE-SALE', 'Bike Sale Markup', 'BIKE_SALE', 'DEFAULT', 'PERCENTAGE', 25.00, '2024-01-01', TRUE, 0)
ON CONFLICT (id) DO NOTHING;

-- Sample parts (for testing/demo purposes)
INSERT INTO parts (id, part_code, name, description, category, brand, unit, is_universal, minimum_stock_level, is_active) VALUES
('PART-BRK-PAD-001', 'BRK-PAD-001', 'Front Brake Pad Set', 'Front brake pads for standard bikes', 'BRAKE', 'Generic', 'set', TRUE, 10, TRUE),
('PART-ENG-OIL-001', 'ENG-OIL-001', 'Engine Oil 10W-40', '1 litre engine oil synthetic', 'FLUIDS', 'Castrol', 'litre', TRUE, 20, TRUE),
('PART-TYR-001', 'TYR-001', 'Front Tyre 100/90-17', 'Standard front tyre', 'TYRE', 'Dunlop', 'pcs', FALSE, 5, TRUE),
('PART-CHN-001', 'CHN-001', 'Drive Chain 520', 'Standard drive chain 520 pitch', 'TRANSMISSION', 'DID', 'pcs', FALSE, 5, TRUE),
('PART-SPK-001', 'SPK-001', 'Spark Plug NGK', 'Standard spark plug', 'ENGINE', 'NGK', 'pcs', TRUE, 20, TRUE)
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- 7. COMMENTS
-- ============================================================================

COMMENT ON TABLE parts IS 'Master data for spare parts and components';
COMMENT ON TABLE part_stock_batches IS 'Stock batches with individual purchase prices (FIFO costing)';
COMMENT ON TABLE part_stock_movements IS 'Audit log of all stock movements';
COMMENT ON TABLE repair_jobs IS 'Work orders for bicycle repairs and overhauls';
COMMENT ON TABLE repair_job_parts IS 'Parts used in repair jobs with batch-level costing';
COMMENT ON TABLE repair_job_labour IS 'Labour charges for repair jobs';
COMMENT ON TABLE repair_job_overheads IS 'Overhead and miscellaneous charges for repair jobs';
COMMENT ON TABLE markup_rules IS 'Pricing markup rules for parts, labour, and bike sales';

COMMENT ON COLUMN bicycles.base_purchase_price IS 'Original purchase price of the bicycle';
COMMENT ON COLUMN bicycles.total_repair_cost IS 'Sum of all repair job costs for this bicycle';
COMMENT ON COLUMN bicycles.total_cost_for_sale IS 'Total cost including purchase and repairs (generated column)';
COMMENT ON COLUMN bicycles.configured_markup_percent IS 'Markup percentage to apply for sale pricing';
COMMENT ON COLUMN bicycles.recommended_sale_price IS 'Calculated recommended sale price based on costs and markup';
