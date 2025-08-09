#!/usr/bin/env bash
set -euo pipefail

DB_URL=${DATABASE_URL:-"postgres://postgres:postgres@localhost:5432/loan_manager"}

echo "Running test data seed against: $DB_URL"
psql "$DB_URL" -f database/seed.sql





