-- ============================================================================
-- Seed Data: Chart of Accounts and Commission Rules
-- Version: 0012
-- Description: Seeds default chart of accounts and sample commission rules
-- ============================================================================

-- ============================================================================
-- 1. Chart of Accounts - Standard Business Accounts
-- ============================================================================

-- Clear existing data if needed (comment out for production)
-- DELETE FROM journal_entry_lines;
-- DELETE FROM journal_entries;
-- DELETE FROM chart_of_accounts;

-- ASSETS (1000-1999)
-- Current Assets (1000-1199)
INSERT INTO chart_of_accounts (id, account_code, account_name, description, category, account_type, normal_balance, level, is_header, is_system, created_by) VALUES
('coa-1000', '1000', 'Assets', 'Total Assets', 'ASSET', 'CURRENT_ASSET', 'DEBIT', 0, TRUE, TRUE, 'system'),
('coa-1100', '1100', 'Current Assets', 'Current Assets', 'ASSET', 'CURRENT_ASSET', 'DEBIT', 1, TRUE, TRUE, 'system'),
('coa-1110', '1110', 'Cash on Hand', 'Physical cash', 'ASSET', 'CASH', 'DEBIT', 2, FALSE, TRUE, 'system'),
('coa-1120', '1120', 'Cash in Bank - Operating', 'Main operating bank account', 'ASSET', 'BANK', 'DEBIT', 2, FALSE, TRUE, 'system'),
('coa-1121', '1121', 'Cash in Bank - Payroll', 'Payroll dedicated account', 'ASSET', 'BANK', 'DEBIT', 2, FALSE, FALSE, 'system'),
('coa-1130', '1130', 'Petty Cash', 'Petty cash float', 'ASSET', 'CASH', 'DEBIT', 2, FALSE, TRUE, 'system'),
('coa-1200', '1200', 'Accounts Receivable', 'Customer receivables', 'ASSET', 'ACCOUNTS_RECEIVABLE', 'DEBIT', 2, FALSE, TRUE, 'system'),
('coa-1210', '1210', 'Loan Receivables', 'Outstanding loans to customers', 'ASSET', 'ACCOUNTS_RECEIVABLE', 'DEBIT', 2, FALSE, TRUE, 'system'),
('coa-1300', '1300', 'Inventory', 'Vehicle inventory', 'ASSET', 'INVENTORY', 'DEBIT', 2, FALSE, TRUE, 'system')
ON CONFLICT (account_code) DO NOTHING;

-- Set parent relationships for current assets
UPDATE chart_of_accounts SET parent_account_id = 'coa-1000' WHERE id = 'coa-1100';
UPDATE chart_of_accounts SET parent_account_id = 'coa-1100' WHERE id IN ('coa-1110', 'coa-1120', 'coa-1121', 'coa-1130', 'coa-1200', 'coa-1210', 'coa-1300');

-- Fixed Assets (1500-1599)
INSERT INTO chart_of_accounts (id, account_code, account_name, description, category, account_type, normal_balance, parent_account_id, level, is_header, is_system, created_by) VALUES
('coa-1500', '1500', 'Fixed Assets', 'Fixed Assets', 'ASSET', 'FIXED_ASSET', 'DEBIT', 'coa-1000', 1, TRUE, TRUE, 'system'),
('coa-1510', '1510', 'Office Equipment', 'Computers, furniture, etc.', 'ASSET', 'FIXED_ASSET', 'DEBIT', 'coa-1500', 2, FALSE, FALSE, 'system'),
('coa-1520', '1520', 'Vehicles', 'Company vehicles', 'ASSET', 'FIXED_ASSET', 'DEBIT', 'coa-1500', 2, FALSE, FALSE, 'system'),
('coa-1590', '1590', 'Accumulated Depreciation', 'Accumulated depreciation on fixed assets', 'ASSET', 'FIXED_ASSET', 'CREDIT', 'coa-1500', 2, FALSE, TRUE, 'system')
ON CONFLICT (account_code) DO NOTHING;

