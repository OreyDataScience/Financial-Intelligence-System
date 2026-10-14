# 01-raw

Raw, unmodified source data for Phase 06. These are the four datasets defined in `../DATA_SPECIFICATION.md`, plus two files that exist only because the data is currently synthetic.

## Rule: raw data is immutable

Nothing downstream edits or overwrites files here. Cleaning, standardization and reconciliation happen in `02-staging` and `03-processed`. The generator enforces this too: it refuses to overwrite existing raw files unless run with `--force`.

## Files

| File | Real source or synthetic-only | Description |
|---|---|---|
| `business_profiles_raw.csv` | Represents a real source | SME identity and context |
| `bank_transactions_raw.csv` | Represents a real source | Bank account activity |
| `invoices_raw.csv` | Represents a real source | Customer invoices |
| `supplier_bills_raw.csv` | Represents a real source | Supplier obligations |
| `data-quality-issues-log.csv` | **Synthetic-only** | Ground truth of every injected problem |
| `generation-summary.md` | **Synthetic-only** | Row counts and issue counts for this generation run |

## Two of these files will never exist with real data

`data-quality-issues-log.csv` and `generation-summary.md` are testing aids produced by the generator. A real bank statement or accounting export never arrives with a list of its own errors.

We keep them here because they let us measure whether the pipeline catches what it should. When real SME data replaces synthetic data, **these two files disappear**, and the pipeline must not depend on them. The pipeline reads the issues log in exactly two places, both clearly separated evaluation steps (staging recall/precision and reconciliation evaluation). If any cleaning or matching decision ever reads the log, that is a bug: the pipeline would be cheating off the answer key.

## Regenerating

The generator lives in `02-data-engineering/01-ingestion/generate_raw_data.py`. It is deterministic (seed 42): the same seed produces byte-identical files.

```powershell
python .\02-data-engineering\01-ingestion\generate_raw_data.py --force
```

Prefer the pipeline runner (`02-data-engineering/06-pipeline-tasks`), which runs all three stages in order.
