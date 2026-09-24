Progress so far — Stage 1: Data Foundation

Status: Raw data generated, spec locked. Staging (02-staging) not yet started.

Defined DATA-SPECIFICATION.md as the source of truth for all data-generation decisions: 5 SME profiles (retail, consulting, construction, wholesale, professional services), the four raw source schemas, intentional data-quality scenarios, and validation/reconciliation rules for later stages.
Built generate_raw_data.py (in 02-data-engineering/01-ingestion) — a reproducible, seeded synthetic data generator implementing that spec.
Generated the initial raw dataset into 01-raw/, covering 1 Jan 2024 – 31 Dec 2025:
business_profiles_raw.csv — 5 SMEs + 1 intentional conflicting duplicate profile
bank_transactions_raw.csv — ~19,800 transactions
invoices_raw.csv — 475 invoices
supplier_bills_raw.csv — 359 bills
Logged every intentionally injected data-quality issue (2,084 total — duplicates, missing references, sign inconsistencies, delayed postings, status/amount mismatches, etc.) to data-quality-issues-log.csv, to be used as ground truth for validating the 02-data-engineering pipeline later.
Documented in 01-raw/README.md that the issues log and generation summary are synthetic-only testing artifacts — a real bank/accounting feed will never produce them, and the pipeline must not depend on their presence.

Next up: build 02-data-engineering cleaning/validation logic and measure detection rate against the known issues log.
