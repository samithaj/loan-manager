# Workshop + Spare Parts Module - UX Flow & Component Plan

## 1. Navigation Structure

### Main Header Navigation (Updated)
```
Logo | Reference | Loan Products | Clients | Inventory | Workshop ▾ | Applications | [User] Logout
                                                           │
                                                           ├── Dashboard
                                                           ├── Parts Inventory
                                                           ├── Stock Batches
                                                           ├── Repair Jobs
                                                           ├── Job Calendar
                                                           ├── Markup Rules
                                                           └── Reports
```

### Workshop Dashboard (Landing Page)
- Quick Stats Cards:
  - Active Jobs (OPEN + IN_PROGRESS)
  - Low Stock Alerts
  - Jobs Completed Today
  - Today's Revenue
  - Parts Value
  - Average Margin %
- Quick Actions:
  - 🔧 New Repair Job
  - 📦 Receive Stock
  - 🔍 Search Parts
  - 📊 View Reports
- Recent Activity Feed:
  - Latest jobs opened/completed
  - Stock movements
  - Low stock alerts

---

## 2. User Roles & Permissions

### Mechanic
- View assigned repair jobs
- Add parts/labour to jobs
- Update job status (OPEN → IN_PROGRESS → COMPLETED)
- View parts inventory (read-only)

### Workshop Manager
- All mechanic permissions
- Create/edit repair jobs
- Manage parts catalog
- Receive stock batches
- Stock adjustments
- View job costs & margins
- Assign mechanics

### Inventory Manager
- Manage parts catalog (CRUD)
- Receive stock batches
- Stock adjustments & transfers
- View stock movements
- Manage suppliers
- Set reorder points

### Finance/Admin
- All permissions
- Configure markup rules
- View full cost breakdowns
- Reports & analytics
- Set bike sale prices

---

## 3. Core UX Flows

### Flow 1: Receive New Stock Batch
**Actor:** Inventory Manager

```
1. Navigate to Workshop → Stock Batches
2. Click "Receive Stock" button
3. Form appears:
   ├── Search/Select Part (autocomplete)
   │   └── If not found → Quick create part inline
   ├── Supplier (dropdown)
   ├── Branch (dropdown, default: user's branch)
   ├── Purchase Date (date picker, default: today)
   ├── Unit Price (currency input)
   ├── Quantity Received (number)
   ├── Expiry Date (optional, for oils/fluids)
   ├── Invoice/GRN Number
   └── [Save] [Cancel]
4. On save:
   ├── Create PartStockBatch record
   ├── Create PURCHASE movement record
   ├── Show success message with batch details
   └── Update parts inventory count
5. Option to "Receive Another" or "View Stock"
```

**Component:** `<StockReceiveForm />`

---

### Flow 2: Create Repair Job
**Actor:** Workshop Manager or Mechanic

```
1. Navigate to Workshop → Repair Jobs
2. Click "New Job" button
3. Job Creation Wizard (3 steps):

   STEP 1: Basic Info
   ├── Search Bike (by license plate, frame number, or ID)
   │   └── Shows: Photo, Model, Current odometer, Last service
   ├── Job Type (dropdown)
   │   ├── SERVICE (routine maintenance)
   │   ├── ACCIDENT_REPAIR
   │   ├── FULL_OVERHAUL_BEFORE_SALE ⭐
   │   ├── MAINTENANCE
   │   ├── CUSTOM_WORK
   │   └── WARRANTY_REPAIR
   ├── Branch (auto-fill from bike location)
   ├── Current Odometer (number)
   ├── Customer Complaint (textarea)
   ├── Priority (Low/Normal/High/Urgent)
   └── [Next →]

   STEP 2: Assignment
   ├── Assign Mechanic (dropdown with photos)
   ├── Estimated Completion Date
   ├── Initial Diagnosis (textarea, optional)
   └── [← Back] [Next →]

   STEP 3: Review & Open
   ├── Summary of all details
   ├── Auto-generated Job Number preview
   └── [← Back] [Create Job]

4. Job created with status = OPEN
5. Redirect to Job Detail page
```

**Components:**
- `<RepairJobWizard />`
- `<BikeSearchSelector />` (reusable)
- `<MechanicSelector />`

---

### Flow 3: Add Parts to Repair Job
**Actor:** Mechanic or Workshop Manager

