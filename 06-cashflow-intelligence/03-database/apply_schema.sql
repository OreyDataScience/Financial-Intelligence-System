-- Applies the Phase 06 database schema, all-or-nothing.
--
-- Run from anywhere with psql (paths below are relative to THIS file, via \ir):
--
--   psql -d <database> -f apply_schema.sql
--
-- PostgreSQL DDL is transactional: if any statement fails, nothing is created.
-- This script creates objects with plain CREATE (not IF NOT EXISTS) on purpose, so it fails
-- loudly instead of silently leaving an old, different definition in place.
-- Later changes belong in 06-migrations, not here.

\set ON_ERROR_STOP on

BEGIN;

\ir 01-schema/001_create_schema_processed.sql

-- Tables, in dependency order (business_profiles is the parent of everything else;
-- bank_transactions must exist before the ledgers that reference it).
\ir 02-tables/001_business_profiles.sql
\ir 02-tables/002_bank_transactions.sql
\ir 02-tables/003_invoices.sql
\ir 02-tables/004_supplier_bills.sql
\ir 02-tables/005_investigation_queue.sql
\ir 02-tables/006_duplicates_removed.sql
\ir 02-tables/007_profile_conflicts.sql
\ir 02-tables/008_data_quality_metrics.sql

COMMIT;
