-- 0001_init.sql — Initial schema derived from BUSINESS_REQUIREMENTS.md (loans subset)
-- Run with: psql "$DATABASE_URL" -f database/migrations/0001_init.sql

-- Users (for Basic auth + roles)
create table if not exists users (
  id uuid primary key,
  username text not null unique,
  password_hash text not null,
  roles_csv text not null default 'user',
  created_at timestamptz not null default now()
);

-- Organization & reference
create table if not exists offices (
  id text primary key,
  name text not null
);

create table if not exists staff (
  id text primary key,
  name text not null,
  role text not null
);

create table if not exists holidays (
  id text primary key,
  name text not null,
  date date not null
);

-- Clients
create table if not exists clients (
  id text primary key,
  display_name text not null,
  mobile text,
  national_id text,
  address text,
  created_on timestamptz not null default now()
);

-- Loan products
create table if not exists loan_products (
  id text primary key,
  name text not null,
  interest_rate numeric not null,
  term_months int not null,
  repayment_frequency text not null
);

-- Loans
create table if not exists loans (
  id text primary key,
  client_id text not null references clients(id),
  product_id text not null references loan_products(id),
  principal numeric not null,
  interest_rate numeric,
  term_months int not null,
  status text not null,
  disbursed_on date,
  created_on timestamptz not null default now()
);

-- Transactions
create table if not exists loan_transactions (
  id text primary key,
  loan_id text not null references loans(id),
  type text not null,
  amount numeric not null,
  date date not null,
  receipt_number text not null,
  posted_by text
);

-- Charges
create table if not exists loan_charges (
  id text primary key,
  loan_id text not null references loans(id),
  name text not null,
  amount numeric not null,
  due_date date,
  status text not null
);

-- Collateral
create table if not exists collaterals (
  id text primary key,
  loan_id text references loans(id),
  type text not null,
  value numeric not null,
  details jsonb
);

-- Vehicle inventory
create table if not exists vehicle_inventory (
  id text primary key,
  vin_or_frame_number text,
  brand text not null,
  model text not null,
  plate text,
  color text,
  purchase_price numeric,
  msrp numeric,
  status text not null,
  linked_loan_id text references loans(id)
);

-- Documents
create table if not exists documents (
  id text primary key,
  owner_type text not null,
  owner_id text not null,
  name text not null,
  mime_type text not null,
  size int not null,
  uploaded_on timestamptz not null default now()
);

-- Delinquency
create table if not exists delinquency_buckets (
  id text primary key,
  name text not null,
  min_days int not null,
  max_days int not null
);

create table if not exists delinquency_status (
  loan_id text primary key references loans(id),
  current_bucket_id text not null references delinquency_buckets(id),
  days_past_due int not null,
  as_of_date date not null
);

-- Jobs for async processing
create table if not exists jobs (
  id text primary key,
  type text not null,
  status text not null,
  created_on timestamptz not null default now(),
  started_on timestamptz,
  completed_on timestamptz,
  total_records int,
  processed_records int,
  success_count int,
  error_count int,
  error_details text,
  result_data text
);

-- Webhooks
create table if not exists webhook_endpoints (
  id text primary key,
  url text not null,
  secret text not null,
  events text not null,
  active boolean not null default true,
  created_on timestamptz not null default now()
);

create table if not exists webhook_deliveries (
  id text primary key,
  endpoint_id text not null references webhook_endpoints(id),
  event_type text not null,
  payload text not null,
  status text not null,
  attempts int not null default 0,
  last_attempt timestamptz,
  next_attempt timestamptz,
  response_status int,
  response_body text,
  created_on timestamptz not null default now()
);

-- Helpful indexes
create index if not exists idx_clients_display_name on clients (display_name);
create index if not exists idx_loans_client on loans (client_id);
create index if not exists idx_txn_loan on loan_transactions (loan_id);
create index if not exists idx_jobs_type_status on jobs (type, status);
create index if not exists idx_webhook_deliveries_endpoint on webhook_deliveries (endpoint_id);
create index if not exists idx_webhook_deliveries_status on webhook_deliveries (status);