```
1. On Job Detail page, navigate to "Parts" tab
2. Click "Add Part" button
3. Add Part Modal:
   ├── Search Part (autocomplete with fuzzy search)
   │   ├── Shows: Part code, Name, Category badge
   │   ├── Real-time stock availability: "12 pcs available at Branch A"
   │   └── Average cost preview
   ├── Quantity Needed (number input)
   │   └── Validation: Cannot exceed available stock
   ├── Auto-populated fields:
   │   ├── Batch Selection (auto FIFO, show batch details)
   │   ├── Unit Cost (from batch, read-only)
   │   ├── Total Cost (calculated)
   │   ├── Unit Price to Customer (from markup rule, editable)
   │   └── Total Price to Customer (calculated)
   ├── Override reason (if price manually changed)
   └── [Add] [Cancel]

4. Part added to job:
   ├── Create RepairJobPart record
   ├── Create REPAIR_USAGE stock movement
   ├── Update batch quantity_available
   ├── Recalculate job totals
   └── Show in parts table

5. Parts Table shows:
   ├── Part Code | Name | Quantity | Unit Cost | Total Cost | Markup | Customer Price
   ├── Row Actions: [Edit Qty] [Remove]
   └── Totals Row: Sum of costs and prices
```

**Components:**
- `<AddPartToJobModal />`
- `<PartSearch />` (reusable autocomplete)
- `<JobPartsTable />`

---

### Flow 4: Add Labour to Repair Job
**Actor:** Mechanic or Workshop Manager

```
1. On Job Detail page, navigate to "Labour" tab
2. Click "Add Labour" button
3. Add Labour Modal:
   ├── Labour Type (dropdown or custom)
   │   ├── Predefined: Engine overhaul, Oil change, Brake service, etc.
   │   └── Custom description
   ├── Mechanic (dropdown, default: assigned mechanic)
   ├── Hours (decimal input: 1.5 hours)
   ├── Auto-populated fields:
   │   ├── Hourly Rate (Cost) - from config or mechanic profile
   │   ├── Labour Cost (calculated)
   │   ├── Hourly Rate (Customer) - with markup
   │   └── Labour Price to Customer (calculated)
   ├── Notes (optional)
   └── [Add] [Cancel]

4. Labour line added:
   ├── Create RepairJobLabour record
   ├── Recalculate job totals
   └── Show in labour table

5. Labour Table shows:
   ├── Description | Mechanic | Hours | Cost Rate | Total Cost | Bill Rate | Customer Price
   ├── Row Actions: [Edit] [Remove]
   └── Totals Row
```

**Components:**
- `<AddLabourModal />`
- `<JobLabourTable />`

---

### Flow 5: Complete Repair Job
**Actor:** Workshop Manager

```
1. Job Detail page with all parts, labour, overhead added
2. Status progression buttons:
   ├── OPEN → [Start Job] → IN_PROGRESS
   └── IN_PROGRESS → [Mark Complete] → COMPLETED

3. When clicking [Mark Complete]:
   ├── Validation:
   │   ├── ✓ At least one part or labour added
   │   └── ✓ Work performed notes filled
   ├── Final Review Modal:
   │   ├── Internal Costs Breakdown:
   │   │   ├── Parts Cost: $X
   │   │   ├── Labour Cost: $Y
   │   │   ├── Overhead: $Z
   │   │   └── Total Cost: $W
   │   ├── Customer Pricing:
   │   │   ├── Parts: $X'
   │   │   ├── Labour: $Y'
   │   │   ├── Overhead: $Z'
   │   │   └── Total Price: $W'
   │   ├── Profitability:
   │   │   ├── Gross Profit: $(W' - W)
   │   │   └── Margin: X%
   │   ├── For FULL_OVERHAUL_BEFORE_SALE jobs:
   │   │   ├── ⚠️ "This job's cost will be added to the bike's total cost"
   │   │   ├── Bike Base Purchase Price: $A
   │   │   ├── This Repair Cost: $W
   │   │   ├── New Total Bike Cost: $A + $W
   │   │   └── Option to set/update bike sale price
   │   └── [Confirm Complete] [Back]

4. On confirm:
   ├── Update job status to COMPLETED
   ├── Set completed_at timestamp
   ├── If job_type = FULL_OVERHAUL_BEFORE_SALE:
   │   └── Update bicycle record:
   │       ├── total_repair_cost += job.total_cost
   │       └── Recalculate total_cost_for_sale
   ├── Create notification for manager
   └── Show success message

5. Next action options:
   ├── [Generate Invoice] → Goes to invoicing (future)
   ├── [View Bike] → Go to bike detail page
   └── [Back to Jobs] → Jobs list
```

