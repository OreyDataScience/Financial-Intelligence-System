# Staging: Detection Evaluation Report

Test-only. Measures the staging detection rules against the synthetic ground-truth log. This evaluation, and the log it reads, do not exist in a real pipeline.

## Recall - did we catch every injected issue?

**Overall recall (issue types staging can see): 100.0%**

| Dataset | Issue type | Injected | Detected | Rate |
|---|---|---|---|---|
| business_profiles_raw.csv | conflicting_record | 1 | 1 | 100% |
| business_profiles_raw.csv | missing_value | 2 | 2 | 100% |
| business_profiles_raw.csv | type_inconsistency | 1 | 1 | 100% |
| bank_transactions_raw.csv | delayed_posting | 380 | 380 | 100% |
| bank_transactions_raw.csv | duplicate | 295 | 295 | 100% |
| bank_transactions_raw.csv | missing_reference | 787 | 787 | 100% |
| bank_transactions_raw.csv | missing_value | 590 | 590 | 100% |
| bank_transactions_raw.csv | reversal | 4 | 4 | 100% |
| bank_transactions_raw.csv | sign_inconsistency | 21 | 21 | 100% |
| invoices_raw.csv | duplicate | 5 | 5 | 100% |
| invoices_raw.csv | missing_value | 20 | 20 | 100% |
| invoices_raw.csv | payment_before_invoice | 8 | 8 | 100% |
| supplier_bills_raw.csv | duplicate | 4 | 4 | 100% |
| supplier_bills_raw.csv | missing_value | 7 | 7 | 100% |

105 injected issues of type `no_bank_receipt` / `ledger_bank_amount_conflict` are invisible to staging by design (they only appear when a ledger is compared with the bank). They are evaluated in `03-processed`.

## Precision - of everything flagged, how much was a real logged issue?

| Dataset | Flag | Flagged | True positives | False positives | Precision |
|---|---|---|---|---|---|
| business_profiles_raw.csv | missing_employee_count | 1 | 1 | 0 | 100% |
| business_profiles_raw.csv | missing_financial_year_end | 1 | 1 | 0 | 100% |
| business_profiles_raw.csv | revenue_format_flagged | 1 | 1 | 0 | 100% |
| business_profiles_raw.csv | conflicting_profile_version | 2 | 1 | 1 | 50% |
| bank_transactions_raw.csv | missing_transaction_reference | 796 | 787 | 9 | 99% |
| bank_transactions_raw.csv | missing_balance_after_transaction | 601 | 590 | 11 | 98% |
| bank_transactions_raw.csv | delayed_posting_flag | 387 | 380 | 7 | 98% |
| bank_transactions_raw.csv | possible_sign_inconsistency | 21 | 21 | 0 | 100% |
| bank_transactions_raw.csv | is_reversal | 4 | 4 | 0 | 100% |
| bank_transactions_raw.csv | is_duplicate | 298 | 295 | 3 | 99% |
| invoices_raw.csv | missing_due_date | 20 | 20 | 0 | 100% |
| invoices_raw.csv | payment_before_invoice_flag | 8 | 8 | 0 | 100% |
| invoices_raw.csv | is_duplicate | 5 | 5 | 0 | 100% |
| supplier_bills_raw.csv | missing_supplier_id | 7 | 7 | 0 | 100% |
| supplier_bills_raw.csv | is_duplicate | 4 | 4 | 0 | 100% |
