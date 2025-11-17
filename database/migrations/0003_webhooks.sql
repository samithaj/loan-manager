-- 0003_webhooks.sql — Add webhook tables
-- Run with: psql "$DATABASE_URL" -f database/migrations/0003_webhooks.sql

create table if not exists webhooks (
  id text primary key,
  url text not null,
  secret text not null,
  active boolean not null default true,
  created_on timestamptz not null default now()
);

create table if not exists webhook_deliveries (
  id text primary key,
  webhook_id text not null references webhooks(id) on delete cascade,
  event_id text not null,
  event_type text not null,
  status text not null,
  attempt_count int not null default 0,
  last_attempt_at timestamptz,
  last_response_status int,
  last_error text
);

create index if not exists idx_webhook_deliveries_webhook_id on webhook_deliveries (webhook_id);
create index if not exists idx_webhook_deliveries_event_id on webhook_deliveries (event_id);
