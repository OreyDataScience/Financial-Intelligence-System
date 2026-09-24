# 02-staging

Standardized, flagged versions of the four raw datasets, produced by `02-data-engineering/02-cleaning/clean_and_validate.py`. Raw data itself is never modified — this stage adds new columns alongside the original fields, preserving full traceability back to `01-raw`.

## What was done

- Parsed all inconsistent date formats (`2024-01-01`, `01/01/2024`, `01 Jan 2024`) into a single standardized date column per date field.
- Computed a signed `net_amount` for bank transactions (positive = inflow, negative = outflow).
- Standardized invoice/bill status values into consistent categories.
- Added explicit boolean flag columns for detected issues: missing references, missing balances, duplicates, delayed postings, possible sign inconsistencies, reversals, paid-amount mismatches, and missing due dates / supplier IDs.
- Detection logic is rule-based only — it never reads the ground-truth issues log. The log is used strictly afterward, for evaluation.

## Files

| File | Description |
|---|---|
| `business_profiles_staging.csv` | Standardized profiles with missing/format/conflict flags |
| `bank_transactions_staging.csv` | Standardized transactions with duplicate/reversal/sign/delay flags |
| `invoices_staging.csv` | Standardized invoices with status/duplicate/mismatch flags |
| `supplier_bills_staging.csv` | Standardized bills with duplicate/missing-supplier flags |
| `detection-evaluation.csv` / `.md` | Recall: % of injected issues actually caught, per issue type |
| `precision-evaluation.csv` | Precision: of everything flagged, how much was a real issue (vs. false positive) |

## Result

- **Recall: 100%** — every injected issue across all 13 categories was detected.
- **Precision: mostly 98–100%** on well-defined checks (missing values, duplicates, delayed postings). Two heuristic-based flags scored lower and are flagged as known limitations, not production-ready logic:
  - `possible_sign_inconsistency` (33% precision) — keyword-based heuristic, fragile by nature.
  - `conflicting_profile_version` (50% precision) — flags both sides of a conflicting pair, but the ground-truth log only recorded one side; not a true error, just a scoring artifact.

Building this also caught two real bugs along the way: an overly broad keyword (`"SETTLEMENT"` matched both legitimate retail sales and genuine supplier outflows) and a type-check that was meaningless given the raw CSVs were loaded as all-string. Both are fixed in the current script.

## Next

`03-processed` — reconcile invoices/bills against bank transactions and produce the analysis-ready, traceable dataset.