**Components:**
- `<JobStatusButtons />`
- `<CompleteJobModal />`
- `<JobCostBreakdown />` (reusable)

---

### Flow 6: View Bike with Repair Costs
**Actor:** Any user with bike view permission

```
1. Navigate to Bikes → [Select Bike]
2. Bike Detail Page shows:

   COST SUMMARY WIDGET (Enhanced):
   ├── Purchase Price: $5,000
   ├── Total Repair Costs: $1,200 ⬅️ NEW
   │   └── Link: "View 3 repair jobs →"
   ├── Total Cost for Sale: $6,200 ⬅️ CALCULATED
   ├── Configured Markup: 25%
   ├── Recommended Sale Price: $7,750
   └── Current Listed Price: $8,000

   REPAIR HISTORY TAB: ⬅️ NEW
   ├── List of all repair jobs for this bike
   ├── Table: Job# | Date | Type | Status | Cost | Actions
   ├── Summary: Total spent on repairs
   └── [New Repair Job] button

   PROFITABILITY WIDGET: ⬅️ NEW
   ├── If sold at current price:
   │   ├── Revenue: $8,000
   │   ├── Total Cost: $6,200
   │   ├── Gross Profit: $1,800
   │   └── Margin: 29%
   └── Visual: Profit gauge or bar chart
```

**Components:**
- `<BikeCostSummary />` (enhanced version)
- `<BikeRepairHistory />`
- `<BikeProfitability />`

---

### Flow 7: Configure Markup Rules
**Actor:** Finance/Admin

```
1. Navigate to Workshop → Markup Rules
2. Rules List Table:
   ├── Columns: Name | Target Type | Target Value | Markup | Status | Priority | Actions
   ├── Filters: Target Type, Active Only
   ├── Search by name
   └── [Create Rule] button

3. Create/Edit Rule Form:
   ├── Rule Name (e.g., "Premium Engine Parts Markup")
   ├── Target Type (dropdown)
   │   ├── PART_CATEGORY
   │   ├── LABOUR
   │   ├── OVERHEAD
   │   ├── BIKE_SALE
   │   └── DEFAULT
   ├── Target Value (conditional dropdown)
   │   ├── If PART_CATEGORY: ENGINE, BRAKE, TYRE, etc.
   │   └── If DEFAULT: "ALL"
   ├── Markup Type: PERCENTAGE or FIXED_AMOUNT (radio)
   ├── Markup Value (number input)
   │   └── Help text: "25 for 25% or $25 fixed"
   ├── Applies to Branches (multi-select, null = all)
   ├── Effective Date Range:
   │   ├── From (date)
   │   └── To (date, optional)
   ├── Priority (1-10, for overlapping rules)
   ├── Active (toggle)
   └── [Save] [Cancel]

4. Rule Precedence Info:
   ├── Shows how rules are applied in order
   └── Preview: "For ENGINE parts, 25% markup will apply"

5. Bulk Actions:
   ├── Activate/Deactivate multiple rules
   └── Clone rule
```

**Components:**
- `<MarkupRulesManager />`
- `<MarkupRuleForm />`

---

### Flow 8: Stock Adjustment
**Actor:** Inventory Manager

```
1. Navigate to Parts Inventory
2. Find part → Click "Adjust Stock"
3. Adjustment Modal:
   ├── Part Info (read-only): Code, Name, Current Total Stock
   ├── Branch (dropdown)
   ├── Current Stock at Branch: X pcs
   ├── Adjustment Type (radio):
   │   ├── Physical Count (Recount discovered difference)
   │   ├── Damaged/Write-off
   │   ├── Found/Added
   │   └── Other
   ├── New Quantity (number input)
   │   └── Shows difference: "+5" or "-3"
   ├── Reason (required textarea)
   ├── Batch Selection (if reducing stock):
   │   └── Which batch to deduct from (dropdown)
   ├── Cost Impact Preview:
   │   └── "This will adjust inventory value by -$150"
   └── [Confirm] [Cancel]

4. On confirm:
   ├── Create ADJUSTMENT movement record
   ├── Update batch quantity
   ├── Log action with reason
   └── Show success notification
```

**Components:**
- `<StockAdjustmentModal />`

---

### Flow 9: Inter-Branch Stock Transfer
**Actor:** Inventory Manager

