# Implementation Plan: Critical Gaps & Verifications

**Branch:** `claude/gap-analysis-bike-system-01RSzPzc8hYJzyyj9R4p4juZ`
**Start Date:** 2025-11-23
**Estimated Completion:** 6-8 weeks (broken into phases)

---

## Phase 1: Core Infrastructure (Week 1-2)

### 1. Vendor/Supplier Management Module

#### Database Schema
```sql
-- Migration: 0013_vendor_management.sql

CREATE TABLE vendors (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL REFERENCES companies(id),
    vendor_code TEXT NOT NULL,
    name TEXT NOT NULL,
    contact_person TEXT,
    phone TEXT,
    email TEXT,
    address TEXT,
    city TEXT,
    country TEXT DEFAULT 'Sri Lanka',
    tax_id TEXT,
    payment_terms TEXT,
    credit_limit DECIMAL(15,2),
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_by TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(company_id, vendor_code)
);

-- Update part_stock_batches to use FK
ALTER TABLE part_stock_batches
    DROP COLUMN supplier_id,
    ADD COLUMN vendor_id TEXT REFERENCES vendors(id);
```

#### Backend Implementation
- **Router:** `/backend/app/routers/vendors.py`
  - CRUD endpoints
  - List with filters (company, active status)
  - Search by name/code
  - Vendor performance metrics

- **Service:** `/backend/app/services/vendor_service.py`
  - Business logic
  - Validation
  - Vendor code generation

#### Frontend Implementation
- **Pages:**
  - `/frontend/src/app/vendors/page.tsx` - List view
  - `/frontend/src/app/vendors/new/page.tsx` - Create form
  - `/frontend/src/app/vendors/[id]/page.tsx` - Detail/edit view

- **Components:**
  - `VendorForm.tsx` - Reusable form
  - `VendorSelector.tsx` - Dropdown for parts purchasing

#### Permissions
- `vendors:read` - View vendors
- `vendors:write` - Create/edit vendors
- `vendors:delete` - Delete vendors

---

### 2. Vehicle Cost Ledger System

#### Database Schema
```sql
-- Migration: 0014_vehicle_cost_ledger.sql

CREATE TYPE cost_entry_type AS ENUM (
    'PURCHASE',
    'REPAIR_PARTS',
    'REPAIR_LABOR',
    'REPAIR_OVERHEAD',
    'TRANSFER_COST',
    'BRANCH_EXPENSE',
    'ADMIN_FEE',
    'DISCOUNT',
    'ADJUSTMENT'
);

CREATE TABLE vehicle_cost_ledger (
    id TEXT PRIMARY KEY,
    bicycle_id TEXT NOT NULL REFERENCES bicycles(id) ON DELETE CASCADE,
    branch_id TEXT NOT NULL REFERENCES offices(id),
    company_id TEXT NOT NULL REFERENCES companies(id),

    cost_type cost_entry_type NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    entry_date DATE NOT NULL DEFAULT CURRENT_DATE,

    -- References to source documents
    reference_type TEXT, -- 'REPAIR_JOB', 'TRANSFER', 'EXPENSE', 'PURCHASE'
    reference_id TEXT,

    description TEXT,
    notes TEXT,

    posted_by TEXT NOT NULL,
    posted_at TIMESTAMPTZ DEFAULT NOW(),

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_cost_ledger_bicycle ON vehicle_cost_ledger(bicycle_id);
CREATE INDEX idx_cost_ledger_date ON vehicle_cost_ledger(entry_date);
CREATE INDEX idx_cost_ledger_type ON vehicle_cost_ledger(cost_type);

-- Create view for easy querying
CREATE VIEW vehicle_total_costs AS
SELECT
    bicycle_id,
    SUM(CASE WHEN cost_type = 'PURCHASE' THEN amount ELSE 0 END) as purchase_cost,
    SUM(CASE WHEN cost_type IN ('REPAIR_PARTS', 'REPAIR_LABOR', 'REPAIR_OVERHEAD') THEN amount ELSE 0 END) as repair_cost,
    SUM(CASE WHEN cost_type = 'TRANSFER_COST' THEN amount ELSE 0 END) as transfer_cost,
    SUM(CASE WHEN cost_type = 'BRANCH_EXPENSE' THEN amount ELSE 0 END) as branch_expense,
    SUM(amount) as total_cost
FROM vehicle_cost_ledger
GROUP BY bicycle_id;
```

