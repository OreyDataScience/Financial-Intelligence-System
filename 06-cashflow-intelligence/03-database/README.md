# 03-database

PostgreSQL database layer for Phase 06 — Cashflow Intelligence.

This stage transforms the processed outputs from `01-data/03-processed` into typed, constrained relational tables. PostgreSQL is the **primary source of processed financial data for all downstream analytics**. R, Python, forecasting models, scenario analysis, risk calculations and client reporting should read from the database rather than independently loading processed CSV files.

**Status:** Initial schema implemented, all eight tables loaded, and initial structural and relationship integrity checks passed on PostgreSQL 18.6. The database contains 21,037 records across operational and audit tables. A repeatable loader, performance indexes, analytical views and application access are the next priorities.

## Files

| Path | What it is |
|---|---|
| `apply_schema.sql` | Applies the initial schema and all eight table definitions in one transaction |
| `01-schema/001_create_schema_processed.sql` | Creates the `processed` schema |
| `02-tables/001_business_profiles.sql` … `008_data_quality_metrics.sql` | One SQL file per table, applied in dependency order |

## Architecture and source of truth

PostgreSQL is the authoritative, queryable source for processed financial data used by Phase 06 analytics.

The current architecture separates the pipeline from the database-backed analytics layer:

1. **Raw data:** Original synthetic source files are retained in `01-data/01-raw`.
2. **Staging:** Standardization, validation flags and intermediate data preparation occur through the existing pipeline.
3. **Processing:** Scripts in `02-data-engineering` clean, deduplicate, reconcile and evaluate the source records.
4. **Database:** The processed outputs are loaded into PostgreSQL's `processed` schema.
5. **Analytics and reporting:** Downstream R and Python components query PostgreSQL to calculate cash-flow metrics, receivables, supplier obligations, forecasts, scenarios, risk indicators and client reports.

The processed CSV files remain important reproducible pipeline artefacts and audit references. They are not intended to become competing sources of truth for downstream analytics.

Raw and staging data remain CSV-based for now. Moving those layers into PostgreSQL is a separate architectural decision and is not required before the analytics layer adopts PostgreSQL as its primary source.

### Current environment

| Setting | Value |
|---|---|
| Database system | PostgreSQL 18.6 |
| Development database | `orey_cashflow_dev` |
| Processed schema | `processed` |
| Database host | `localhost` |
| Default port | `5432` |
| SQL client | `psql` |
| Initial table count | 8 |

The development database is local to the current machine. Production deployment, credentials, access roles, backups and operational monitoring still need to be configured.

## Apply the schema

From the repository root, run:

```powershell
psql -h localhost -p 5432 -U postgres -d orey_cashflow_dev -W -f .\06-cashflow-intelligence\03-database\apply_schema.sql
```

Adjust the relative path if your working directory is already `06-cashflow-intelligence`.

Alternatively, when working from the Phase 06 directory:

```powershell
psql -h localhost -p 5432 -U postgres -d orey_cashflow_dev -W -f .\03-database\apply_schema.sql
```

`apply_schema.sql` uses psql's `\ir` command, so it must be executed through `psql`. If using pgAdmin or DBeaver, execute the schema file and individual table files in dependency order instead.

The initial schema uses plain `CREATE` statements. Running it against an existing schema will fail rather than silently replacing existing definitions.

**Important:** `apply_schema.sql` creates the initial schema and tables; it does not provide a complete repeatable data-loading workflow. The next database-engineering step is to implement a controlled loader that can validate and refresh the processed data safely.

Do not drop the `processed` schema simply to rerun the setup unless you explicitly intend to reset the development database and understand the consequences. Future structural changes should use versioned migrations.

## The design decisions

### Layout

| Decision | Choice | Why |
|---|---|---|
| Schema | `processed` | Holds deduplicated, standardized and reconciled records used by downstream analytics |
| Table and column names | Consistent with processed CSVs and their column order | Simplifies loading, traceability and comparison with pipeline outputs |
| Tables | 8 | Separates business profiles, bank transactions, invoices, supplier bills and supporting audit records |
| Database role | Primary analytics source | Provides a consistent interface for R, Python, forecasts, scenarios and reporting |
| Data refresh | Controlled whole-layer refresh planned | Prevents partial or inconsistent processed datasets from reaching analytics |

Future schemas such as `analytics`, `forecasts`, `scenarios` and `risk` may be introduced through deliberate migrations when their responsibilities and interfaces are defined.

### Types, chosen from the profiled data

