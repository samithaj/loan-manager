# Migration 0012: Customer KYC, Commissions & Accounting Modules

## Overview

This migration adds comprehensive Customer KYC, Commission calculation, and Accounting functionality to the loan management system.

## What's Included

### Tables Created (9 tables)

**Customer KYC (3 tables):**
1. `customer_guarantors` - Guarantor information for loan applications
2. `customer_employment` - Employment history and income verification
3. `customer_bank_accounts` - Customer banking information

**Commissions (1 table):**
4. `commission_rules` - Commission calculation rules with flexible formulas

**Accounting (5 tables):**
5. `chart_of_accounts` - Hierarchical chart of accounts
6. `journal_entries` - Double-entry bookkeeping journal entries
7. `journal_entry_lines` - Journal entry line items
8. `petty_cash_floats` - Petty cash float management
9. `petty_cash_vouchers` - Petty cash disbursement/receipt vouchers

### Enums Created (13 enums)

- `employment_type_enum` - Employment types (PERMANENT, CONTRACT, etc.)
- `income_frequency_enum` - Income frequency (DAILY, WEEKLY, MONTHLY, ANNUAL)
- `bank_account_type_enum` - Bank account types
- `bank_account_status_enum` - Account status
- `commission_type_enum` - Commission types
- `formula_type_enum` - Commission formula types
- `tier_basis_enum` - Tiered commission basis
- `account_category_enum` - Account categories (ASSET, LIABILITY, etc.)
- `chart_account_type_enum` - Specific account types
- `journal_entry_type_enum` - Journal entry types
- `journal_entry_status_enum` - Entry status (DRAFT, POSTED, VOID)
- `voucher_type_enum` - Voucher types (RECEIPT, DISBURSEMENT)
- `voucher_status_enum` - Voucher status

### Indexes Created

Performance indexes on:
- Foreign keys
- Lookup fields (NIC, account codes, entry numbers)
- Filter fields (status, dates, types)
- JSONB fields (applicable_roles in commission_rules)

### Triggers Created

- `updated_at` auto-update triggers on all 9 tables

## Running the Migration

### Full Database Setup (from scratch)

```bash
export DATABASE_URL=postgresql://user:password@localhost:5432/loan_manager
make db
```

This will run all migrations including 0012.

### Run Migration 0012 Only

```bash
export DATABASE_URL=postgresql://user:password@localhost:5432/loan_manager
psql "$DATABASE_URL" -f database/migrations/0012_customer_kyc_commissions_accounting.sql
```

### Run Seed Data

```bash
psql "$DATABASE_URL" -f database/seeds/0012_seed_accounting_data.sql
```

This seeds:
- **Chart of Accounts**: 40+ standard business accounts (assets, liabilities, equity, revenue, expenses)
- **Commission Rules**: 6 default commission rules for various scenarios

## Rollback

To rollback this migration:

```sql
-- Drop tables (order matters due to foreign keys)
DROP TABLE IF EXISTS journal_entry_lines CASCADE;
DROP TABLE IF EXISTS journal_entries CASCADE;
DROP TABLE IF EXISTS petty_cash_vouchers CASCADE;
DROP TABLE IF EXISTS petty_cash_floats CASCADE;
DROP TABLE IF EXISTS chart_of_accounts CASCADE;
DROP TABLE IF EXISTS commission_rules CASCADE;
DROP TABLE IF EXISTS customer_bank_accounts CASCADE;
DROP TABLE IF EXISTS customer_employment CASCADE;
DROP TABLE IF EXISTS customer_guarantors CASCADE;

-- Drop enums
DROP TYPE IF EXISTS employment_type_enum CASCADE;
DROP TYPE IF EXISTS income_frequency_enum CASCADE;
DROP TYPE IF EXISTS bank_account_type_enum CASCADE;
DROP TYPE IF EXISTS bank_account_status_enum CASCADE;
DROP TYPE IF EXISTS commission_type_enum CASCADE;
DROP TYPE IF EXISTS formula_type_enum CASCADE;
DROP TYPE IF EXISTS tier_basis_enum CASCADE;
DROP TYPE IF EXISTS account_category_enum CASCADE;
DROP TYPE IF EXISTS chart_account_type_enum CASCADE;
DROP TYPE IF EXISTS journal_entry_type_enum CASCADE;
DROP TYPE IF EXISTS journal_entry_status_enum CASCADE;
DROP TYPE IF EXISTS voucher_type_enum CASCADE;
DROP TYPE IF EXISTS voucher_status_enum CASCADE;
```

## Verification

After running the migration, verify with:

```sql
-- Check tables exist
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN (
    'customer_guarantors',
    'customer_employment',
    'customer_bank_accounts',
    'commission_rules',
    'chart_of_accounts',
    'journal_entries',
    'journal_entry_lines',
    'petty_cash_floats',
    'petty_cash_vouchers'
);

-- Check seeded data
SELECT COUNT(*) as chart_accounts FROM chart_of_accounts;
SELECT COUNT(*) as commission_rules FROM commission_rules;
```

Expected results:
- 9 tables created
- 40+ chart of accounts
- 6 commission rules

## Key Features

### Customer KYC
- **Guarantor Management**: Full KYC for loan guarantors with verification workflow
- **Employment Tracking**: Income normalization across different frequencies
- **Bank Accounts**: Primary account management with verification

### Commissions
- **Flexible Formulas**: FLAT_RATE, PERCENTAGE_OF_SALE, PERCENTAGE_OF_PROFIT, TIERED
- **Smart Matching**: Rule matching based on role, branch, vehicle condition, dates
- **Tiered Calculations**: JSON-based tier configuration for complex commission structures

### Accounting
- **Chart of Accounts**: Hierarchical structure with parent/child relationships
- **Double-Entry**: Enforced balanced entries (debits = credits)
- **Journal Entries**: Post/void workflow with audit trail
- **Petty Cash**: Float tracking with voucher approval workflow
- **Integration**: Vouchers auto-create journal entries when posted

## Dependencies

Requires:
- PostgreSQL 12+
- `clients` table (for customer foreign keys)

## Notes

- All tables use VARCHAR(36) for UUIDs
- Timestamps use `CURRENT_TIMESTAMP` defaults
- `is_system` flag protects critical chart of accounts from deletion
- JSONB fields used for flexible data (commission tiers, applicable roles)
- Check constraints enforce data integrity (balanced entries, debit XOR credit)