```
1. Navigate to Workshop → Stock Batches
2. Click "Transfer Stock" button
3. Transfer Wizard:

   STEP 1: Select Items
   ├── From Branch (dropdown)
   ├── To Branch (dropdown)
   ├── Part Search & Add:
   │   ├── Search part
   │   ├── Available stock at FROM branch
   │   ├── Quantity to transfer (with validation)
   │   ├── Batch selection (auto FIFO or manual)
   │   └── [Add to Transfer]
   ├── Transfer Items List (table)
   │   └── Part | Batch | Qty | Unit Cost | Total Value
   └── [Next →]

   STEP 2: Transfer Details
   ├── Transfer Date (default: today)
   ├── Reference Number (auto-generated)
   ├── Notes
   ├── Approval Required? (if over threshold)
   └── [← Back] [Submit Transfer]

4. On submit:
   ├── Create two movement records per item:
   │   ├── TRANSFER_OUT for FROM branch (-qty)
   │   └── TRANSFER_IN for TO branch (+qty)
   ├── Update batch quantities
   ├── Create transfer document/receipt
   └── Notify TO branch manager

5. Transfer Status Tracking:
   ├── INITIATED
   ├── IN_TRANSIT
   ├── RECEIVED (TO branch confirms)
   └── History of all transfers
```

**Components:**
- `<StockTransferWizard />`
- `<TransferHistory />`

---

### Flow 10: Reports & Analytics
**Actor:** Workshop Manager, Finance

#### Report Types:

**A. Job Profitability Report**
```
Filters:
├── Date Range
├── Branch
├── Job Type
├── Mechanic
└── Status

Table:
├── Job# | Bike | Date | Type | Cost | Price | Profit | Margin%
├── Sortable columns
├── Export to CSV/PDF
└── Summary Totals

Visualizations:
├── Profit Trend (line chart)
├── Margin by Job Type (bar chart)
└── Top Profitable Jobs (top 10)
```

**B. Parts Inventory Report**
```
Filters:
├── Branch
├── Category
├── Stock Level (All/Low Stock/Out of Stock)
└── Value Range

Table:
├── Part Code | Name | Category | Total Qty | Avg Cost | Total Value | Status
├── Color-coded: Red = Below minimum, Orange = Near minimum
└── Reorder Recommendations

Visualizations:
├── Inventory Value by Category (pie chart)
├── Stock Level Distribution
└── Slow-Moving Parts (aged inventory)
```

**C. Mechanic Performance Report**
```
Filters:
├── Date Range
├── Branch
└── Mechanic

Metrics per Mechanic:
├── Jobs Completed
├── Total Labour Hours
├── Average Job Completion Time
├── Total Revenue Generated
├── Customer Ratings (if implemented)
└── Efficiency Score

Visualizations:
├── Jobs Completed Trend
├── Mechanic Comparison (bar chart)
└── Workload Distribution
```

**D. Cost Analysis Report (Bike Level)**
```
For bikes with FULL_OVERHAUL_BEFORE_SALE jobs:

Table:
├── Bike Model | Purchase Price | Repair Costs | Total Cost | Sale Price | Profit | Margin%
├── Filter by: Date Range, Status (sold/unsold), Branch
└── Summary: Total invested, Total revenue, Total profit

Visualizations:
├── Cost Breakdown (stacked bar: purchase vs repair)
├── Margin Distribution
└── ROI by Bike Model
```

**Components:**
- `<ReportDashboard />`
- `<JobProfitabilityReport />`
- `<PartsInventoryReport />`
- `<MechanicPerformanceReport />`
- `<BikeOverhaulCostReport />`

---

## 4. Page-Level Component Map

### `/app/workshop/page.tsx` - Workshop Dashboard
```tsx
Components:
├── <WorkshopStatsCards />
│   ├── <StatCard title="Active Jobs" value={12} icon="🔧" />
│   ├── <StatCard title="Low Stock Items" value={5} trend="warning" />
│   └── ...
├── <QuickActions />
│   └── [New Job] [Receive Stock] [Search Parts] [Reports]
├── <RecentActivityFeed />
│   └── List of latest movements/jobs
└── <JobStatusSummary />
    └── Pipeline: Open → In Progress → Completed
```

### `/app/workshop/parts/page.tsx` - Parts Inventory (Enhanced)
```tsx
Current Features ✓:
- Dual view: Stock Summary cards / Parts Catalog table
- Filters: Category, Search
- Inventory summary stats

Enhancements Needed:
├── <PartCRUDActions />
│   └── [Create Part] [Import CSV] [Export]
├── <StockLevelIndicators />
│   └── Visual alerts for low stock
├── <BulkActions />
│   └── Multi-select for adjustments
└── Links to:
    ├── "View Batches" → /workshop/parts/[id]/batches
    ├── "Movement History" → /workshop/parts/[id]/movements
    └── "Adjust Stock" → Opens modal
```