| Kind of value | PostgreSQL type | Reason |
|---|---|---|
| Money, amounts and balances | `NUMERIC(18,2)` | Exact decimal arithmetic to the cent; avoids binary floating-point rounding |
| Values retained as received, including mixed-format dates and descriptions | `TEXT` | Preserves source representations for traceability |
| Standardized dates | `DATE` | Supports chronological filtering and aggregation without introducing an unnecessary time component |
| Flags | `BOOLEAN NOT NULL` | Explicit true/false states for required quality and processing flags |
| Counts and elapsed days | `INTEGER` | Appropriate for discrete quantities |
| Data-quality metric values | `NUMERIC(18,4)` | Supports rates and metrics requiring four decimal places |
| Categories, statuses and reasons | `TEXT` with `CHECK` constraints | Allows controlled vocabulary extensions through deliberate schema changes |
| Currency | `TEXT` with a format constraint | Requires a valid three-letter uppercase currency code |

The standardized schema retains both original and standardized representations where required. For example, `transaction_date` preserves the source value while `transaction_date_std` provides a date suitable for analysis.

### Identifiers and relationships

- **Natural keys:** `source_record_id` is the stable identifier assigned by the pipeline for a source record. It connects processed records to their corresponding source and staging records.
- **Business key:** `business_id` identifies the business. `business_profiles` contains the parent business records, and the relevant financial and audit tables reference those businesses.
- **Ledger-to-bank references:** Invoice and supplier-bill records can reference a matched bank transaction through `matched_bank_source_record_id`.
- **Bank-to-ledger references:** `matched_ledger_type` and `matched_ledger_source_record_id` identify an invoice or supplier bill. This is a polymorphic relationship, so a conventional foreign key cannot enforce the complete relationship by itself.
- **Audit references:** Investigation records and duplicate-removal records retain the source identifiers and dataset names needed to trace issues back to their originating records.

The current database constraints enforce the defined foreign keys and uniqueness rules. Cross-table polymorphic consistency must also be checked through validation queries and, where appropriate, application or database logic.

### Missing, zero, unknown and not applicable

These states must remain distinct throughout data engineering and analytics.

| Meaning | Representation |
|---|---|
| Missing | `NULL`, with the associated missing-data flag where defined |
| Zero | Numeric `0`, representing a known zero value |
| Unknown or unresolved | An explicit status or investigation reason where applicable |
| Not applicable | An explicit `not_applicable` reconciliation status where appropriate, or `NULL` for a field that genuinely does not apply |
| Absent text | `NULL`, rather than an empty string |

A zero is not a substitute for missing information. Similarly, an invoice marked as paid does not, by itself, establish that a corresponding bank cash movement has been confirmed.

Downstream cash-flow calculations must respect reconciliation statuses, match confidence, reversals and unresolved exceptions. Uncertain records must not silently be treated as confirmed cash movements.

### What the constraints enforce

The schema enforces structural rules and the contracts defined by the processing pipeline, including:

- Primary keys, foreign keys and uniqueness rules.
- Approved status and reason vocabularies.
- The relationship `net_amount = credit_amount - debit_amount`, with the appropriate handling of nullable amounts.
- Consistency between missing-data flags and nullable fields.
- Reconciliation fields that must agree with each other.
- Prevention of duplicate records in the processed analysis tables.
- Valid formats and nonblank values for constrained fields.

The constraints deliberately do not reject every unusual business event. A payment dated before an invoice, a delayed posting or a possible sign inconsistency is a condition to investigate, not automatically a reason to discard the record.

When the pipeline introduces a new status or reason, the corresponding database contract must be reviewed and updated deliberately.

## Current tables and verified record counts

All eight tables have been created and populated in the development database.

| Table | Records | Purpose |
|---|---:|---|
| `processed.business_profiles` | 5 | Business-level profile information |
| `processed.bank_transactions` | 19,673 | Processed bank transactions |
| `processed.invoices` | 470 | Customer invoice and receivables records |
| `processed.supplier_bills` | 355 | Supplier bill and obligations records |
| `processed.investigation_queue` | 141 | Records requiring review |
| `processed.duplicates_removed` | 307 | Audit trail for removed duplicate records |
| `processed.profile_conflicts` | 1 | Conflicting business-profile versions |
| `processed.data_quality_metrics` | 85 | Data-quality metrics by business and dataset |
| **Total** | **21,037** | Operational and audit records |

The total includes audit records. It is not the count of distinct financial transactions, and it must not be used as a financial volume or activity metric.

## Initial validation results

The following checks have been completed against `orey_cashflow_dev`:

| Validation | Result |
|---|---|
| All eight tables populated | Passed |
| Expected table record counts | Passed |
| Bank transactions referencing existing businesses | 0 missing references |
| Invoices referencing existing businesses | 0 missing references |
| Supplier bills referencing existing businesses | 0 missing references |
| Bank-to-ledger reciprocal-link consistency | 0 inconsistent links |
| Bank transaction IDs assigned to multiple invoice or supplier-bill records | 0 shared assignments |