#### Backend Implementation
- **Service:** `/backend/app/services/vehicle_cost_service.py`
  - `post_cost_entry()` - Add cost entry
  - `get_vehicle_cost_breakdown()` - Get cost summary
  - `get_cost_history()` - Get ledger entries
  - `recalculate_total_cost()` - Recompute from ledger

- **Integration Points:**
  1. Bicycle creation → Post PURCHASE cost
  2. Repair job completion → Post REPAIR_* costs
  3. Transfer completion → Post TRANSFER_COST
  4. Branch expense creation → Post BRANCH_EXPENSE

#### Migration Strategy
1. Create new tables
2. Migrate existing costs from computed columns to ledger
3. Update all cost-posting logic to use ledger
4. Deprecate computed columns (keep as computed from ledger)

---

### 3. Transfer Cost Tracking

#### Database Schema
```sql
-- Migration: 0015_transfer_cost_tracking.sql

ALTER TABLE bicycle_transfers
    ADD COLUMN transfer_cost DECIMAL(12,2) DEFAULT 0,
    ADD COLUMN cost_breakdown JSONB DEFAULT '{}'::jsonb;

-- Example cost_breakdown structure:
-- {
--   "transport_fee": 5000.00,
--   "handling_charge": 500.00,
--   "insurance": 1000.00,
--   "road_permits": 200.00,
--   "other": 300.00
-- }
```

#### Backend Implementation
- Update `transfer_service.py`:
  - Add `transfer_cost` to approve/complete workflow
  - Post to vehicle cost ledger on completion

- Update `bike_transfers.py` router:
  - Accept `transfer_cost` and `cost_breakdown` in approval

#### Frontend Implementation
- Update transfer approval UI:
  - Add cost input fields
  - Show cost breakdown

---

## Phase 2: Custom Fields Engine (Week 3-4)

### 4. Custom Fields / Form Builder

#### Database Schema
```sql
-- Migration: 0016_custom_fields_system.sql

CREATE TYPE field_data_type AS ENUM (
    'TEXT',
    'NUMBER',
    'DATE',
    'BOOLEAN',
    'SELECT',
    'MULTI_SELECT',
    'FILE',
    'IMAGE',
    'TEXTAREA',
    'EMAIL',
    'PHONE',
    'URL'
);

CREATE TABLE custom_fields (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL REFERENCES companies(id),
    entity_type TEXT NOT NULL, -- 'bicycle', 'loan_application', 'customer', etc.
    field_key TEXT NOT NULL,
    label TEXT NOT NULL,
    data_type field_data_type NOT NULL,

    -- Validation
    is_required BOOLEAN DEFAULT FALSE,
    default_value TEXT,

    -- For SELECT/MULTI_SELECT
    options JSONB, -- ["Option 1", "Option 2"]

    -- For NUMBER
    min_value DECIMAL(15,2),
    max_value DECIMAL(15,2),

    -- For TEXT/TEXTAREA
    max_length INTEGER,

    -- Display
    placeholder TEXT,
    help_text TEXT,
    display_order INTEGER DEFAULT 0,

    -- Conditional display
    conditional_rules JSONB,

    is_active BOOLEAN DEFAULT TRUE,
    created_by TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(company_id, entity_type, field_key)
);

CREATE TABLE custom_field_values (
    id TEXT PRIMARY KEY,
    custom_field_id TEXT NOT NULL REFERENCES custom_fields(id) ON DELETE CASCADE,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    value_json JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(custom_field_id, entity_id)
);

CREATE INDEX idx_custom_field_values_entity ON custom_field_values(entity_type, entity_id);
```