-- LIABILITIES (2000-2999)
INSERT INTO chart_of_accounts (id, account_code, account_name, description, category, account_type, normal_balance, level, is_header, is_system, created_by) VALUES
('coa-2000', '2000', 'Liabilities', 'Total Liabilities', 'LIABILITY', 'CURRENT_LIABILITY', 'CREDIT', 0, TRUE, TRUE, 'system'),
('coa-2100', '2100', 'Current Liabilities', 'Current Liabilities', 'LIABILITY', 'CURRENT_LIABILITY', 'CREDIT', 1, TRUE, TRUE, 'system'),
('coa-2110', '2110', 'Accounts Payable', 'Supplier payables', 'LIABILITY', 'ACCOUNTS_PAYABLE', 'CREDIT', 2, FALSE, TRUE, 'system'),
('coa-2120', '2120', 'Accrued Expenses', 'Accrued liabilities', 'LIABILITY', 'CURRENT_LIABILITY', 'CREDIT', 2, FALSE, FALSE, 'system'),
('coa-2130', '2130', 'Salaries Payable', 'Unpaid salaries', 'LIABILITY', 'CURRENT_LIABILITY', 'CREDIT', 2, FALSE, TRUE, 'system'),
('coa-2140', '2140', 'Commissions Payable', 'Unpaid commissions', 'LIABILITY', 'CURRENT_LIABILITY', 'CREDIT', 2, FALSE, TRUE, 'system')
ON CONFLICT (account_code) DO NOTHING;

UPDATE chart_of_accounts SET parent_account_id = 'coa-2000' WHERE id = 'coa-2100';
UPDATE chart_of_accounts SET parent_account_id = 'coa-2100' WHERE id IN ('coa-2110', 'coa-2120', 'coa-2130', 'coa-2140');

-- Long-term Liabilities (2500-2599)
INSERT INTO chart_of_accounts (id, account_code, account_name, description, category, account_type, normal_balance, parent_account_id, level, is_header, is_system, created_by) VALUES
('coa-2500', '2500', 'Long-term Liabilities', 'Long-term debts', 'LIABILITY', 'LONG_TERM_LIABILITY', 'CREDIT', 'coa-2000', 1, TRUE, TRUE, 'system'),
('coa-2510', '2510', 'Bank Loans', 'Long-term bank loans', 'LIABILITY', 'LONG_TERM_LIABILITY', 'CREDIT', 'coa-2500', 2, FALSE, FALSE, 'system')
ON CONFLICT (account_code) DO NOTHING;

-- EQUITY (3000-3999)
INSERT INTO chart_of_accounts (id, account_code, account_name, description, category, account_type, normal_balance, level, is_header, is_system, created_by) VALUES
('coa-3000', '3000', 'Equity', 'Owner\'s Equity', 'EQUITY', 'EQUITY', 'CREDIT', 0, TRUE, TRUE, 'system'),
('coa-3100', '3100', 'Owner\'s Capital', 'Initial capital investment', 'EQUITY', 'EQUITY', 'CREDIT', 1, FALSE, TRUE, 'system'),
('coa-3200', '3200', 'Retained Earnings', 'Accumulated profits/losses', 'EQUITY', 'EQUITY', 'CREDIT', 1, FALSE, TRUE, 'system')
ON CONFLICT (account_code) DO NOTHING;

UPDATE chart_of_accounts SET parent_account_id = 'coa-3000' WHERE id IN ('coa-3100', 'coa-3200');

-- REVENUE (4000-4999)
INSERT INTO chart_of_accounts (id, account_code, account_name, description, category, account_type, normal_balance, level, is_header, is_system, created_by) VALUES
('coa-4000', '4000', 'Revenue', 'Total Revenue', 'REVENUE', 'OPERATING_REVENUE', 'CREDIT', 0, TRUE, TRUE, 'system'),
('coa-4100', '4100', 'Operating Revenue', 'Revenue from operations', 'REVENUE', 'OPERATING_REVENUE', 'CREDIT', 1, TRUE, TRUE, 'system'),
('coa-4110', '4110', 'Vehicle Sales Revenue', 'Revenue from vehicle sales', 'REVENUE', 'OPERATING_REVENUE', 'CREDIT', 2, FALSE, TRUE, 'system'),
('coa-4120', '4120', 'Loan Interest Income', 'Interest earned on loans', 'REVENUE', 'OPERATING_REVENUE', 'CREDIT', 2, FALSE, TRUE, 'system'),
('coa-4130', '4130', 'Service Revenue', 'Revenue from services', 'REVENUE', 'OPERATING_REVENUE', 'CREDIT', 2, FALSE, FALSE, 'system'),
('coa-4200', '4200', 'Other Revenue', 'Non-operating revenue', 'REVENUE', 'NON_OPERATING_REVENUE', 'CREDIT', 1, TRUE, FALSE, 'system'),
('coa-4210', '4210', 'Interest Income', 'Bank interest earned', 'REVENUE', 'NON_OPERATING_REVENUE', 'CREDIT', 2, FALSE, FALSE, 'system')
ON CONFLICT (account_code) DO NOTHING;