### `/app/workshop/parts/[id]/page.tsx` - Part Detail (NEW)
```tsx
Components:
├── <PartDetailHeader />
│   ├── Part code, name, category badge
│   ├── Edit/Delete buttons
│   └── Active status toggle
├── <TabNavigation />
│   ├── Overview
│   ├── Stock Batches
│   ├── Movement History
│   └── Usage Analytics
├── TAB: Overview
│   ├── <PartInfoCard /> (specifications, brand, unit, etc.)
│   ├── <StockSummaryCard /> (total qty, value, locations)
│   └── <ReorderSettings /> (min level, reorder point)
├── TAB: Stock Batches
│   ├── <BatchesTable />
│   │   └── Batch ID | Purchase Date | Supplier | Unit Cost | Qty Avail | Expiry | Actions
│   └── [Receive Stock] button
├── TAB: Movement History
│   ├── <MovementHistoryTable />
│   │   └── Date | Type | Qty | Batch | Branch | Related Doc | User
│   └── Filters: Date range, Movement type
└── TAB: Usage Analytics
    ├── Usage trend chart (qty over time)
    ├── Most used in job types
    └── Average consumption rate
```

### `/app/workshop/parts/new/page.tsx` - Create Part (NEW)
```tsx
<PartForm mode="create">
  ├── Part Code (unique validation)
  ├── Name
  ├── Description (rich text editor)
  ├── Category (dropdown with icons)
  ├── Brand
  ├── Unit (dropdown: pcs, set, litre, kg...)
  ├── Universal Part? (toggle)
  │   └── If NO: Bike Model Compatibility (multi-select)
  ├── Minimum Stock Level
  ├── Reorder Point
  ├── Default Supplier (optional)
  ├── Photo Upload (drag-drop)
  └── [Save] [Save & Add Another] [Cancel]
</PartForm>
```

### `/app/workshop/stock-batches/page.tsx` - Stock Batches (NEW)
```tsx
Components:
├── <StockBatchesTable />
│   ├── Columns: Batch ID | Part | Supplier | Branch | Purchase Date | Unit Cost | Qty Avail | Expiry | Actions
│   ├── Filters:
│   │   ├── Branch (multi-select)
│   │   ├── Date Range
│   │   ├── Supplier
│   │   └── Expiring Soon (checkbox)
│   ├── Search: Part name/code
│   └── Sort: Date, Cost, Quantity
├── Actions:
│   ├── [Receive Stock] → <StockReceiveForm />
│   ├── [Transfer Stock] → <StockTransferWizard />
│   └── [Export] CSV
└── Summary Cards:
    ├── Total Batches
    ├── Total Inventory Value
    └── Expiring This Month
```

### `/app/workshop/jobs/page.tsx` - Repair Jobs List (Enhanced)
```tsx
Current Features ✓:
- Job cards with status, bike info, costs
- Filters: Status, Job Type, Mechanic
- Summary stats

Enhancements:
├── <JobsViewToggle /> (Card view / Table view)
├── <JobsFilters /> (enhanced)
│   ├── Date Range picker
│   ├── Branch (multi-select)
│   ├── Priority filter
│   └── Search: Job#, License plate
├── <JobsTable /> (alternative to cards)
│   └── Job# | Bike | Type | Status | Opened | Mechanic | Cost | Price | Margin | Actions
├── <BulkActions />
│   └── Bulk status updates (for managers)
└── [New Job] → <RepairJobWizard />
```

