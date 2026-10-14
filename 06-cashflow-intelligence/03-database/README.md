# 03-database

PostgreSQL schema for Phase 06. This stage turns `01-data/03-processed` into typed, constrained tables that every analytics stage can read.

**Status:** schema and tables designed and tested. Tested on PostgreSQL 16 by applying the schema, loading all eight processed CSVs (21,037 rows) and trying to corrupt the result on purpose. A loader, indexes and views come next (see the end of this file).

## Files

| Path | What it is |
|---|---|
| `apply_schema.sql` | Applies everything below in one transaction (all or nothing) |
| `01-schema/001_create_schema_processed.sql` | Creates the `processed` schema |
| `02-tables/001_business_profiles.sql` … `008_data_quality_metrics.sql` | One file per table, in dependency order |

## Apply it

```powershell
psql "postgresql://USER@HOST:5432/DBNAME" -f .\03-database\apply_schema.sql
```

`apply_schema.sql` uses psql's `\ir`, so it needs the `psql` command line tool. In pgAdmin or DBeaver, run the schema file and then the table files in numeric order instead. It creates objects with plain `CREATE`, so running it twice fails with "already exists" rather than silently keeping an old definition. To start over in development only: `DROP SCHEMA processed CASCADE;`. Later changes belong in `06-migrations`.

## The design decisions

### Layout

| Decision | Choice | Why |
|---|---|---|
| Schema | `processed` | One schema per pipeline layer. Later phases add `analytics`, `forecasts`, `scenarios` and `risk` in their own migrations, keeping each stage's output apart from the data it reads |
| Table / column names | Identical to the CSV files, in CSV column order | Loading is a plain `\copy`, and the raw-versus-standardized naming (`transaction_date` vs `transaction_date_std`) stays consistent with every README |
| Tables | 8 (120 columns, 71 named constraints) | One per processed CSV that the platform consumes |

### Types, chosen from the profiled data

| Kind of value | PostgreSQL type | Reason |
|---|---|---|
| Money (amounts, balances) | `NUMERIC(18,2)` | Exact to the cent. Never floating point |
| Values kept exactly as received (`transaction_date`, `due_date`, `annual_revenue`, `invoice_status`, descriptions) | `TEXT` | Raw means raw. Mixed date formats and `'R 3,500,000'` are preserved, not interpreted |
| Standardized dates (`*_std`), `business_start_date` | `DATE` | Real dates for analysis. No time component exists in the data |
| Flags | `BOOLEAN NOT NULL` | A flag is never unknown |
| Counts and days | `INTEGER` | |
| Metric values | `NUMERIC(18,4)` | Rates need four decimals |
| Categories (statuses, reasons) | `TEXT` + `CHECK` | Easier to extend than `ENUM` types, which are awkward to alter. The `CHECK` still rejects anything unrecognised |
| Currency | `TEXT` + `CHECK (~ '^[A-Z]{3}$')` | ZAR expected; anything else is allowed but must be a valid code and handled explicitly |

### Identifiers

- **Natural keys, no surrogate IDs.** `source_record_id` (for example `BT_0000123`, `INV_000045`) is assigned by our own import step, is stable, and is exactly what links a processed row back to staging and raw. It is the primary key on each data table. An extra generated number would add a second ID with no benefit.
- **`business_id` is the parent key.** `business_profiles` has one row per business, and every other table references it. A row for an unknown business cannot exist.
- **Ledger to bank is a real foreign key** (`matched_bank_source_record_id`), and unique, so one bank transaction cannot be claimed by two invoices.
- **Bank to ledger is polymorphic** (`matched_ledger_type` + `matched_ledger_source_record_id` point at either an invoice or a bill), so it cannot be a foreign key. It is kept consistent by constraints instead. The same applies to `investigation_queue`, which points at any table via `(dataset, source_record_id)`.

### Missing, zero, unknown and not applicable

This is the specification's rule, now enforced by the database.

