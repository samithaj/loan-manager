# Vehicle Cost Aggregator / Ledger System - Implementation Progress

## ✅ Completed Components

### Backend Models (100%)
- ✅ `FundSource` - Fund source tracking (PC, BNK, HO, SUP, etc.)
- ✅ `VehicleCostLedger` - Main cost tracking table with bill numbers
- ✅ `VehicleCostSummary` - Cached cost totals per vehicle
- ✅ `BillNumberSequence` - Bill number generation tracking
- ✅ Models registered in `__init__.py`

### Backend Services (100%)
- ✅ `BillNumberService` - Bill number generation (<BRANCH>-<FUND>-<YYYYMMDD>-<SEQ>)
  - Unique bill number generation
  - Bill number validation
  - Bill number parsing
  - Row-level locking for sequences

- ✅ `VehicleCostService` - Complete cost tracking service
  - Create cost entries
  - Update cost entries (with lock check)
  - List with comprehensive filters
  - Get vehicle cost summary
  - Lock vehicle costs (after sale)
  - Record vehicle sale with profit calculation
  - Auto-update summaries on every change
  - Cost statistics and aggregations

### Backend Schemas (100%)
- ✅ FundSource schemas (Create, Update, Response)
- ✅ VehicleCost schemas (Create, Update, Response, Detail, List)
- ✅ VehicleCostSummary schemas
- ✅ BillNumber schemas (Request, Response, Validation)
- ✅ VehicleSale schemas (Request, Response)
- ✅ Cost filters and queries
- ✅ Statistics schemas
- ✅ Petty cash tracking schemas

## 🚧 Remaining Work

### Backend API (Router) - Not Started
Need to create: `backend/app/routers/vehicle_costs.py`

**Required Endpoints:**
```python
# Fund Sources
POST   /api/v1/vehicle-costs/fund-sources
GET    /api/v1/vehicle-costs/fund-sources
GET    /api/v1/vehicle-costs/fund-sources/{id}
PATCH  /api/v1/vehicle-costs/fund-sources/{id}

# Cost Entries
POST   /api/v1/vehicle-costs/entries
GET    /api/v1/vehicle-costs/entries
GET    /api/v1/vehicle-costs/entries/{id}
PATCH  /api/v1/vehicle-costs/entries/{id}
DELETE /api/v1/vehicle-costs/entries/{id}

# Vehicle Costs
GET    /api/v1/vehicle-costs/vehicles/{vehicle_id}/summary
GET    /api/v1/vehicle-costs/vehicles/{vehicle_id}/entries
POST   /api/v1/vehicle-costs/vehicles/{vehicle_id}/entries
POST   /api/v1/vehicle-costs/vehicles/{vehicle_id}/sale
POST   /api/v1/vehicle-costs/vehicles/{vehicle_id}/lock

# Bill Numbers
POST   /api/v1/vehicle-costs/bill-numbers/generate
POST   /api/v1/vehicle-costs/bill-numbers/validate

# Statistics & Reports
GET    /api/v1/vehicle-costs/statistics
GET    /api/v1/vehicle-costs/petty-cash/{branch_id}/summary
```

### Database Migration - Not Started
Need to create: `database/migrations/0011_vehicle_cost_ledger.sql`

**Tables to Create:**
- fund_sources
- vehicle_cost_ledger
- vehicle_cost_summary
- bill_number_sequences

**Enums to Create:**
- cost_event_type

**Sample Data:**
- Default fund sources (PC, BNK, HO, SUP, CUS)

### Frontend Pages - Not Started

**Required Pages:**
1. `/vehicles/costs` - Vehicle cost list/dashboard
2. `/vehicles/{id}/costs` - Vehicle cost detail
3. `/vehicles/{id}/costs/add` - Add cost entry
4. `/vehicles/costs/reports` - Cost reports and analytics
5. `/vehicles/costs/petty-cash` - Petty cash tracking

### Frontend Components - Not Started

**Required Components:**
1. `CostEntryForm` - Form for adding/editing costs
2. `CostSummaryCard` - Display cost breakdown
3. `BillNumberDisplay` - Formatted bill number display
4. `CostTimeline` - Chronological cost visualization
5. `PettyCashWidget` - Petty cash summary widget
6. `ProfitCalculator` - Sale profit calculator

### Navigation Integration - Not Started
- Add "Vehicle Costs" menu to Header.tsx
- Link from vehicle detail pages to cost tracking

### Tests - Not Started
Need to create: `tests/test_vehicle_cost_workflow.py`

