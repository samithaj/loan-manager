-- ============================================================================
-- Migration: Vendor/Supplier Management System
-- Version: 0013
-- Description: Adds vendors table and links to part stock batches
-- ============================================================================

-- ============================================================================
-- 1. CREATE VENDORS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS vendors (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL REFERENCES companies(id),
    vendor_code TEXT NOT NULL,
    name TEXT NOT NULL,

    -- Contact Information
    contact_person TEXT,
    phone TEXT,
    email TEXT,

    -- Address
    address TEXT,
    city TEXT,
    province TEXT,
    postal_code TEXT,
    country TEXT DEFAULT 'Sri Lanka',

    -- Business Details
    tax_id TEXT,  -- VAT/TIN number
    business_registration_no TEXT,

    -- Payment Terms
    payment_terms TEXT,  -- 'NET_30', 'NET_60', 'COD', etc.
    credit_limit DECIMAL(15,2) DEFAULT 0,
    currency TEXT DEFAULT 'LKR',

    -- Banking (for payments)
    bank_name TEXT,
    bank_account_no TEXT,
    bank_branch TEXT,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,

    -- Performance Metrics (computed)
    total_purchases DECIMAL(15,2) DEFAULT 0,
    total_orders INTEGER DEFAULT 0,
    last_purchase_date DATE,

    -- Notes
    notes TEXT,

    -- Audit
    created_by TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_vendor_code UNIQUE(company_id, vendor_code)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_vendors_company ON vendors(company_id);
CREATE INDEX IF NOT EXISTS idx_vendors_active ON vendors(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_vendors_name ON vendors(name);

-- Trigger for updated_at
CREATE TRIGGER update_vendors_updated_at
    BEFORE UPDATE ON vendors
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 2. MIGRATE EXISTING SUPPLIER DATA
-- ============================================================================

-- Create vendors from existing supplier_id in part_stock_batches
-- This handles the migration from TEXT supplier_id to FK vendor_id

-- First, insert unique suppliers as vendors
INSERT INTO vendors (id, company_id, vendor_code, name, is_active, created_at)
SELECT
    'VEN-' || substr(md5(random()::text), 1, 16) as id,
    'MA' as company_id,  -- Default to first company, adjust as needed
    'VEN-' || row_number() OVER (ORDER BY supplier_id) as vendor_code,
    supplier_id as name,
    TRUE as is_active,
    NOW() as created_at
FROM (
    SELECT DISTINCT supplier_id
    FROM part_stock_batches
    WHERE supplier_id IS NOT NULL AND supplier_id != ''
) as unique_suppliers
ON CONFLICT DO NOTHING;

-- ============================================================================
-- 3. UPDATE PART_STOCK_BATCHES TABLE
-- ============================================================================

-- Add new vendor_id column
ALTER TABLE part_stock_batches
    ADD COLUMN IF NOT EXISTS vendor_id TEXT REFERENCES vendors(id);

-- Populate vendor_id from existing supplier_id
UPDATE part_stock_batches psb
SET vendor_id = v.id
FROM vendors v
WHERE v.name = psb.supplier_id
  AND psb.supplier_id IS NOT NULL
  AND psb.supplier_id != '';

-- Create index
CREATE INDEX IF NOT EXISTS idx_part_stock_batches_vendor ON part_stock_batches(vendor_id);

-- Note: Keep supplier_id column for now (backward compatibility)
-- In future migration, can drop it: ALTER TABLE part_stock_batches DROP COLUMN supplier_id;

-- ============================================================================
-- 4. CREATE VENDOR CATEGORIES (OPTIONAL)
-- ============================================================================

CREATE TABLE IF NOT EXISTS vendor_categories (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Insert common categories
INSERT INTO vendor_categories (id, name, description) VALUES
    ('CAT-PARTS', 'Parts Supplier', 'Motorcycle parts and accessories'),
    ('CAT-TOOLS', 'Tools & Equipment', 'Workshop tools and equipment'),
    ('CAT-FLUIDS', 'Oils & Fluids', 'Lubricants, oils, and fluids'),
    ('CAT-TIRES', 'Tire Supplier', 'Tires and tubes'),
    ('CAT-ELECTRIC', 'Electrical Parts', 'Electrical components'),
    ('CAT-SERVICE', 'Service Provider', 'External services like painting, welding'),
    ('CAT-OTHER', 'Other', 'Miscellaneous suppliers')
ON CONFLICT (name) DO NOTHING;

-- Add category to vendors
ALTER TABLE vendors
    ADD COLUMN IF NOT EXISTS category_id TEXT REFERENCES vendor_categories(id);

-- ============================================================================
-- 5. CREATE VENDOR CONTACTS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS vendor_contacts (
    id TEXT PRIMARY KEY,
    vendor_id TEXT NOT NULL REFERENCES vendors(id) ON DELETE CASCADE,

    name TEXT NOT NULL,
    position TEXT,
    phone TEXT,
    mobile TEXT,
    email TEXT,

    is_primary BOOLEAN DEFAULT FALSE,

    notes TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_vendor_contacts_vendor ON vendor_contacts(vendor_id);

-- Trigger for updated_at
CREATE TRIGGER update_vendor_contacts_updated_at
    BEFORE UPDATE ON vendor_contacts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 6. CREATE VIEWS FOR REPORTING
-- ============================================================================

-- Vendor Performance View
CREATE OR REPLACE VIEW vendor_performance AS
SELECT
    v.id,
    v.vendor_code,
    v.name,
    v.company_id,
    COUNT(DISTINCT psb.id) as total_batches,
    SUM(psb.quantity_received) as total_quantity_purchased,
    SUM(psb.quantity_received * psb.purchase_price_per_unit) as total_purchase_value,
    AVG(psb.purchase_price_per_unit) as avg_purchase_price,
    MAX(psb.purchase_date) as last_purchase_date,
    MIN(psb.purchase_date) as first_purchase_date
FROM vendors v
LEFT JOIN part_stock_batches psb ON psb.vendor_id = v.id
GROUP BY v.id, v.vendor_code, v.name, v.company_id;

-- ============================================================================
-- 7. SEED DEFAULT VENDORS (OPTIONAL)
-- ============================================================================

-- Add a default "Unknown" vendor for legacy data
INSERT INTO vendors (id, company_id, vendor_code, name, is_active, created_by)
VALUES
    ('VEN-UNKNOWN', 'MA', 'UNK', 'Unknown Vendor', TRUE, 'SYSTEM'),
    ('VEN-CASH', 'MA', 'CASH', 'Cash Purchase', TRUE, 'SYSTEM'),
    ('VEN-INTERNAL', 'MA', 'INT', 'Internal Transfer', TRUE, 'SYSTEM')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE vendors IS 'Suppliers/vendors for parts and services';
COMMENT ON TABLE vendor_categories IS 'Categories for organizing vendors';
COMMENT ON TABLE vendor_contacts IS 'Contact persons at vendor companies';
COMMENT ON VIEW vendor_performance IS 'Vendor purchase history and performance metrics';

COMMENT ON COLUMN vendors.payment_terms IS 'Payment terms: NET_30, NET_60, COD, etc.';
COMMENT ON COLUMN vendors.credit_limit IS 'Maximum credit allowed for this vendor';
COMMENT ON COLUMN vendors.total_purchases IS 'Lifetime total purchases from vendor';
COMMENT ON COLUMN vendors.total_orders IS 'Total number of purchase orders';

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
