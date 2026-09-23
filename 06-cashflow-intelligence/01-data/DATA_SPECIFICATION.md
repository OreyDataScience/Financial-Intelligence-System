# Phase 06: Synthetic SME Data Specification

**Status:** Locked for v1 generation
**Owner:** Orey Analytics — Cash Flow Intelligence
**Applies to:** `01-data/01-raw`, `01-data/02-staging`, `01-data/03-processed`

This document is the source of truth for how synthetic SME financial data is generated, structured, and validated for Phase 06.

---

## 1. Scope & Design Decisions

| Design decision | Specification |
|---|---|
| Geography | South Africa |
| Currency | ZAR (R) ... non-ZAR records explicitly flagged, never assumed |
| Business population (v1) | 5 synthetic SMEs |
| Historical period | 1 January 2024 – 31 December 2025 (24 months) |
| Transaction sources | Bank statements, accounting exports, invoices, supplier bills |
| Data type | Synthetic, with realistic financial patterns and intentional imperfections |
| Data approach | Immutable raw → validated staging → reconciled processed |
| Reproducibility | Fixed random seed (`SEED = 42`) |
| Main objective | A reliable, imperfect-by-design foundation for cash-flow intelligence |

---

## 2. SME Profiles

| ID | Business type | Annual revenue (approx) | Employees | Cash-flow characteristics |
|---|---|---|---|---|
| SME_001 | Retail store | R3,500,000 | 8 | Daily small-value sales, biweekly supplier payments, monthly inventory restock, low receivables risk |
| SME_002 | Consulting firm | R2,100,000 | 5 | Few clients, irregular/lumpy invoice payments, monthly payroll, low fixed opex |
| SME_003 | Construction business | R8,000,000 | 15 | Large infrequent project payments, 60–90 day delayed receivables, subcontractor liabilities, high volatility |
| SME_004 | Wholesale distributor | R12,000,000 | 20 | High transaction volume, thin margins, 30–60 day supplier credit terms |
| SME_005 | Professional services | R1,800,000 | 4 | Recurring monthly retainer revenue, steady opex, occasional late-paying clients |

These profiles drive the *statistical generation parameters* (transaction frequency, amount distributions, payment delay distributions) They are not hard-coded transactions. Population will expand beyond 5 once pipeline and quality controls are validated against this set.

---

## 3. Raw Data Sources

Four raw datasets are simulated, each representing a distinct, imperfect real-world feed. Sources are allowed to disagree with each other (reconciliation is a staging/processing concern, not a generation-time fix)

| Dataset | Captures |
|---|---|
| `business_profiles_raw.csv` | SME identity, industry, size, financial context |
| `bank_transactions_raw.csv` | Bank account activity (cash-flow & liquidity foundation) |
| `invoices_raw.csv` | Customer invoices, due dates, amounts, payment status |
| `supplier_bills_raw.csv` | Supplier obligations, due dates, settlement status |

### 3.1 `business_profiles_raw.csv`

| Field | Description |
|---|---|
| source_record_id | Unique ID assigned to the imported row |
| business_id | SME identifier |
| business_name | Fictional business name |
| industry | Business sector |
| business_start_date | Business establishment date |
| province | South African province |
| employee_count | Approximate number of employees |
| annual_revenue | Reported annual revenue |
| accounting_basis | Cash or accrual, if known |
| financial_year_end | Business financial year-end |
| source_file | Originating profile source |

**Injected issues:** missing employee_count; inconsistent industry labels (e.g. "Retail" vs "retail trade"); annual_revenue stored as text with currency symbol for a subset of rows; missing financial_year_end; one conflicting duplicate profile version per business.

### 3.2 `bank_transactions_raw.csv`

| Field | Description |
|---|---|
| source_record_id | Unique ID assigned to the imported row |
| business_id | SME identifier |
| bank_name | Simulated financial institution |
| account_id | Synthetic bank account identifier |
| transaction_date | Date the transaction occurred |
| posting_date | Date the bank posted the transaction |
| transaction_description | Original bank-provided description |
| transaction_reference | Bank transaction reference |
| debit_amount | Amount debited, as supplied |
| credit_amount | Amount credited, as supplied |
| balance_after_transaction | Reported account balance, if available |
| currency | Transaction currency |
| source_file | Originating statement/export |

**Injected issues:** duplicate imports (same transaction, new source_record_id); missing references; inconsistent date formats (2026-03-04, 04/03/2026, 04 Mar 2026); debit/credit sign inconsistencies for a subset of one bank's exports; missing balances; inconsistent merchant description spellings; reversal pairs (debit + matching reversal 1–4 days later); posting delays (0–5 days typical, occasional 10+ day late posting).

### 3.3 `invoices_raw.csv`