### `/app/workshop/jobs/[id]/page.tsx` - Job Detail (NEW)
```tsx
Layout:
├── <JobHeader />
│   ├── Job Number, Status badge
│   ├── <JobStatusButtons /> (Start/Complete/Cancel)
│   └── Edit/Delete (if authorized)
├── <BikeInfoCard />
│   ├── Photo, Model, License Plate
│   ├── Link to bike detail
│   └── Current location/branch
├── <JobInfoCard />
│   ├── Job type, Priority
│   ├── Opened date, Mechanic
│   ├── Customer complaint
│   └── Diagnosis notes
├── <TabNavigation />
│   ├── Parts
│   ├── Labour
│   ├── Overhead
│   ├── Cost Summary
│   └── Timeline/Activity
└── Tab Content:

    TAB: Parts
    ├── <JobPartsTable />
    │   └── Part Code | Name | Qty | Unit Cost | Total Cost | Markup | Customer Price | [Remove]
    ├── [Add Part] → <AddPartToJobModal />
    └── Subtotal: Parts Cost / Parts Price

    TAB: Labour
    ├── <JobLabourTable />
    │   └── Description | Mechanic | Hours | Cost Rate | Total Cost | Bill Rate | Customer Price | [Edit] [Remove]
    ├── [Add Labour] → <AddLabourModal />
    └── Subtotal: Labour Cost / Labour Price

    TAB: Overhead
    ├── <JobOverheadTable />
    │   └── Description | Cost | Price to Customer | [Remove]
    ├── [Add Overhead] → <AddOverheadModal />
    └── Subtotal: Overhead Cost / Overhead Price

    TAB: Cost Summary
    ├── <JobCostBreakdown />
    │   ├── Internal Costs:
    │   │   ├── Parts: $X
    │   │   ├── Labour: $Y
    │   │   ├── Overhead: $Z
    │   │   └── Total: $W
    │   ├── Customer Pricing:
    │   │   ├── Parts: $X' (markup: +20%)
    │   │   ├── Labour: $Y' (markup: +40%)
    │   │   ├── Overhead: $Z'
    │   │   └── Total: $W'
    │   └── Profitability:
    │       ├── Gross Profit: $(W' - W)
    │       ├── Margin: X%
    │       └── Visual: Profit gauge
    └── For FULL_OVERHAUL jobs:
        └── <BikeImpactWidget />
            ├── "This cost will be added to bike total cost"
            └── Link to bike detail

    TAB: Timeline
    ├── <ActivityTimeline />
    │   ├── Job opened by [User] at [Time]
    │   ├── Part added: [Part name] × 2
    │   ├── Status changed: OPEN → IN_PROGRESS
    │   ├── Labour added: Engine overhaul - 3.5 hrs
    │   └── Job completed by [User] at [Time]
    └── Audit trail of all changes
```

### `/app/workshop/jobs/new/page.tsx` - Create Job (NEW)
```tsx
<RepairJobWizard>
  <Step1_BasicInfo />
  <Step2_Assignment />
  <Step3_Review />
</RepairJobWizard>
```

### `/app/workshop/markup-rules/page.tsx` - Markup Configuration (NEW)
```tsx
Components:
├── <MarkupRulesTable />
│   ├── Columns: Name | Target | Value | Markup | Priority | Status | Actions
│   ├── Filter: Target Type, Active only
│   └── Search: Rule name
├── [Create Rule] → Opens <MarkupRuleFormModal />
├── Row Actions:
│   ├── [Edit] → <MarkupRuleFormModal mode="edit" />
│   ├── [Clone]
│   ├── [Activate/Deactivate]
│   └── [Delete]
└── <MarkupRulePrecedenceInfo />
    └── Explains how rules are applied
```

### `/app/workshop/reports/page.tsx` - Reports Dashboard (NEW)
```tsx
Components:
├── <ReportSelector />
│   ├── Job Profitability
│   ├── Parts Inventory
│   ├── Mechanic Performance
│   └── Bike Overhaul Cost
├── <ReportFilters /> (dynamic based on report type)
└── <ReportVisualization />
    ├── Charts (using recharts or similar)
    ├── Data tables
    └── Export buttons (CSV, PDF)
```

### `/app/bikes/[id]/page.tsx` - Bike Detail (Enhanced)
```tsx
Current features ✓:
- Bike info, photos, pricing

Enhancements:
├── Add <BikeRepairHistoryTab />
│   ├── Table: Job# | Date | Type | Status | Cost | [View]
│   ├── Summary: Total repair costs
│   └── [New Repair Job] → Pre-fills bike
├── Enhance <BikeCostSummary />
│   ├── Show: Purchase + Repairs = Total Cost
│   ├── Markup % and Sale Price
│   └── Link to "View Repair Jobs"
└── Add <BikeProfitabilityWidget />
    ├── If bike status = FOR_SALE or SOLD
    ├── Show: Revenue vs Total Cost vs Profit
    └── Visual: Profit margin gauge
```

---

## 5. Component Library Structure

### Directory: `/frontend/src/components/workshop/`

