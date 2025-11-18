# Data Migration Guide

This directory contains templates and instructions for migrating historical bike data into the system.

## Overview

The bike lifecycle system provides three import scripts for migrating historical data:

1. **summery.xlsx Import** - Import cost summary data
2. **November Notebook Import** - Import procurement records
3. **BRC Cost Reconciliation** - Match repair costs with existing jobs

## Directory Structure

```
data/
├── templates/          # CSV templates for imports
│   ├── summery_template.csv
│   ├── notebook_template.csv
│   └── brc_template.csv
├── raw/               # Place your raw Excel files here (gitignored)
├── converted/         # Place converted CSV files here (gitignored)
└── README.md          # This file
```

## Step-by-Step Migration Process

### Step 1: Prepare Your Data

#### 1.1 Export summery.xlsx to CSV

1. Open `summery.xlsx` in Excel
2. Go to File → Save As
3. Choose "CSV (Comma delimited)" format
4. Save as `data/converted/summery.csv`

**Required columns**:
- `stock_number` - Stock number (e.g., MA/WW/ST/0001)
- `brand` - Bike brand (e.g., Honda)
- `model` - Bike model (e.g., CB 125F)
- `year` - Year (e.g., 2020)
- `company_id` - Company ID (MA or IN)
- `branch_id` - Branch ID (e.g., WW, HP, BRC)
- `status` - Current status (IN_STOCK, SOLD, etc.)
- `purchase_price` - Purchase price in LKR
- `repair_cost` - Total repair costs
- `branch_expenses` - Branch-level expenses
- `selling_price` - Selling price (if sold)
- `sale_date` - Sale date (if sold)
- `customer_name` - Customer name (if sold)
- `notes` - Additional notes

#### 1.2 Transcribe November Notebook to CSV

1. Create a new Excel file
2. Add columns as per `templates/notebook_template.csv`
3. Manually transcribe each entry from the physical notebook
4. Save as CSV: `data/converted/notebook.csv`

**Required columns**:
- `date` - Procurement date (YYYY-MM-DD)
- `company_id` - Company ID (MA or IN)
- `branch_id` - Branch ID
- `license_plate` - License plate number
- `brand` - Bike brand
- `model` - Bike model
- `year` - Year
- `purchase_price` - Purchase price in LKR
- `supplier_name` - Supplier name
- `supplier_contact` - Supplier phone
- `procured_by` - Staff member who purchased
- `payment_method` - CASH, BANK, etc.
- `invoice_number` - Invoice reference
- `notes` - Additional notes

#### 1.3 Export BRC Excel to CSV

1. Open the BRC cost tracking Excel file
2. Save as CSV: `data/converted/brc_costs.csv`

**Required columns**:
- `stock_number` - Stock number or leave blank
- `license_plate` - License plate (fallback identifier)
- `brand` - Brand name
- `model` - Model name
- `job_date` - Repair date
- `description` - Job description
- `parts_cost` - Parts cost
- `labor_cost` - Labor cost
- `total_cost` - Total cost
- `mechanic` - Mechanic name
- `job_status` - COMPLETED, PENDING, etc.
- `notes` - Additional notes

### Step 2: Test Import (Dry Run)

Always test your import first with `--dry-run` flag:

```bash
# Test summery import
python scripts/import_summery.py \
  --file data/converted/summery.csv \
  --dry-run \
  --verbose

# Test notebook import
python scripts/import_notebook.py \
  --file data/converted/notebook.csv \
  --company MA \
  --dry-run \
  --verbose

# Test BRC reconciliation
python scripts/reconcile_brc.py \
  --file data/converted/brc_costs.csv \
  --dry-run \
  --verbose
```

Review the output carefully:
- Check for errors
- Verify the number of records to be imported
- Look for warnings about missing data

### Step 3: Run Actual Import

Once dry run looks good, run the actual import:

```bash
# Import summery data
python scripts/import_summery.py \
  --file data/converted/summery.csv \
  --verbose

# Import notebook data
python scripts/import_notebook.py \
  --file data/converted/notebook.csv \
  --company MA \
  --verbose

# Reconcile BRC costs (create missing jobs)
python scripts/reconcile_brc.py \
  --file data/converted/brc_costs.csv \
  --create-missing \
  --verbose
```

### Step 4: Verify Imported Data

#### 4.1 Check via API

```bash
# Count bikes
curl http://localhost:8000/v1/bikes?limit=1 | jq '.total'

# Check recent bikes
curl http://localhost:8000/v1/bikes?limit=5 | jq '.data[] | {stock_number, brand, model}'

# Check sales
curl http://localhost:8000/v1/sales?limit=5 | jq '.data[] | {stock_number, selling_price}'
```

#### 4.2 Check via Database

```sql
-- Count bikes by status
SELECT status, COUNT(*) as count
FROM bicycles
WHERE business_model = 'SECOND_HAND_SALE'
GROUP BY status;

-- Check cost totals
SELECT
    COUNT(*) as total_bikes,
    SUM(base_purchase_price) as total_purchase,
    SUM(total_repair_cost) as total_repair,
    SUM(selling_price) as total_sales
FROM bicycles
WHERE business_model = 'SECOND_HAND_SALE';

-- Verify stock numbers
SELECT
    company_id,
    current_branch_id,
    COUNT(*) as count
FROM bicycles
WHERE current_stock_number IS NOT NULL
GROUP BY company_id, current_branch_id;
```