| Field | Description |
|---|---|
| source_record_id | Unique imported row ID |
| business_id | SME identifier |
| invoice_id | Invoice identifier from source |
| customer_id | Synthetic customer identifier |
| invoice_date | Date issued |
| due_date | Contractual payment due date |
| invoice_amount | Original invoice amount |
| amount_paid | Amount recorded as paid |
| invoice_status | Source-reported status (not trusted as fact) |
| payment_date | Recorded payment date, if available |
| currency | Invoice currency |
| source_file | Originating accounting export |

**Injected issues:** duplicate invoices; missing due dates; inconsistent status casing/values (Paid, paid, PAID, Partially Paid); partial payments; incorrect/implausible payment dates (before invoice_date); invoice_amount vs amount_paid mismatches; invoices marked "Paid" with no identifiable bank receipt.

### 3.4 `supplier_bills_raw.csv`

| Field | Description |
|---|---|
| source_record_id | Unique imported row ID |
| business_id | SME identifier |
| bill_id | Supplier bill identifier |
| supplier_id | Synthetic supplier identifier |
| bill_date | Date received/recorded |
| due_date | Contractual due date |
| bill_amount | Original bill amount |
| amount_paid | Amount recorded as paid |
| bill_status | Source-reported status |
| payment_date | Recorded payment date, if available |
| currency | Bill currency |
| source_file | Originating accounting export |

**Injected issues:** duplicate bills; missing supplier_id; incorrect due dates; partial payments; inconsistent statuses; bills recorded after their actual date; conflicts with bank debits (bill marked paid, no matching bank record).

---

## 4. Critical Data-Generation Rules

1. All SMEs operate in ZAR by default. Non-ZAR records are explicitly identified, never assumed.
2. Raw data is immutable. Corrections happen only in staging (source rows are never overwritten)
3. Every imported row gets a unique `source_record_id`. Duplicate financial events retain separate import-row IDs.
4. `business_id` is consistent across all four datasets.
5. `transaction_date` and `posting_date` are always kept distinct fields.
6. `invoice_status` / `bill_status` are source-reported values, never automatically trusted as fact.
7. No artificial balancing. Realistic discrepancies between sources are intentional and preserved.
8. Every intentionally injected data-quality issue is logged (see §6) so pipeline detection can be tested against ground truth.
9. Zero, missing, unknown, and not-applicable are always distinguishable — never collapsed into a single representation (e.g. `0`, blank, and `NULL` mean different things and are encoded differently).

---

## 5. Downstream Consumption Requirements

The dataset is designed around what every downstream module needs, not around convenience:

| Module | Needs from this dataset |
|---|---|
| Cashflow intelligence (05) | Clean-enough transaction history to compute burn rate, runway, liquidity ratios |
| Forecasting (06) | Sufficient history (24 months) and enough noise to test model robustness, not just fit a clean line |
| Scenario engine (07) | Real receivables/payables timing to simulate delayed payment / stress scenarios |
| Risk engine (08) | Genuine anomalies and payment-behaviour patterns to score against, not fabricated risk signals |
| Reporting (10) | Enough business diversity across 5 profiles to produce meaningfully different reports |
| Web app (12) | Realistic-enough SME identities and time series to build UI against non-trivial data |

---

## 6. Data-Quality Issue Log

Every injected issue is recorded at generation time in `01-data/01-raw/data-quality-issues-log.csv` with:

| Field | Description |
|---|---|
| issue_id | Unique ID |
| dataset | Which raw file the issue was injected into |
| source_record_id | The affected row |
| business_id | SME affected |
| issue_type | Category (e.g. `duplicate`, `missing_reference`, `sign_inconsistency`, `date_format_variant`, `status_inconsistency`) |
| description | Human-readable description of what was injected |

This log is the **ground truth** used later to validate that the `02-data-engineering` pipeline correctly detects and flags each category of issue. It is not visible to the pipeline itself (only to test/validation code)

---

## 7. Validation & Reconciliation Rules (for staging/processed stages)

These are targets for `02-staging` and `03-processed`, defined now so raw generation and later pipeline work stay aligned:

- Every `business_id` in transactional files must exist in `business_profiles_raw.csv`.
- Reconciliation must attempt to match invoice/bill payment records to bank transactions within a configurable tolerance window (amount + date), and explicitly flag unmatched records rather than dropping them.
- Reversal pairs must be identified and net correctly, not treated as two independent cash movements.
- Records with unresolvable conflicts are routed to a `needs_investigation` status (never silently resolved in either direction)
- Missingness, duplicate rate, and reconciliation-match rate are quantified per dataset per business in the data-quality report (`03-processed` stage output).

---

## 8. Outputs Expected From This Stage

- `01-raw/business_profiles_raw.csv`
- `01-raw/bank_transactions_raw.csv`
- `01-raw/invoices_raw.csv`
- `01-raw/supplier_bills_raw.csv`
- `01-raw/data-quality-issues-log.csv` (ground truth, generation-time only)
- `01-raw/generation-summary.md` (row counts, date ranges, injected issue counts per category)

Staging and processed outputs are out of scope for this document and will be specified separately once raw generation is validated.