UPDATE chart_of_accounts SET parent_account_id = 'coa-4000' WHERE id IN ('coa-4100', 'coa-4200');
UPDATE chart_of_accounts SET parent_account_id = 'coa-4100' WHERE id IN ('coa-4110', 'coa-4120', 'coa-4130');
UPDATE chart_of_accounts SET parent_account_id = 'coa-4200' WHERE id = 'coa-4210';

-- EXPENSES (5000-5999)
INSERT INTO chart_of_accounts (id, account_code, account_name, description, category, account_type, normal_balance, level, is_header, is_system, created_by) VALUES
('coa-5000', '5000', 'Expenses', 'Total Expenses', 'EXPENSE', 'OPERATING_EXPENSE', 'DEBIT', 0, TRUE, TRUE, 'system'),
('coa-5100', '5100', 'Cost of Goods Sold', 'Direct costs', 'EXPENSE', 'COST_OF_GOODS_SOLD', 'DEBIT', 1, TRUE, TRUE, 'system'),
('coa-5110', '5110', 'Vehicle Purchase Cost', 'Cost of vehicles purchased', 'EXPENSE', 'COST_OF_GOODS_SOLD', 'DEBIT', 2, FALSE, TRUE, 'system'),
('coa-5200', '5200', 'Operating Expenses', 'Operating expenses', 'EXPENSE', 'OPERATING_EXPENSE', 'DEBIT', 1, TRUE, TRUE, 'system'),
('coa-5210', '5210', 'Salaries & Wages', 'Employee salaries', 'EXPENSE', 'OPERATING_EXPENSE', 'DEBIT', 2, FALSE, TRUE, 'system'),
('coa-5220', '5220', 'Commissions Expense', 'Sales commissions', 'EXPENSE', 'OPERATING_EXPENSE', 'DEBIT', 2, FALSE, TRUE, 'system'),
('coa-5230', '5230', 'Rent Expense', 'Office/showroom rent', 'EXPENSE', 'OPERATING_EXPENSE', 'DEBIT', 2, FALSE, FALSE, 'system'),
('coa-5240', '5240', 'Utilities Expense', 'Electricity, water, etc.', 'EXPENSE', 'OPERATING_EXPENSE', 'DEBIT', 2, FALSE, FALSE, 'system'),
('coa-5250', '5250', 'Marketing & Advertising', 'Marketing expenses', 'EXPENSE', 'OPERATING_EXPENSE', 'DEBIT', 2, FALSE, FALSE, 'system'),
('coa-5260', '5260', 'Repairs & Maintenance', 'Vehicle repairs and maintenance', 'EXPENSE', 'OPERATING_EXPENSE', 'DEBIT', 2, FALSE, FALSE, 'system'),
('coa-5270', '5270', 'Fuel Expense', 'Fuel for company vehicles', 'EXPENSE', 'OPERATING_EXPENSE', 'DEBIT', 2, FALSE, FALSE, 'system'),
('coa-5280', '5280', 'Office Supplies', 'Stationery and supplies', 'EXPENSE', 'OPERATING_EXPENSE', 'DEBIT', 2, FALSE, FALSE, 'system'),
('coa-5290', '5290', 'Depreciation Expense', 'Depreciation on fixed assets', 'EXPENSE', 'OPERATING_EXPENSE', 'DEBIT', 2, FALSE, TRUE, 'system'),
('coa-5300', '5300', 'Petty Cash Expenses', 'Miscellaneous petty cash expenses', 'EXPENSE', 'OPERATING_EXPENSE', 'DEBIT', 2, FALSE, TRUE, 'system')
ON CONFLICT (account_code) DO NOTHING;

