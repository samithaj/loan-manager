-- 0002_idempotency.sql — Add idempotency records table
-- Run with: psql "$DATABASE_URL" -f database/migrations/0002_idempotency.sql

create table if not exists idempotency_records (
  idempotency_key text primary key,
  request_path text not null,
  response_status int not null,
  response_body text not null,
  created_at timestamptz not null default now()
);

-- Index for cleanup of old records (24h TTL)
create index if not exists idx_idempotency_created_at on idempotency_records (created_at);