**Test Coverage:**
- Bill number generation uniqueness
- Cost entry creation and updates
- Summary recalculation
- Lock/unlock logic
- Sale recording and profit calculation
- Filter and query operations

## 📊 System Architecture

### Bill Number Format
```
<BRANCH_CODE>-<FUND_CODE>-<YYYYMMDD>-<SEQ>
Example: BD-PC-20251122-0041

Where:
- BD = Badulla branch
- PC = Petty Cash
- 20251122 = November 22, 2025
- 0041 = 41st transaction for this branch+fund+date
```

### Cost Event Types
1. PURCHASE - Initial vehicle purchase
2. BRANCH_TRANSFER - Transfer between branches
3. REPAIR_JOB - Repair work costs
4. SPARE_PARTS - Parts replacement
5. ADMIN_FEES - Administrative costs
6. REGISTRATION - Vehicle registration
7. INSURANCE - Insurance premiums
8. TRANSPORT - Transport/fuel costs
9. FUEL - Fuel expenses
10. INSPECTION - Inspection costs
11. DOCUMENTATION - Document fees
12. OTHER_EXPENSE - Other miscellaneous costs
13. SALE - Vehicle sale (terminal event)

### Cost Summary Fields
- `purchase_cost` - Initial purchase price
- `transfer_cost` - Transfer/transport costs
- `repair_cost` - All repair work
- `parts_cost` - Spare parts
- `admin_cost` - Admin fees
- `registration_cost` - Registration
- `insurance_cost` - Insurance
- `transport_cost` - Transport/fuel
- `other_cost` - Other expenses
- **`total_cost`** - Sum of all above
- `sale_price` - Final sale price
- `profit` - sale_price - total_cost
- `profit_margin_pct` - (profit / sale_price) * 100

## 🔐 Security & Business Rules

### Access Control
- **Branch Managers**: Can only view/add costs for their branch
- **Finance Officers**: Can view all costs, approve high-value entries
- **LMOs**: Can add costs for vehicles they manage
- **Admins**: Full access

### Lock Logic
1. Costs can be edited ONLY if `is_locked = false`
2. All costs are locked when vehicle is SOLD
3. Once locked, no edits allowed (audit trail)
4. Lock requires admin/supervisor approval

### Approval Workflow (Optional Phase 2)
- Costs above threshold require approval
- Fund sources can have different thresholds
- Pending approval entries flagged in reports

## 📈 Reports & Analytics

### Available Reports
1. **Vehicle Landed Cost** - Total cost breakdown per vehicle
2. **Cost by Branch** - Which branch incurred what costs
3. **Repair Cost Analysis** - Most expensive repairs/models
4. **Profit by Branch** - Profit attribution
5. **Petty Cash Usage** - Daily/weekly PC spend by branch
6. **Fund Source Usage** - How much spent from each source

## 🔗 Integration Points

### With Existing Systems
- **Bicycle/Vehicle Module**: Uses existing `bicycles` table
- **Branch System**: Uses `branches` table from loan approval
- **User System**: Uses `users` table for creator/approver tracking
- **Workshop Module**: Can reference `repair_jobs` for automatic cost posting

### Future Integrations
- Automatic cost posting from workshop repairs
- Integration with accounting system
- Bank reconciliation for fund sources
- SMS alerts for high-value transactions

## ⏱️ Estimated Remaining Effort

- **API Router**: 2-3 hours
- **Database Migration**: 1 hour
- **Frontend Pages**: 4-5 hours
- **Frontend Components**: 2-3 hours
- **Navigation Integration**: 30 minutes
- **Tests**: 2-3 hours
- **Documentation**: 1 hour

**Total**: ~12-16 hours of development work

## 🚀 Quick Start (When Complete)

```bash
# 1. Run migration
psql -U postgres -d loan_manager -f database/migrations/0011_vehicle_cost_ledger.sql

# 2. Create default fund sources via API or seed script

# 3. Start tracking costs!
POST /api/v1/vehicle-costs/entries
{
  "vehicle_id": "BIKE123",
  "branch_id": "...",
  "event_type": "REPAIR_JOB",
  "fund_source_id": "...",  # Petty Cash
  "amount": 12500,
  "description": "Front fork replacement"
}

# Bill number generated automatically: BD-PC-20251122-0041
```

## 📝 Notes

- All costs stored in LKR currency (configurable per entry)
- File attachments (receipts) stored as URL arrays
- Metadata JSON field for flexible additional data
- Full audit trail with creator/timestamp
- Summary auto-updates on every cost change
- Thread-safe bill number generation with row locks
