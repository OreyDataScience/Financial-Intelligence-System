# 01-raw

Raw, unmodified source data for Phase 06 Cash Flow Intelligence. This folder holds the four raw datasets defined in `01-data/DATA-SPECIFICATION.md`, plus two generation-time artifacts that exist only because this data is currently synthetic.

## Rule: raw data is immutable

Files in this folder are never edited or overwritten by the pipeline. Cleaning, standardization, and reconciliation happen downstream in `02-staging` and `03-processed`. If a raw file needs to change, a new version is added (the original is never silently modified)

## Files

| File | Real or synthetic-only | Description |
|---|---|---|
| `business_profiles_raw.csv` | Represents a real source | SME identity and context |
| `bank_transactions_raw.csv` | Represents a real source | Bank account activity |
| `invoices_raw.csv` | Represents a real source | Customer invoices |
| `supplier_bills_raw.csv` | Represents a real source | Supplier obligations |
| `data-quality-issues-log.csv` | **Synthetic-only** | Ground truth of every data-quality issue intentionally injected during generation |
| `generation-summary.md` | **Synthetic-only** | Row counts and issue-type counts for this generation run |

## Important: two of these files won't exist with real data

`data-quality-issues-log.csv` and `generation-summary.md` are **testing aids produced by the synthetic data generator**, not something a real bank statement or accounting export would ever come with. A real source never ships with a list of its own errors attached.

We're keeping them in `01-raw` for now because they're useful ground truth while we build and validate the `02-data-engineering` pipeline, they let us check what percentage of known, intentionally-injected issues the pipeline actually catches.

**When real SME data replaces synthetic data, these two files disappear.** The pipeline (cleaning, validation, reconciliation logic in `02-data-engineering`) must not depend on their presence, and no downstream stage should read them for anything other than test/validation purposes. If pipeline code ever reaches for `data-quality-issues-log.csv` to make a cleaning decision, that's a bug (it means the pipeline is cheating off the answer key instead of detecting issues on its own)

## Regenerating the synthetic dataset

The generator lives in `02-data-engineering/01-ingestion/generate_raw_data.py` and is fully reproducible (fixed seed = 42). Re-running it with the same seed produces byte-for-byte the same dataset, which matters for debugging pipeline changes over time.

```
python generate_raw_data.py --outdir ../../01-data/01-raw
```

See `01-data/DATA-SPECIFICATION.md` for the full schema definitions, SME profiles, and the complete list of data-quality problems intentionally built into this dataset.