```
/workshop/
├── common/
│   ├── PartSearch.tsx (autocomplete)
│   ├── BikeSearchSelector.tsx
│   ├── MechanicSelector.tsx
│   ├── CategoryBadge.tsx
│   ├── StatusBadge.tsx
│   └── CurrencyInput.tsx
│
├── parts/
│   ├── PartForm.tsx (create/edit)
│   ├── PartDetailCard.tsx
│   ├── PartsTable.tsx
│   ├── PartsStockCard.tsx (existing, keep)
│   ├── PartBatchesTable.tsx
│   ├── PartMovementHistory.tsx
│   └── StockLevelIndicator.tsx
│
├── stock/
│   ├── StockReceiveForm.tsx
│   ├── StockAdjustmentModal.tsx
│   ├── StockTransferWizard.tsx
│   ├── BatchesTable.tsx
│   └── TransferHistory.tsx
│
├── jobs/
│   ├── RepairJobWizard.tsx
│   ├── JobCard.tsx (existing, enhance)
│   ├── JobsTable.tsx
│   ├── JobStatusButtons.tsx
│   ├── JobPartsTable.tsx
│   ├── JobLabourTable.tsx
│   ├── JobOverheadTable.tsx
│   ├── JobCostBreakdown.tsx
│   ├── AddPartToJobModal.tsx
│   ├── AddLabourModal.tsx
│   ├── AddOverheadModal.tsx
│   ├── CompleteJobModal.tsx
│   └── ActivityTimeline.tsx
│
├── markup/
│   ├── MarkupRulesTable.tsx
│   ├── MarkupRuleFormModal.tsx
│   └── MarkupRulePrecedenceInfo.tsx
│
├── reports/
│   ├── ReportDashboard.tsx
│   ├── JobProfitabilityReport.tsx
│   ├── PartsInventoryReport.tsx
│   ├── MechanicPerformanceReport.tsx
│   └── BikeOverhaulCostReport.tsx
│
├── dashboard/
│   ├── WorkshopStatsCards.tsx
│   ├── StatCard.tsx
│   ├── QuickActions.tsx
│   ├── RecentActivityFeed.tsx
│   └── JobStatusSummary.tsx
│
└── bike-integration/
    ├── BikeRepairHistory.tsx
    ├── BikeProfitabilityWidget.tsx
    └── BikeImpactWidget.tsx (for job detail page)
```

---

## 6. Responsive Design Patterns

### Mobile (< 768px)
- Stack cards vertically
- Hamburger menu for navigation
- Simplified tables → Card view
- Bottom sheets for modals
- Sticky "Add" FAB button

### Tablet (768px - 1024px)
- 2-column grid for cards
- Side drawer navigation
- Full table views with horizontal scroll
- Modal dialogs

### Desktop (> 1024px)
- 3-column grid for cards
- Full navigation in header
- Wide tables with all columns
- Split view: List + Detail (for jobs)
- Inline editing where possible

---

## 7. State Management Strategy

### Per-Component State (useState)
- Form inputs
- Modal open/close
- UI toggles (view mode, filters)

### URL State (useSearchParams)
- List filters
- Pagination (offset, limit)
- Active tab
- Search queries

### Server State (React Query / SWR)
- API data fetching
- Caching
- Automatic refetch
- Optimistic updates

Example:
```tsx
// Using native fetch with manual state
const [jobs, setJobs] = useState([]);
const [loading, setLoading] = useState(true);

useEffect(() => {
  fetchJobs();
}, [filters]);

// Or using SWR (recommended)
import useSWR from 'swr';
const { data: jobs, error, mutate } = useSWR('/v1/workshop/jobs', fetcher);
```

---

## 8. API Integration Checklist

All endpoints already implemented in backend ✓:

### Parts API
- ✓ GET /v1/workshop/parts
- ✓ POST /v1/workshop/parts
- ✓ GET /v1/workshop/parts/{id}
- ✓ PUT /v1/workshop/parts/{id}
- ✓ DELETE /v1/workshop/parts/{id}
- ✓ GET /v1/workshop/parts/summary
- ✓ POST /v1/workshop/parts/{id}/stock (receive)
- ✓ GET /v1/workshop/parts/{id}/stock (batches)
- ✓ POST /v1/workshop/parts/{id}/adjust
- ✓ GET /v1/workshop/parts/{id}/movements

### Jobs API
- ✓ GET /v1/workshop/jobs
- ✓ POST /v1/workshop/jobs
- ✓ GET /v1/workshop/jobs/{id}
- ✓ PUT /v1/workshop/jobs/{id}
- ✓ POST /v1/workshop/jobs/{id}/parts
- ✓ POST /v1/workshop/jobs/{id}/labour
- ✓ POST /v1/workshop/jobs/{id}/overhead
- ✓ PUT /v1/workshop/jobs/{id}/status

