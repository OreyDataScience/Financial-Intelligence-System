# Staging: Detection Evaluation Report

(Test-only — measures pipeline detection logic against known synthetic ground truth.
This evaluation step, and the ground-truth log it reads, do not exist in the real pipeline.)

## Recall — did we catch every injected issue?

**Overall detection (recall) rate: 100.0%**

| Dataset | Issue type | Injected | Detected | Rate |
|---|---|---|---|---|
| business_profiles_raw.csv | missing_value | 2 | 2 | 100% |
| business_profiles_raw.csv | type_inconsistency | 1 | 1 | 100% |
| business_profiles_raw.csv | conflicting_record | 1 | 1 | 100% |
| bank_transactions_raw.csv | delayed_posting | 376 | 376 | 100% |
| bank_transactions_raw.csv | duplicate | 292 | 292 | 100% |
| bank_transactions_raw.csv | missing_reference | 780 | 780 | 100% |
| bank_transactions_raw.csv | missing_value | 585 | 585 | 100% |
| bank_transactions_raw.csv | reversal | 2 | 2 | 100% |
| bank_transactions_raw.csv | sign_inconsistency | 1 | 1 | 100% |
| invoices_raw.csv | duplicate | 5 | 5 | 100% |
| invoices_raw.csv | missing_value | 20 | 20 | 100% |
| supplier_bills_raw.csv | duplicate | 4 | 4 | 100% |
| supplier_bills_raw.csv | missing_value | 15 | 15 | 100% |

## Precision — of everything we flagged, how much was a real logged issue?

A flag with no logged issue_type isn't necessarily wrong — it may be a genuine finding the generator never logged as an 'issue' at all (e.g. a payment recorded before its invoice date). Those rows are marked n/a rather than scored as false positives.

| Dataset | Flag | Total flagged | True positives | False positives | Precision |
|---|---|---|---|---|---|
| business_profiles_raw.csv | missing_employee_count | 1 | 1 | 0 | 100% |
| business_profiles_raw.csv | missing_financial_year_end | 1 | 1 | 0 | 100% |
| business_profiles_raw.csv | revenue_format_flagged | 1 | 1 | 0 | 100% |
| business_profiles_raw.csv | conflicting_profile_version | 2 | 1 | 1 | 50% |
| bank_transactions_raw.csv | missing_transaction_reference | 791 | 780 | 11 | 99% |
| bank_transactions_raw.csv | missing_balance_after_transaction | 595 | 585 | 10 | 98% |
| bank_transactions_raw.csv | delayed_posting_flag | 381 | 376 | 5 | 99% |
| bank_transactions_raw.csv | possible_sign_inconsistency | 3 | 1 | 2 | 33% |
| bank_transactions_raw.csv | is_reversal | 2 | 2 | 0 | 100% |
| bank_transactions_raw.csv | is_duplicate | 293 | 292 | 1 | 100% |
| invoices_raw.csv | missing_due_date | 20 | 20 | 0 | 100% |
| invoices_raw.csv | payment_before_invoice_flag | 6 | n/a | n/a | n/a (no logged issue_type) |
| invoices_raw.csv | is_duplicate | 5 | 5 | 0 | 100% |
| supplier_bills_raw.csv | missing_supplier_id | 15 | 15 | 0 | 100% |
| supplier_bills_raw.csv | is_duplicate | 4 | 4 | 0 | 100% |
