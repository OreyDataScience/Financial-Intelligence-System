Progress so far — Stage 1: Data Foundation

Status: Raw data generated, staging pipeline built and validated. Processed (03-processed) not yet started.

Defined DATA-SPECIFICATION.md as the source of truth for all data-generation decisions: 5 SME profiles (retail, consulting, construction, wholesale, professional services), the four raw source schemas, intentional data-quality scenarios, and validation/reconciliation rules for later stages.
Built generate_raw_data.py (in 02-data-engineering/01-ingestion) — a reproducible, seeded synthetic data generator implementing that spec.
Generated the initial raw dataset into 01-raw/, covering 1 Jan 2024 – 31 Dec 2025:
business_profiles_raw.csv — 5 SMEs + 1 intentional conflicting duplicate profile
bank_transactions_raw.csv — ~19,800 transactions
invoices_raw.csv — 475 invoices
supplier_bills_raw.csv — 359 bills
Logged every intentionally injected data-quality issue (2,084 total — duplicates, missing references, sign inconsistencies, delayed postings, status/amount mismatches, etc.) to data-quality-issues-log.csv, to be used as ground truth for validating the 02-data-engineering pipeline later.
Documented in 01-raw/README.md that the issues log and generation summary are synthetic-only testing artifacts — a real bank/accounting feed will never produce them, and the pipeline must not depend on their presence.

Built clean_and_validate.py (in 02-data-engineering/02-cleaning) — standardizes dates, sign conventions, and status values across all four datasets, and flags data-quality issues using rule-based detection logic only (it never reads the issues log while cleaning — that would defeat the point).
Generated staging datasets into 02-staging/: standardized versions of all four datasets with explicit flag columns (duplicates, missing values, delayed postings, possible sign inconsistencies, reversals, amount mismatches), alongside the untouched original fields for full traceability.
Evaluated the pipeline against the ground-truth issues log, after the fact, as a separate test step:
Recall: 100% — every one of the 2,084 injected issues was caught, across all 13 issue types.
Precision: 98–100% on well-defined checks (missing values, duplicates, delayed postings). Two heuristic-based flags scored lower and are documented as known limitations rather than trusted as-is: a keyword-based sign-inconsistency check (33% precision — fragile by nature) and a conflicting-profile-version check (50% precision — flags both sides of a conflict pair, which is arguably correct behaviour scored harshly by a strict ground-truth match).
Along the way, this process caught and fixed two real bugs in the detection logic itself: an overly broad keyword that matched both legitimate revenue and genuine outflows, and a type-check that was meaningless given how the raw CSVs were loaded. Worth remembering as a pattern going forward — build the detector, measure it honestly, then fix what the measurement reveals.

Next up: build 03-processed — reconcile invoices and supplier bills against bank transactions, resolve conflicts into a `needs_investigation` status where unresolvable, and produce the analysis-ready, reconciled dataset the rest of the platform will consume.