| Meaning | In the database |
|---|---|
| **Missing** (should exist, was not supplied) | `NULL`, with the matching `missing_*` flag kept consistent by a `CHECK` |
| **Zero** | `0`. `amount_paid` is `NOT NULL`, so an unpaid invoice is 0 and nothing is ever "unknown" by accident |
| **Unknown / unresolved** | `reconciliation_status = 'needs_investigation'` with a reason |
| **Not applicable** | `reconciliation_status = 'not_applicable'` (nothing to reconcile yet), or `NULL` on a column that does not apply |
| **Never an empty string** | Every nullable text column carries a "no blank strings" `CHECK`. `NULL` is the only way to say "absent" |

### What the constraints do, and don't, enforce

**They enforce structure and the pipeline's own contracts:**
- keys and references
- vocabularies for statuses and reasons
- `net_amount = credit - debit`
- no duplicates in the analysis layer
- reconciliation fields that agree with each other, for example a bank link exists only when the reason says one does, and `matched` implies a link
- `NULL`/flag pairs that agree

**They deliberately do not reject business anomalies.** A payment dated before its invoice, a late posting, or a possible sign error is real-world data to flag and route to review, not an error to refuse. That is the specification's rule that unusual is not wrong.

If a new status or reason appears that the pipeline does not know about, the load fails loudly. That is intended: the vocabulary gets extended on purpose, never absorbed silently.

### Deliberately left out

- **`reconciliation-evaluation.csv`** (and the raw issues log) are **not loaded**. They measure the pipeline against synthetic ground truth and will not exist with real data. Production tables must never depend on them. If wanted for development, they belong in a separate schema.
- **Raw and staging layers** are not in the database yet. The pipeline reads and writes CSVs for those, and only `processed` is the platform's source.

## How it was tested

On PostgreSQL 16.15, with your actual processed data:

1. **Applied** the schema from an unrelated folder; a second run failed loudly with nothing half-created.
2. **Loaded** all eight CSVs in dependency order; every row count matched its CSV (21,037 rows).
3. **Checked fidelity:** sums of net amounts, credits, balances, invoice amounts and amount differences match pandas to the cent. `NULL` counts match CSV blanks exactly, and there are no empty strings.
4. **Tried to break it:** 19 deliberate corruptions (blank strings, a reintroduced duplicate, a wrong `net_amount`, orphaned and double-claimed bank rows, hidden profile conflicts, deleting a parent) were each rejected by a named constraint, and the data was unchanged afterwards.

## Found while inspecting the data (and what changed)

Profiling every column before choosing types turned up three things:

1. **`amount_difference` carried floating-point noise** (`1114.3100000000013`). **Fixed** in `reconcile_and_process.py`; it is now rounded to cents.
2. **`balance_after_transaction` was not a real running balance.** Only about a quarter of rows followed the previous balance plus the transaction. A real bank statement is always coherent, and this would have misled the cash-position work. **Fixed** in `generate_raw_data.py`: balances are now recomputed chronologically from each business's opening balance. All issue counts and evaluation results are unchanged.
3. **The synthetic businesses are not economically calibrated** to their own profiles. **Not fixed yet**; see the limitation in `01-data/DATA_SPECIFICATION.md` §10. It does not affect this schema, but it must be fixed before burn rate, runway and forecasting mean anything.

After pulling these changes, rebuild the data once: `python .\02-data-engineering\06-pipeline-tasks\run_phase06_data_pipeline.py --regenerate`

## Next

| Folder | What | Why |
|---|---|---|
| `05-indexes` | Indexes on foreign-key columns and the common filters (`business_id` + date, reconciliation status) | Primary and unique keys are indexed automatically; foreign-key columns are not |
| `06-migrations` | Versioned changes from here on | `apply_schema.sql` is the starting point only |
| load step | A script that applies the schema, loads the CSVs in this order and reloads cleanly | The `processed` schema is reloaded as a whole, never edited in place |
| `03-views` | Analysis-friendly views, for example reconciled invoices only, or cash position by day | Gives `05-cashflow-intelligence` a stable interface |
| `13-authentication-security` | Roles and grants | None yet |
| queue workflow | Owner and resolution columns on `investigation_queue` | The queue is currently a read-only report |
