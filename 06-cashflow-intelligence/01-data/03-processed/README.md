# 03-processed

Analysis-ready data, produced by `02-data-engineering/03-transformation/reconcile_and_process.py` from `02-staging`.

This is the layer that `05-cashflow-intelligence`, forecasting, scenarios, risk and the web app should read. It keeps full traceability: every row carries its `source_record_id`, and anything removed is logged rather than lost.

## What processing does

- **Removes duplicate imports** from the analysis layer and logs every one in `duplicates-removed.csv`.
- **Links reversal pairs** (`netted_pair_id`). They already net to zero in cash, so nothing is dropped.
- **Reconciles invoices and supplier bills to the bank** on counterparty, amount and date, in priority order (see the specification, §7). Each ledger row gets a `reconciliation_status`, a `reconciliation_reason`, a `match_confidence` and the matched bank row.
- **Never forces a match.** Anything that cannot be matched is `needs_investigation` with a reason. Nothing is silently fixed in either direction.
- **Keeps conflicting business profiles visible** (`profile_status = conflict_needs_review`, listed in `profile-conflicts.csv`). Missing values stay missing.
- **Builds an investigation queue** of everything a person should look at.

## Files

| File | Description |
|---|---|
| `business_profiles_processed.csv` | One working record per business, with `profile_status` |
| `bank_transactions_processed.csv` | Deduplicated bank rows with reconciliation status, reversal links, review reasons and data-quality notes |
| `invoices_processed.csv` | Deduplicated invoices with reconciliation outcome |
| `supplier_bills_processed.csv` | Deduplicated bills with reconciliation outcome |
| `investigation-queue.csv` | Every item needing review, with dataset, reason and detail |
| `duplicates-removed.csv` | Audit trail of removed duplicates |
| `profile-conflicts.csv` | Conflicting profile versions and which fields differ |
| `data-quality-metrics.csv`, `data-quality-report.md` | Per-business quality rates and match rates (pipeline output, no ground truth) |
| `reconciliation-evaluation.csv`, `reconciliation-evaluation.md` | **Test-only.** Measurement against ground truth |

## Reconciliation outcomes

| Status | Meaning |
|---|---|
| `matched` | A bank transaction agrees on counterparty / amount / date. `match_confidence` is `high` when the counterparty appears in the bank description, `low` when only amount and date agree |
| `needs_investigation` | Reason is one of `no_bank_record`, `amount_conflict`, `possible_sign_error_in_bank`, `payment_reversed`, `missing_payment_date` |
| `not_applicable` | Nothing to reconcile yet (unpaid / overdue) |

## Results (seed 42)

| | Invoices | Supplier bills |
|---|---|---|
| Matched | 330 (70%) | 253 (71%) |
| Needs investigation | 57 (12%) | 62 (17%) |
| Not applicable | 83 (18%) | 40 (11%) |

Investigation queue: 141 items in total (57 invoices, 62 bills, 21 sign-inconsistent bank rows, 1 conflicting profile).

Measured against ground truth (test-only):

- **Recall: 104 of 105** injected ledger/bank problems were sent to investigation. The one miss is a genuine ambiguity: two same-supplier payments of nearly identical amounts inside one date window, with no payment reference to tell them apart.
- **Precision: 0 of 119** queued ledger items lacked a real cause. Each traces to an injected ledger/bank problem, a bank row recorded under the wrong sign (11), or a reversed bank payment (4).
- **Bank side:** every settlement-like bank transaction is accounted for (583 matched, 34 in conflict, 0 unexplained).

## What to carry forward

Downstream metrics should keep the reconciliation fields. A cash or receivables figure should be able to say how much of it is reconciled, how much is low confidence and how much sits in the investigation queue. That is what makes the numbers trustworthy to a lender.

## Limitations

- Amount tolerance (1%) and date window (±10 days) are fixed defaults; real businesses will need them tuned per bank and per customer behaviour.
- Matching is deterministic and rule-based; there is no probabilistic scoring or learning yet.
- Bank rows classed as operational (card settlements, cash-and-carry, payroll, operating expenses) are never matched to invoices. On real data some customers will pay that way.
