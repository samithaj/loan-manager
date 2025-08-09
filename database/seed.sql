-- seed.sql — Basic seed data
-- Usage: psql "$DATABASE_URL" -f database/seed.sql

-- Offices
insert into offices (id, name) values ('HQ', 'Head Office') on conflict do nothing;

-- Staff
insert into staff (id, name, role) values ('STF-1', 'Admin', 'admin') on conflict do nothing;

-- Loan products
insert into loan_products (id, name, interest_rate, term_months, repayment_frequency)
values ('LP-STD', 'Standard Loan', 18.0, 12, 'MONTHLY') on conflict do nothing;

-- Delinquency buckets
insert into delinquency_buckets (id, name, min_days, max_days) values
  ('B0','Current',0,0),
  ('B1','1-30',1,30),
  ('B2','31-60',31,60),
  ('B3','61-90',61,90),
  ('B4','90+',91,9999)
on conflict do nothing;