#### 4.3 Manual Verification

1. Pick 5-10 random records from original Excel
2. Look them up in the system by stock number
3. Verify all data matches (price, dates, costs, etc.)
4. Check calculations (total cost, profit/loss)

### Step 5: Handle Issues

#### If Import Fails

1. Check error messages in output
2. Fix data issues in CSV
3. Delete imported records if needed:
   ```sql
   DELETE FROM bicycles WHERE procurement_notes LIKE '%Imported from%';
   ```
4. Re-run import

#### Common Issues

**Issue**: Duplicate stock numbers
- **Solution**: Check for duplicates in CSV before import
  ```bash
  cut -d, -f1 summery.csv | sort | uniq -d
  ```

**Issue**: Invalid dates
- **Solution**: Ensure dates are in YYYY-MM-DD format or supported formats

**Issue**: Missing required fields
- **Solution**: Fill in missing data or use defaults

**Issue**: Cost discrepancies in BRC reconciliation
- **Solution**: Review discrepancy report in output, investigate differences

## Import Options

### Common Flags

- `--file FILE` - Path to CSV file (required)
- `--dry-run` - Test import without making changes
- `--verbose` - Show detailed logging
- `--help` - Show all available options

### Script-Specific Flags

**import_notebook.py**:
- `--company MA` - Set default company ID

**reconcile_brc.py**:
- `--create-missing` - Create repair jobs that don't exist

## Data Validation Rules

### Stock Numbers
- Format: `{COMPANY}/{BRANCH}/ST/{NUMBER}`
- Example: `MA/WW/ST/2066`
- Must be unique

### Dates
- Accepted formats: YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY
- If missing, uses current date

### Prices
- Must be positive numbers
- Decimals allowed
- Currency symbols (LKR, Rs.) are stripped automatically

### Status Values
- Valid: `IN_STOCK`, `SOLD`, `ALLOCATED`, `IN_TRANSIT`, `MAINTENANCE`, `WRITTEN_OFF`
- Default: `IN_STOCK`
- Auto-set to `SOLD` if selling_price exists

## Best Practices

1. **Backup First**: Always backup your database before import
   ```bash
   pg_dump -U postgres loan_manager > backup_$(date +%Y%m%d).sql
   ```

2. **Test on Sample**: Start with a small sample (5-10 rows) to verify

3. **Review Logs**: Save import logs for audit trail
   ```bash
   python scripts/import_summery.py --file data.csv --verbose 2>&1 | tee import.log
   ```

4. **Import Order**:
   - First: Notebook (procurement records)
   - Second: Summery (updates with costs)
   - Third: BRC (adds repair jobs)

5. **Verify After Each Step**: Don't proceed if errors occur

## Troubleshooting

### Script Won't Run

```bash
# Check Python path
which python3

# Install dependencies
pip install -r backend/requirements.txt

# Check database connection
psql postgresql://postgres@localhost:5432/loan_manager -c "SELECT 1"
```

### Import Hangs

- Check database connection
- Look for locks: `SELECT * FROM pg_locks WHERE granted = false;`
- Restart PostgreSQL if needed

### Data Doesn't Appear

- Check you're connected to correct database
- Verify no filters are applied in queries
- Check business_model field (should be SECOND_HAND_SALE)

## Getting Help

If you encounter issues:

1. Check error messages in terminal output
2. Review logs in `--verbose` mode
3. Verify CSV format against templates
4. Check database connection and permissions
5. Contact system administrator

## Post-Import Tasks

After successful import:

1. **Refresh Materialized Views**:
   ```bash
   python scripts/refresh_materialized_views.py --all
   ```

2. **Verify Reports**:
   - Check acquisition ledger
   - Verify cost summary totals
   - Review branch stock counts

3. **Update Stock Number Sequences**:
   - System will auto-continue from highest number
   - Verify next stock number is correct

4. **Archive Source Files**:
   - Move original Excel files to `data/raw/archive/`
   - Keep CSV files in `data/converted/` for reference

5. **Document Import**:
   - Note date of import
   - Record number of bikes imported
   - Save import logs

## Example Complete Workflow

```bash
# 1. Create backup
pg_dump -U postgres loan_manager > backup_$(date +%Y%m%d).sql

# 2. Prepare CSV files (manually)
# - Export summery.xlsx → data/converted/summery.csv
# - Transcribe notebook → data/converted/notebook.csv
# - Export BRC → data/converted/brc_costs.csv

# 3. Test imports
python scripts/import_notebook.py --file data/converted/notebook.csv --dry-run
python scripts/import_summery.py --file data/converted/summery.csv --dry-run
python scripts/reconcile_brc.py --file data/converted/brc_costs.csv --dry-run

# 4. Run actual imports
python scripts/import_notebook.py --file data/converted/notebook.csv --verbose 2>&1 | tee logs/notebook_import.log
python scripts/import_summery.py --file data/converted/summery.csv --verbose 2>&1 | tee logs/summery_import.log
python scripts/reconcile_brc.py --file data/converted/brc_costs.csv --create-missing --verbose 2>&1 | tee logs/brc_import.log

# 5. Verify
curl http://localhost:8000/v1/bikes?limit=1 | jq '.total'

# 6. Refresh views
python scripts/refresh_materialized_views.py --all

# 7. Archive files
mv data/raw/*.xlsx data/raw/archive/
```

---

**Note**: This is a one-time migration process. Once complete, all new data should be entered through the web interface or API.
