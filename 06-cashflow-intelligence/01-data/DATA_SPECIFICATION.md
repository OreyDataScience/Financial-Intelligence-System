# Phase 06 — Synthetic SME Data Specification

**Status:** v2 — implemented and validated
**Owner:** Orey Analytics — Cash Flow Intelligence
**Applies to:** `01-data/01-raw`, `01-data/02-staging`, `01-data/03-processed`

This is the source of truth for how synthetic SME financial data is generated, structured and validated in Phase 06. The generator implements this document; if the generator and this file disagree, this file is updated first.

The guiding principle: **build the pipeline as if Orey Analytics were onboarding real South African SMEs**, even while developing on synthetic data.

---

## 1. Scope and design decisions

| Decision | Specification |
|---|---|
| Geography / currency | South Africa / ZAR (non-ZAR rows would be flagged, never assumed) |
| Population (v1) | 5 synthetic SMEs |
| History | 1 January 2024 – 31 December 2025 (24 months) |
| Sources | Bank statements, invoices, supplier bills, business profiles |
| Approach | Immutable raw → flagged staging → reconciled processed |
| Reproducibility | Fixed seed (`SEED = 42`); same seed gives byte-identical raw files |
| Overwrite protection | Generator refuses to overwrite raw data unless `--force` is passed |

---

## 2. SME profiles

| ID | Business type | Annual revenue | Staff | Cash-flow character |
|---|---|---|---|---|
| SME_001 | Retail store | R3.5m | 8 | Daily card sales, supplier payments, a few B2B invoices |
| SME_002 | Consulting firm | R2.1m | 5 | Irregular client payments, monthly payroll |
| SME_003 | Construction | R8.0m | 15 | Large, infrequent project payments; subcontractor liabilities |
| SME_004 | Wholesale distributor | R12.0m | 20 | High volume, cash-and-carry plus trade-credit accounts, supplier credit |
| SME_005 | Professional services | R1.8m | 4 | Recurring retainers, steady costs, occasional late payers |

Profiles drive statistical parameters (frequency, amount ranges, payment delays). They are starting profiles; the population will grow once the pipeline is proven.

---

## 3. Raw sources and schemas

Sources are allowed to disagree with each other. Reconciling them is a downstream concern, never a generation-time fix.

**`business_profiles_raw.csv`** — `source_record_id, business_id, business_name, industry, business_start_date, province, employee_count, annual_revenue, accounting_basis, financial_year_end, source_file`

**`bank_transactions_raw.csv`** — `source_record_id, business_id, bank_name, account_id, transaction_date, posting_date, transaction_description, transaction_reference, debit_amount, credit_amount, balance_after_transaction, currency, source_file`

**`invoices_raw.csv`** — `source_record_id, business_id, invoice_id, customer_id, invoice_date, due_date, invoice_amount, amount_paid, invoice_status, payment_date, currency, source_file`

**`supplier_bills_raw.csv`** — `source_record_id, business_id, bill_id, supplier_id, bill_date, due_date, bill_amount, amount_paid, bill_status, payment_date, currency, source_file`

Original fields, formats and sign conventions are preserved exactly as received.

---

## 4. How the data is generated

Generation order matters, because the sources must be *economically linked* for reconciliation to be a meaningful test:

1. **Invoices and supplier bills are generated first** as the underlying economic events (amounts, terms, statuses, payment dates).
2. **Payments that have not happened by 31 Dec 2025 are recorded as unpaid** (the ledger is a view as of the data cut-off).
3. **Bank transactions are then derived** from paid / partially-paid ledger records: invoices become bank credits, bills become bank debits, with small date offsets, and the counterparty ID appears in the bank description.
4. **Deliberate gaps are introduced:**
   - ~12% of paid/partially-paid records get **no bank transaction** (`no_bank_receipt`).
   - ~3% of fully-paid records have a **bank amount that differs** from the ledger (`ledger_bank_amount_conflict`).
5. **Independent operational noise** is added, which has no ledger counterpart by design: retail card settlements, wholesale cash-and-carry orders, payroll, operating expenses.
6. **Bank-export messiness** is applied (see §6), then ledger date formats are scrambled and duplicate imports added.

Every injected issue is written to `data-quality-issues-log.csv` at the moment it is injected.

---

## 5. Generation rules

1. Raw data is immutable. Corrections happen in staging or processed, never in raw.
2. Every imported row has a unique `source_record_id`; duplicate imports keep separate IDs.
3. `business_id` is consistent across all four datasets.
4. `transaction_date` and `posting_date` stay distinct.
5. Ledger status fields are source-reported claims, never trusted facts.
6. No artificial balancing: discrepancies between sources are intentional.
7. Zero, missing, unknown and not-applicable are never collapsed (see §8).
8. Unusual is not the same as wrong: large one-off payments are legitimate events and are not flagged as errors.

