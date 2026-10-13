# Reconciliation Evaluation (test-only)

Compares reconciliation outcomes with the synthetic ground-truth log. This file and the log it reads do not exist in a real pipeline.

## Recall - were the injected ledger/bank problems caught?

| Dataset | Injected issue | Injected | Sent to investigation | With expected reason | Wrongly matched |
|---|---|---|---|---|---|
| invoices_raw.csv | no_bank_receipt | 48 | 48 | 48 | 0 |
| invoices_raw.csv | ledger_bank_amount_conflict | 9 | 9 | 9 | 0 |
| supplier_bills_raw.csv | no_bank_receipt | 37 | 36 | 36 | 1 |
| supplier_bills_raw.csv | ledger_bank_amount_conflict | 11 | 11 | 10 | 0 |

## Precision - is everything in the investigation queue there for a real reason?

| Dataset | In queue | Injected ledger/bank problem | Bank row had wrong sign | Bank payment reversed | Unexplained |
|---|---|---|---|---|---|
| invoices_raw.csv | 57 | 57 | 0 | 0 | 0  |
| supplier_bills_raw.csv | 62 | 47 | 11 | 4 | 0  |

"Wrongly matched" counts injected problems that the matcher paired with a different, near-identical payment. That is an inherent ambiguity when the same counterparty has two payments of almost the same amount inside one date window and the bank row carries no payment reference.
