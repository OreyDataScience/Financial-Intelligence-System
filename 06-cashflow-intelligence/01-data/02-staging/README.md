# 02-staging

Standardized, flagged versions of the four raw datasets, produced by `02-data-engineering/02-cleaning/clean_and_validate.py`.

Raw fields are never changed. Standardized values and flags are added as **new columns alongside the originals**, so every staged row stays traceable to the raw row it came from.

## What staging does

- Parses the three mixed date formats (`2024-01-01`, `01/01/2024`, `01 Jan 2024`) into one standard column per date field.
- Computes a signed `net_amount` for bank rows (positive = money in, negative = money out).
- Standardizes invoice and bill statuses (`Paid` / `paid` / `PAID` → `paid`, and so on).
- Adds explicit boolean flags: duplicates, missing references / balances / due dates / supplier IDs, delayed postings, reversals, possible sign inconsistencies, payment dated before the invoice or bill, conflicting profile versions, revenue stored as text.
- Uses **rules only**. The ground-truth issues log is never read during cleaning.

Staging deliberately does **not** resolve anything. It marks problems; deciding what to do about them is the processing stage's job.

## Files

| File | Description |
|---|---|
| `business_profiles_staging.csv` | Profiles with missing / format / conflict flags and a numeric revenue column |
| `bank_transactions_staging.csv` | Transactions with standardized dates, `net_amount` and issue flags |
| `invoices_staging.csv` | Invoices with standardized dates and status, and issue flags |
| `supplier_bills_staging.csv` | Bills with standardized dates and status, and issue flags |
| `detection-evaluation.csv`, `precision-evaluation.csv`, `detection-evaluation-report.md` | Test-only measurement of the detectors against ground truth |

## Results (seed 42)

- **Recall: 100%.** Every injected issue that staging can see was detected, across all 14 issue-type / dataset combinations.
- **Precision: 98–100%** on the well-defined checks. Every residual "false positive" (9 missing references, 11 missing balances, 7 delayed postings) is a duplicate or reversal row that correctly inherits the original row's blank or delay. It is correct behaviour that strict row-ID scoring penalizes.
- **`conflicting_profile_version`: 50%.** It flags both sides of a conflicting pair; the ground truth recorded only the stale one. Pair-aware scoring would be needed to call that a true error.
- **`possible_sign_inconsistency`: 100% on this dataset** (21 of 21), but it is a keyword heuristic and fragile by nature; see Limitations.

106 injected issues of two types (`no_bank_receipt`, `ledger_bank_amount_conflict`) are **invisible to staging by design**. They only appear when a ledger is compared with the bank, so they are measured in `03-processed`.

## Lessons from building and measuring this stage

- A keyword that is too generic misfires: `SETTLEMENT` matched both genuine supplier outflows and ordinary card-sale inflows. Detectors need specific patterns.
- Reversal rows are legitimately credits that carry outflow wording; without an explicit exclusion they were mistaken for sign errors.
- Reading every column as text means "arrived as a string" proves nothing; type checks must look at content.

## Limitations

- The sign check relies on description keywords. A production version should learn each business's normal sign pattern per description template.
- Staging evaluation measures recall and precision against synthetic ground truth only. Real data will not have an answer key.