These results establish that the imported tables have the expected counts and that the tested relationships are consistent.

They do **not** prove that every reconciliation decision, transaction amount, business profile or forecast is financially correct. Further financial validation, source-to-database comparisons and economic calibration remain necessary.

## Deliberately left out

- **`reconciliation-evaluation.csv`:** This file evaluates the pipeline against the synthetic dataset's known ground truth. It remains a development-validation artefact and is not loaded into the production-facing `processed` schema.
- **Raw and staging database tables:** These layers remain CSV-based for now. The current PostgreSQL source of truth begins at the processed layer.
- **Analytics, forecasting and scenario tables:** These belong to future analytical components and should be added through deliberate schema design and migrations.
- **Authentication and production access controls:** The current local development setup is not a production security configuration.
- **Automated loading and refresh:** The initial imports were performed manually. A repeatable loader with validation and failure handling remains to be implemented.

## Data-quality findings and limitations

Profiling the synthetic data revealed several important findings.

### 1. Floating-point noise in amount differences

`amount_difference` previously contained floating-point artefacts such as `1114.3100000000013`. The processing logic was updated to round these amounts to cents before database loading.

### 2. Running-balance integrity

The initial synthetic bank balances did not consistently follow the preceding balance plus the transaction movement. The generator was updated to recompute balances chronologically from each business's opening balance.

The resulting balances must still be tested through independent database validation before they are treated as fully reliable for cash-position analysis.

### 3. Synthetic-business economic calibration

The synthetic businesses are not yet fully economically calibrated to their own business profiles. This is a known limitation.

Before relying on burn rate, runway, cash-flow forecasts or business-level financial conclusions, validate the relationship between each business's profile, transaction activity, revenue and operating obligations. A structurally valid database can still contain economically unrealistic synthetic data.

### 4. Reconciliation exceptions

The data contains records that require investigation, including conflicting amounts, missing bank records, possible sign errors, reversals and conflicting profile versions.

These records must remain visible to downstream analytics. A matched or paid status should not be interpreted as proof of cash movement without applying the appropriate reconciliation rules.

## Next implementation steps

The next work should follow this order.

| Priority | Component | Objective |
|---|---|---|
| 1 | Database loader | Implement a repeatable, dependency-aware loading process with validation, failure handling and safe refresh behaviour |
| 2 | Source-to-database validation | Compare database results against processed CSV outputs and independently verify financial totals and data-quality metrics |
| 3 | `05-indexes` | Add justified indexes for common filters and joins, including business identifiers, transaction dates and reconciliation statuses |
| 4 | `03-views` | Create stable analytical views for reconciled cash movements, receivables, supplier obligations and other approved metrics |
| 5 | R and Python connectivity | Configure analytics scripts and application components to query PostgreSQL as their primary processed-data source |
| 6 | Financial logic validation | Validate cash movement, opening and closing balances, outstanding obligations and business-level economic plausibility |
| 7 | Forecasting and scenarios | Build the rolling 13-week and 12-month forecasting and what-if analysis components on validated database inputs |
| 8 | Reporting | Generate executive-summary PDFs from the same approved metrics used by the web application |
| 9 | Security and migrations | Introduce versioned schema changes, least-privilege roles, credential management, backups and production deployment controls |

### Future folders

- `03-views` — analysis-friendly SQL views.
- `05-indexes` — performance indexes.
- `06-migrations` — versioned database changes.
- A database-loading component under the existing data-engineering structure, unless a dedicated database-loader directory is established.
- Authentication and security configuration under the project's existing security structure.

Folder numbering should be aligned with the existing repository before creating new directories. Do not create a second copy of a folder or loader that already exists.

## Development rules

1. PostgreSQL is the primary source for downstream analytics.
2. The existing pipeline remains responsible for processing and reconciling source data.
3. Preserve raw source files and reproducible pipeline outputs.
4. Do not silently overwrite unresolved data-quality issues.
5. Do not interpret invoice status as confirmed bank cash movement without reconciliation evidence.
6. Validate record counts, relationships and financial totals after each database refresh.
7. Use versioned migrations for structural changes after the initial schema.
8. Keep credentials out of source control and use appropriately restricted database roles as the application develops.
9. Do not treat synthetic data as production evidence or make business-level claims until its economic assumptions have been validated.

The database layer is the foundation for Orey Analytics' Phase 06 cash-flow intelligence platform. Its purpose is not merely to store processed CSVs, but to provide a consistent, auditable and validated financial-data interface for the analytics, forecasting, risk and reporting components built on top of it.