#### Backend Implementation
- **Router:** `/backend/app/routers/custom_fields.py`
  - CRUD for field definitions
  - Get fields for entity type
  - Save/retrieve values

- **Service:** `/backend/app/services/custom_fields_service.py`
  - Validation logic
  - Value serialization/deserialization
  - Conditional logic evaluation

#### Frontend Implementation
- **Form Builder UI:** `/frontend/src/app/admin/custom-fields/`
  - Drag-drop field designer
  - Field configuration panel
  - Preview mode

- **Dynamic Form Renderer:** `DynamicFormRenderer.tsx`
  - Renders fields based on definition
  - Handles all data types
  - Client-side validation

- **Integration:**
  - Loan application form
  - Vehicle details form
  - Customer KYC form

---

## Phase 3: Workflow Enhancements (Week 5)

### 5. Parts Return Workflow UI

#### Backend (Already Exists)
- ✅ `part_stock_movements` with RETURN type
- ✅ Stock batch adjustment logic

#### Frontend Implementation
- **Page:** `/frontend/src/app/workshop/parts/returns/page.tsx`
  - Return form (select job, part, quantity, reason)
  - Return history list

- **Components:**
  - `PartReturnForm.tsx`
  - `ReturnHistoryTable.tsx`

#### Workflow
1. User selects repair job
2. Shows parts used in job
3. User selects part to return + quantity + reason
4. System:
   - Creates RETURN movement
   - Updates batch quantity
   - Creates credit note (optional)

---

### 6. Multi-level Loan Approval Verification

#### Tasks
1. **Review Current Implementation:**
   - Check `loan_applications.py` and `loan_application_service.py`
   - Verify decision tracking in `loan_approvals` table

2. **Implement Threshold-Based Routing:**
   ```sql
   -- If not exists, add to loan approval config
   CREATE TABLE loan_approval_thresholds (
       id TEXT PRIMARY KEY,
       company_id TEXT REFERENCES companies(id),
       min_amount DECIMAL(15,2),
       max_amount DECIMAL(15,2),
       required_approver_role TEXT,
       approval_level INTEGER,
       created_at TIMESTAMPTZ DEFAULT NOW()
   );
   ```

3. **Service Enhancements:**
   - Auto-route based on loan amount
   - Enforce approval sequence (Level 1 → Level 2)
   - Send notifications to next approver

4. **Frontend:**
   - Approval queue with level indicators
   - Approval history timeline

---

### 7. Commission Split Logic Verification

#### Review Points
1. **Check Commission Service:**
   - Does it support branch-specific rules?
   - Can it split between selling/source branches?

2. **Verify Integration:**
   ```python
   # Expected logic in bike_lifecycle_service.py
   def sell_bike():
       # Get source branch from transfer history
       source_branch = get_original_branch(bicycle)
       selling_branch = sale.selling_branch_id

       # Calculate commissions
       if source_branch != selling_branch:
           # Split commission
           selling_commission = profit * selling_branch_pct
           source_commission = profit * source_branch_pct

       # Garage commission from repair jobs
       if bicycle.total_repair_cost > 0:
           garage_commission = calculate_garage_bonus()
   ```

3. **Implement Missing Logic:**
   - Add source branch tracking
   - Add garage incentive calculation
   - Update commission creation

4. **Add Commission Rules:**
   - Selling branch rule
   - Source branch rule
   - Garage incentive rule
   - Sales officer rule

---

## Phase 4: Testing & Documentation (Week 6)

### Testing Checklist

#### Vendor Management
- [ ] Create vendor
- [ ] Edit vendor
- [ ] List vendors with filters
- [ ] Link vendor to part purchase
- [ ] View vendor purchase history

#### Vehicle Cost Ledger
- [ ] Post purchase cost
- [ ] Post repair costs (parts, labor, overhead)
- [ ] Post transfer cost
- [ ] Post branch expense
- [ ] View cost breakdown
- [ ] Calculate total cost
- [ ] Verify profit calculation uses ledger

#### Custom Fields
- [ ] Create field definition (all types)
- [ ] Edit field definition
- [ ] Delete field definition
- [ ] Save field values on entity
- [ ] Retrieve field values
- [ ] Validate required fields
- [ ] Test conditional logic