### Additional APIs Needed:
- GET /v1/workshop/markup-rules
- POST /v1/workshop/markup-rules
- PUT /v1/workshop/markup-rules/{id}
- DELETE /v1/workshop/markup-rules/{id}
- GET /v1/workshop/reports/job-profitability
- GET /v1/workshop/reports/inventory
- GET /v1/bicycles/{id}/repair-history

---

## 9. Accessibility (A11y) Requirements

- Semantic HTML (header, nav, main, article)
- ARIA labels for icon buttons
- Keyboard navigation (Tab, Enter, Esc)
- Focus management in modals
- Screen reader announcements for status changes
- Color contrast ratios (WCAG AA)
- Form labels and error messages
- Loading states with sr-only text

---

## 10. Performance Optimization

- Lazy load report charts
- Virtualize long tables (react-window)
- Debounce search inputs (300ms)
- Optimize images (Next.js Image component)
- Code splitting per route
- Memoize expensive calculations
- Use React.memo for list items
- Pagination for large datasets

---

## 11. Testing Strategy

### Unit Tests (Jest + React Testing Library)
- Form validation logic
- Cost calculation functions
- Badge color mapping
- Date formatting utilities

### Integration Tests
- Form submission flows
- Modal interactions
- Table filtering/sorting
- API calls (mocked)

### E2E Tests (Playwright)
- Create repair job end-to-end
- Add parts to job
- Complete job and verify bike cost update
- Stock receive flow
- Transfer stock between branches

---

## 12. Implementation Priority

### Phase 1: Core CRUD (Week 1)
1. ✅ Enhanced Header with Workshop dropdown
2. ✅ Workshop Dashboard page
3. ✅ Part Create/Edit forms
4. ✅ Stock Receive form
5. ✅ Basic Job Detail page

### Phase 2: Job Management (Week 2)
6. ✅ Repair Job Wizard
7. ✅ Add Parts to Job modal
8. ✅ Add Labour to Job modal
9. ✅ Job Status workflow
10. ✅ Complete Job modal with cost push to bike

### Phase 3: Stock Management (Week 3)
11. ✅ Stock Adjustment modal
12. ✅ Stock Transfer wizard
13. ✅ Part Detail page with batches
14. ✅ Movement history view

### Phase 4: Markup & Integration (Week 4)
15. ✅ Markup Rules CRUD
16. ✅ Bike Detail page repair history tab
17. ✅ Bike Profitability widget
18. ✅ Cost Summary enhancements

### Phase 5: Reports & Analytics (Week 5)
19. ✅ Job Profitability Report
20. ✅ Parts Inventory Report
21. ✅ Mechanic Performance Report
22. ✅ Bike Overhaul Cost Report

---

## 13. Design System Tokens

### Colors (Tailwind)
```css
/* Status */
--status-open: theme('colors.yellow.500');
--status-in-progress: theme('colors.blue.500');
--status-completed: theme('colors.green.500');
--status-invoiced: theme('colors.purple.500');
--status-cancelled: theme('colors.red.500');

/* Categories */
--category-engine: theme('colors.red.600');
--category-brake: theme('colors.orange.600');
--category-tyre: theme('colors.yellow.600');
--category-electrical: theme('colors.blue.600');
--category-suspension: theme('colors.indigo.600');
--category-transmission: theme('colors.purple.600');
--category-fluids: theme('colors.green.600');

/* Alerts */
--alert-low-stock: theme('colors.red.100');
--alert-warning: theme('colors.yellow.100');
```

### Typography
- Headings: `font-bold` (700)
- Subheadings: `font-semibold` (600)
- Body: `font-normal` (400)
- Labels: `font-medium` (500)
- Sizes: `text-3xl` (h1), `text-xl` (h2), `text-lg` (h3), `text-base` (body)

### Spacing
- Card padding: `p-6`
- Section gap: `gap-6`
- Form element gap: `gap-4`
- Table cell padding: `px-6 py-3`

---

## Summary

This plan covers:
- ✅ 13 new pages/routes
- ✅ 40+ new components
- ✅ 10 major user flows
- ✅ Complete CRUD for parts, jobs, markup rules
- ✅ Advanced features: stock batching (FIFO), transfers, reports
- ✅ Seamless bike integration with repair cost tracking
- ✅ Responsive design (mobile, tablet, desktop)
- ✅ Accessibility & performance best practices
- ✅ Clear implementation phases

Ready to start building! 🚀