UPDATE chart_of_accounts SET parent_account_id = 'coa-5000' WHERE id IN ('coa-5100', 'coa-5200');
UPDATE chart_of_accounts SET parent_account_id = 'coa-5100' WHERE id = 'coa-5110';
UPDATE chart_of_accounts SET parent_account_id = 'coa-5200' WHERE id IN ('coa-5210', 'coa-5220', 'coa-5230', 'coa-5240', 'coa-5250', 'coa-5260', 'coa-5270', 'coa-5280', 'coa-5290', 'coa-5300');

-- ============================================================================
-- 2. Default Commission Rules
-- ============================================================================

-- Vehicle Sale Commission Rules
INSERT INTO commission_rules (id, rule_name, commission_type, description, formula_type, rate, applicable_roles, effective_from, is_active, priority, created_by) VALUES
('comm-rule-001', 'Basic Vehicle Sale - Sales Agent', 'VEHICLE_SALE', 'Standard commission for sales agents on vehicle sales', 'PERCENTAGE_OF_PROFIT', 5.00, '["SALES_AGENT"]'::jsonb, '2024-01-01', TRUE, 10, 'system'),
('comm-rule-002', 'Basic Vehicle Sale - Branch Manager', 'VEHICLE_SALE', 'Override commission for branch managers on vehicle sales', 'PERCENTAGE_OF_PROFIT', 2.00, '["BRANCH_MANAGER"]'::jsonb, '2024-01-01', TRUE, 5, 'system')
ON CONFLICT DO NOTHING;

-- Tiered Vehicle Sale Commission (for high performers)
INSERT INTO commission_rules (id, rule_name, commission_type, description, formula_type, tier_basis, tier_configuration, applicable_roles, effective_from, is_active, priority, created_by) VALUES
('comm-rule-003', 'Tiered Vehicle Sale - Senior Agent', 'VEHICLE_SALE', 'Tiered commission based on sale amount for senior agents', 'TIERED', 'SALE_AMOUNT',
'{"tiers": [
    {"min": 0, "max": 500000, "rate": 3.0},
    {"min": 500000, "max": 1000000, "rate": 4.0},
    {"min": 1000000, "max": null, "rate": 5.0}
]}'::jsonb,
'["SALES_AGENT", "BRANCH_MANAGER"]'::jsonb, '2024-01-01', FALSE, 15, 'system')
ON CONFLICT DO NOTHING;

-- Loan Origination Commission
INSERT INTO commission_rules (id, rule_name, commission_type, description, formula_type, rate, applicable_roles, effective_from, is_active, priority, created_by) VALUES
('comm-rule-004', 'Loan Origination Fee', 'LOAN_ORIGINATION', 'Commission on loan origination', 'PERCENTAGE_OF_SALE', 1.00, '["LOAN_MANAGEMENT_OFFICER"]'::jsonb, '2024-01-01', TRUE, 10, 'system')
ON CONFLICT DO NOTHING;

-- Insurance Sale Commission
INSERT INTO commission_rules (id, rule_name, commission_type, description, formula_type, rate, applicable_roles, effective_from, is_active, priority, created_by) VALUES
('comm-rule-005', 'Insurance Sale', 'INSURANCE_SALE', 'Commission on insurance policy sales', 'FLAT_RATE', 5000.00, '["SALES_AGENT"]'::jsonb, '2024-01-01', TRUE, 10, 'system')
ON CONFLICT DO NOTHING;

-- Service Commission
INSERT INTO commission_rules (id, rule_name, commission_type, description, formula_type, rate, min_amount, max_amount, applicable_roles, effective_from, is_active, priority, created_by) VALUES
('comm-rule-006', 'Service Revenue Share', 'SERVICE', 'Commission on service revenue', 'PERCENTAGE_OF_SALE', 10.00, 1000.00, 50000.00, '["SALES_AGENT"]'::jsonb, '2024-01-01', TRUE, 10, 'system')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- Seed Data Complete
-- ============================================================================

-- Summary of seeded data
DO $$
DECLARE
    account_count INTEGER;
    rule_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO account_count FROM chart_of_accounts WHERE is_system = TRUE;
    SELECT COUNT(*) INTO rule_count FROM commission_rules;

    RAISE NOTICE 'Seed data complete:';
    RAISE NOTICE '  - Chart of Accounts: % accounts created', account_count;
    RAISE NOTICE '  - Commission Rules: % rules created', rule_count;
END $$;
