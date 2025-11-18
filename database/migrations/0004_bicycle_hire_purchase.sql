-- 0004_bicycle_hire_purchase.sql — Database schema extensions for Bicycle Hire Purchase System
-- Run with: psql "$DATABASE_URL" -f database/migrations/0004_bicycle_hire_purchase.sql

-- ======================================================================
-- BICYCLES TABLE
-- ======================================================================
CREATE TABLE IF NOT EXISTS bicycles (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  brand TEXT NOT NULL,
  model TEXT NOT NULL,
  year INTEGER NOT NULL,
  condition TEXT NOT NULL CHECK (condition IN ('NEW', 'USED')),
  license_plate TEXT UNIQUE,
  frame_number TEXT,
  engine_number TEXT,
  purchase_price NUMERIC(12,2) NOT NULL,
  cash_price NUMERIC(12,2) NOT NULL,
  hire_purchase_price NUMERIC(12,2) NOT NULL,
  duty_amount NUMERIC(12,2) DEFAULT 0,
  registration_fee NUMERIC(12,2) DEFAULT 0,
  mileage_km INTEGER,
  description TEXT,
  branch_id TEXT NOT NULL REFERENCES offices(id),
  status TEXT NOT NULL DEFAULT 'AVAILABLE' CHECK (status IN ('AVAILABLE', 'RESERVED', 'SOLD', 'MAINTENANCE')),
  image_urls JSONB DEFAULT '[]'::jsonb,
  thumbnail_url TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for bicycles table
CREATE INDEX IF NOT EXISTS idx_bicycles_branch ON bicycles(branch_id);
CREATE INDEX IF NOT EXISTS idx_bicycles_status ON bicycles(status);
CREATE INDEX IF NOT EXISTS idx_bicycles_condition ON bicycles(condition);
CREATE INDEX IF NOT EXISTS idx_bicycles_license_plate ON bicycles(license_plate);

-- ======================================================================
-- BICYCLE APPLICATIONS TABLE
-- ======================================================================
CREATE TABLE IF NOT EXISTS bicycle_applications (
  id TEXT PRIMARY KEY,
  -- Customer information
  full_name TEXT NOT NULL,
  phone TEXT NOT NULL,
  email TEXT,
  nip_number TEXT,
  -- Address information
  address_line1 TEXT NOT NULL,
  address_line2 TEXT,
  city TEXT NOT NULL,
  -- Employment information
  employer_name TEXT,
  monthly_income NUMERIC(12,2),
  -- Application details
  bicycle_id TEXT NOT NULL REFERENCES bicycles(id),
  branch_id TEXT NOT NULL REFERENCES offices(id),
  tenure_months INTEGER NOT NULL CHECK (tenure_months IN (12, 24, 36, 48)),
  down_payment NUMERIC(12,2) NOT NULL DEFAULT 0,
  -- Status tracking
  status TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'UNDER_REVIEW', 'APPROVED', 'REJECTED', 'CONVERTED_TO_LOAN')),
  notes TEXT,
  loan_id TEXT REFERENCES loans(id),
  -- Audit fields
  submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  reviewed_by UUID REFERENCES users(id),
  reviewed_at TIMESTAMPTZ
);

-- Indexes for bicycle_applications table
CREATE INDEX IF NOT EXISTS idx_bicycle_applications_status ON bicycle_applications(status);
CREATE INDEX IF NOT EXISTS idx_bicycle_applications_branch ON bicycle_applications(branch_id);
CREATE INDEX IF NOT EXISTS idx_bicycle_applications_submitted_at ON bicycle_applications(submitted_at);
CREATE INDEX IF NOT EXISTS idx_bicycle_applications_bicycle ON bicycle_applications(bicycle_id);

-- ======================================================================
-- EXTEND OFFICES TABLE
-- ======================================================================
ALTER TABLE offices ADD COLUMN IF NOT EXISTS allows_bicycle_sales BOOLEAN DEFAULT TRUE;
ALTER TABLE offices ADD COLUMN IF NOT EXISTS bicycle_display_order INTEGER DEFAULT 0;
ALTER TABLE offices ADD COLUMN IF NOT EXISTS map_coordinates JSONB;
ALTER TABLE offices ADD COLUMN IF NOT EXISTS operating_hours TEXT;
ALTER TABLE offices ADD COLUMN IF NOT EXISTS public_description TEXT;

-- ======================================================================
-- EXTEND USERS TABLE FOR METADATA
-- ======================================================================
ALTER TABLE users ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;

-- ======================================================================
-- INSERT BICYCLE HIRE PURCHASE LOAN PRODUCT
-- ======================================================================
INSERT INTO loan_products (id, name, interest_rate, term_months, repayment_frequency)
VALUES (
  'BICYCLE_HP',
  'Bicycle Hire Purchase',
  12.0,
  36,
  'MONTHLY'
) ON CONFLICT (id) DO NOTHING;

-- ======================================================================
-- UPDATED_AT TRIGGER FOR BICYCLES
-- ======================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_bicycles_updated_at BEFORE UPDATE ON bicycles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ======================================================================
-- COMMENTS FOR DOCUMENTATION
-- ======================================================================
COMMENT ON TABLE bicycles IS 'Inventory of bicycles available for hire purchase';
COMMENT ON TABLE bicycle_applications IS 'Customer applications for bicycle hire purchase';
COMMENT ON COLUMN bicycles.status IS 'AVAILABLE: Ready for sale, RESERVED: Application pending, SOLD: Already sold, MAINTENANCE: Under repair';
COMMENT ON COLUMN bicycle_applications.status IS 'PENDING: Just submitted, UNDER_REVIEW: Being reviewed, APPROVED: Approved but not yet converted, REJECTED: Rejected, CONVERTED_TO_LOAN: Converted to active loan';