#### Transfer Costs
- [ ] Add cost to transfer approval
- [ ] Cost posted to ledger
- [ ] Cost included in total cost
- [ ] Cost shown in P&L

#### Parts Return
- [ ] Create return from job
- [ ] Stock quantity updated
- [ ] Movement recorded
- [ ] Return history visible

#### Loan Approval
- [ ] Application routes to Level 1
- [ ] Level 1 approves → routes to Level 2
- [ ] Level 2 approves → disbursement
- [ ] Threshold-based routing works

#### Commission Split
- [ ] Selling branch commission created
- [ ] Source branch commission created (if transferred)
- [ ] Garage commission created (if repairs)
- [ ] Sales officer commission created

---

## Implementation Order

### Week 1-2: Foundation
1. Day 1-2: Vendor Management (DB + Backend)
2. Day 3-4: Vendor Management (Frontend)
3. Day 5-7: Vehicle Cost Ledger (DB + Backend)
4. Day 8-10: Vehicle Cost Ledger (Integration + Migration)

### Week 3-4: Custom Fields
5. Day 11-13: Custom Fields (DB + Backend)
6. Day 14-17: Custom Fields (Form Builder UI)
7. Day 18-20: Custom Fields (Integration)

### Week 5: Workflows
8. Day 21-22: Transfer Cost Tracking
9. Day 23-24: Parts Return UI
10. Day 25-26: Loan Approval Verification
11. Day 27-28: Commission Split Verification

### Week 6: Testing
12. Day 29-32: End-to-end testing
13. Day 33-35: Bug fixes
14. Day 36-40: Documentation & PR

---

## Deliverables

1. **Database Migrations:**
   - 0013_vendor_management.sql
   - 0014_vehicle_cost_ledger.sql
   - 0015_transfer_cost_tracking.sql
   - 0016_custom_fields_system.sql
   - 0017_loan_approval_thresholds.sql (if needed)

2. **Backend Files:**
   - `/backend/app/routers/vendors.py`
   - `/backend/app/routers/custom_fields.py`
   - `/backend/app/services/vendor_service.py`
   - `/backend/app/services/vehicle_cost_service.py`
   - `/backend/app/services/custom_fields_service.py`
   - Updates to existing services

3. **Frontend Files:**
   - `/frontend/src/app/vendors/` (pages)
   - `/frontend/src/app/admin/custom-fields/` (pages)
   - `/frontend/src/app/workshop/parts/returns/` (pages)
   - `/frontend/src/components/vendors/` (components)
   - `/frontend/src/components/forms/DynamicFormRenderer.tsx`
   - `/frontend/src/components/workshop/PartReturnForm.tsx`

4. **Documentation:**
   - API documentation updates
   - User guide for custom fields
   - Migration guide for cost ledger
   - Commission configuration guide

---

## Risk Mitigation

### Data Migration Risks
- **Vehicle Cost Ledger Migration:**
  - Risk: Data loss or inconsistency
  - Mitigation:
    - Backup database before migration
    - Run migration in transaction
    - Verify totals match before/after
    - Keep computed columns for validation

### Breaking Changes
- **Vendor FK on part_stock_batches:**
  - Risk: Existing records have TEXT supplier_id
  - Mitigation:
    - Create vendors from existing supplier names
    - Map old supplier_id to new vendor_id
    - Add migration script for data

### Performance
- **Cost Ledger Queries:**
  - Risk: Slower queries with ledger SUM
  - Mitigation:
    - Add indexed materialized view
    - Cache total costs on bicycle record
    - Use background job to refresh

---

## Success Criteria

✅ All critical gaps addressed
✅ All verifications completed
✅ Tests passing
✅ No breaking changes to existing functionality
✅ Documentation updated
✅ Code review approved
✅ Production deployment ready

---

**Next Steps:**
1. Review this plan
2. Get stakeholder approval
3. Begin implementation in order
4. Daily progress updates
5. Weekly demos

