# 01-data

Data foundation for Phase 06 — Cash Flow Intelligence. Everything here is synthetic but built to behave like real South African SME data: messy, partly contradictory, and never trusted blindly.

The full definition (SMEs, schemas, injected problems, reconciliation rules) lives in [`DATA_SPECIFICATION.md`](DATA_SPECIFICATION.md).

## Progress — Stage 1: Data Foundation

**Status:** Raw, staging and processed layers built and validated end to end. The data foundation is ready for `05-cashflow-intelligence`.

### What exists

| Layer | Folder | What it holds |
|---|---|---|
| Raw | `01-raw` | Four messy source datasets exactly as "received", plus a ground-truth log of every injected problem (synthetic-only) |
| Staging | `02-staging` | Standardized dates, signed amounts, standardized statuses and explicit flag columns; raw fields untouched |
| Processed | `03-processed` | Deduplicated, reconciled, analysis-ready data; an investigation queue; data-quality metrics |

Scale: 5 SMEs · 1 Jan 2024 – 31 Dec 2025 · 19,971 bank rows · 475 invoices · 359 supplier bills · 2,230 injected issues across 18 categories.

### What was built

- **Specification first.** `DATA_SPECIFICATION.md` was agreed before any data existed, so the generator implements the spec rather than the other way round.
- **A generator that links the sources.** Invoices and bills are created first, and most of their payments produce real bank transactions. A controlled minority is deliberately left without a bank record, and a few are given a different bank amount. This is what makes reconciliation a genuine test. (An earlier version generated the sources independently, so ~97% of payments were unmatchable by accident. Reconciliation work exposed it and it was fixed at the source.)
- **Staging detectors** that use rules only and never read the answer key. Measured afterwards: **100% recall** on every issue type staging can see; precision 98–100% on well-defined checks. The only "false positives" are duplicate and reversal copies that correctly inherit the original row's blank or delay.
- **A multi-pass reconciliation engine** matching paid invoices/bills to bank transactions on counterparty, amount and date, with counterparty-confirmed matches taking priority. Measured against ground truth: **104 of 105** injected ledger/bank problems sent to investigation, and **0 of 119** queued ledger items without a real cause.
- **An investigation queue** (`03-processed/investigation-queue.csv`) of everything a person should review, each with a reason. Nothing is dropped and nothing is silently "fixed".

### Honest limitations

- Near-identical payments from the same counterparty inside one date window cannot be told apart without a payment reference (1 such case in this dataset).
- The sign-inconsistency check is a keyword heuristic. It works here, but a production version should learn each business's normal pattern.
- Synthetic bank descriptions always carry the counterparty ID. Real ones often will not, so low-confidence matching will matter more.

## How to run

From anywhere (paths resolve from the script locations, not your terminal's folder):

```powershell
python .\02-data-engineering\06-pipeline-tasks\run_phase06_data_pipeline.py
```

Raw data is immutable, so generation is skipped when raw files already exist. To rebuild the synthetic dataset from scratch (identical output, fixed seed):

```powershell
python .\02-data-engineering\06-pipeline-tasks\run_phase06_data_pipeline.py --regenerate
```

Requires `pandas`, `numpy` and `faker`.

## Next

Build `05-cashflow-intelligence` on top of `03-processed`: cash position, runway, burn rate, receivables and payables ageing, and payment behaviour. The investigation queue and match-confidence columns should travel with the data so downstream metrics can show how much of a figure is reconciled versus uncertain.