---

## 6. Issue catalogue (ground truth)

Counts are for seed 42.

| Dataset | Issue type | What is injected | Count |
|---|---|---|---|
| bank_transactions | `duplicate` | Same transaction imported twice | 295 |
| bank_transactions | `missing_reference` | Blank transaction reference | 787 |
| bank_transactions | `missing_value` | Blank running balance | 590 |
| bank_transactions | `delayed_posting` | Posting 12 days after transaction | 380 |
| bank_transactions | `sign_inconsistency` | One bank's export records debits as credits | 21 |
| bank_transactions | `reversal` | A debit followed by its reversal | 4 |
| bank_transactions | *(unlogged)* | Mixed date formats, inconsistent descriptions | all rows |
| invoices | `duplicate` | Duplicate invoice import | 5 |
| invoices | `missing_value` | Missing due date | 20 |
| invoices | `payment_before_invoice` | Payment dated before the invoice | 8 |
| invoices | `no_bank_receipt` | Paid per ledger, no bank record | 48 |
| invoices | `ledger_bank_amount_conflict` | Ledger and bank disagree on amount | 9 |
| supplier_bills | `duplicate` | Duplicate bill import | 4 |
| supplier_bills | `missing_value` | Missing supplier ID | 7 |
| supplier_bills | `no_bank_receipt` | Paid per ledger, no bank record | 37 |
| supplier_bills | `ledger_bank_amount_conflict` | Ledger and bank disagree on amount | 11 |
| business_profiles | `missing_value` | Missing employee count / financial year-end | 2 |
| business_profiles | `type_inconsistency` | Revenue stored as text, e.g. "R 3,500,000" | 1 |
| business_profiles | `conflicting_record` | Second, stale profile version | 1 |

Total logged: **2,230**.

---

## 7. Validation and reconciliation rules

| Rule | Value |
|---|---|
| Amount tolerance (same payment) | within 1% (minimum R1) |
| Amount-conflict window | same counterparty, amount off by up to 20% |
| Date window | ledger `payment_date` within ±10 days of bank `transaction_date` |
| Reversal window | within 10 days, same business and description, opposite amount |
| Excluded from matching | bank rows that never have a ledger counterpart (card settlements, cash-and-carry, payroll, operating expenses), reversal rows, sign-inconsistent rows |

Matching runs in priority order, assigned globally by best fit so row order never decides a winner:

1. Exact amount + date, **counterparty-confirmed** matches first
2. Exact amount + date without counterparty evidence (flagged low confidence)
3. Amount conflict: same counterparty, amount differs
4. Explained by a bank row recorded under the wrong sign
5. Nothing found → `no_bank_record`

Outcomes: `matched`, `needs_investigation` (with a reason), `not_applicable`. Nothing is dropped and nothing is silently fixed. Conflicting profiles are kept visible and routed to review.

---

## 8. Zero, missing, unknown and not applicable

| Meaning | How it is represented |
|---|---|
| **Zero** (a real amount of 0) | `0` — e.g. `amount_paid = 0` on an unpaid invoice |
| **Missing** (should exist, was not supplied) | blank in raw, kept blank (never filled) in staging and processed; flagged (`missing_*`) |
| **Unknown** (cannot be determined) | `needs_investigation` with a reason |
| **Not applicable** (nothing to reconcile) | `reconciliation_status = not_applicable`, reason `not_yet_paid` |

---

## 9. Outputs by stage

| Stage | Outputs |
|---|---|
| `01-raw` | 4 raw datasets, `data-quality-issues-log.csv`, `generation-summary.md` |
| `02-staging` | 4 staged datasets with standardized columns and flags; recall / precision evaluation |
| `03-processed` | 4 analysis-ready datasets, `duplicates-removed.csv`, `profile-conflicts.csv`, `investigation-queue.csv`, `data-quality-metrics.csv`, `data-quality-report.md`, reconciliation evaluation |

---

## 10. Known limitations

- Matching ambiguity: two payments to the same counterparty with nearly identical amounts inside one date window cannot be told apart without a payment reference. The pipeline can mis-pair them; this is measured and reported, not hidden.
- `possible_sign_inconsistency` is a keyword heuristic and fragile by nature; a production version should learn each business's normal sign pattern per description template.
- Synthetic data is cleaner than reality in one way: counterparty IDs always appear in bank descriptions. Real bank data will often lack them, so low-confidence matching will matter more.
- `payment_before_invoice` is flagged but not yet routed anywhere downstream.
