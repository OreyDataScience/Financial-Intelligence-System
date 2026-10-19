
/*
    Orey Analytics
    Phase 06 - Cash Flow Intelligence

    View: analytics.v_bank_transactions_enriched

    Purpose:
    Provide a consistent transaction-level dataset for
    downstream cash-flow analytics, forecasting and reporting.

    Design principles:
    - Preserve all processed bank transactions.
    - Use standardized dates for analysis.
    - Retain reconciliation and data-quality indicators.
    - Enrich each transaction with its SME profile.
    - Do not interpret net movement as closing cash balance.
*/

BEGIN;

CREATE SCHEMA IF NOT EXISTS analytics;

CREATE OR REPLACE VIEW analytics.v_bank_transactions_enriched AS
SELECT
    -- Transaction identifiers
    b.source_record_id,
    b.business_id,

    -- SME profile
    p.business_name,
    p.industry,
    p.province,
    p.accounting_basis,
    p.profile_status,

    -- Account and transaction details
    b.bank_name,
    b.account_id,
    b.currency,
    b.transaction_date_std AS transaction_date,
    b.posting_date_std AS posting_date,
    b.transaction_description,
    b.description_normalized,
    b.transaction_reference,

    -- Financial amounts
    b.debit_amount,
    b.credit_amount,
    b.net_amount,
    b.balance_after_transaction,

    -- Operational and timing indicators
    b.is_operational,
    b.posting_delay_days,
    b.delayed_posting_flag,

    -- Data-quality indicators
    b.missing_transaction_reference,
    b.missing_balance_after_transaction,
    b.possible_sign_inconsistency,
    b.is_reversal,
    b.is_netted_pair,
    b.netted_pair_id,
    b.review_reasons,
    b.data_quality_notes,

    -- Reconciliation details
    b.reconciliation_status,
    b.matched_ledger_type,
    b.matched_ledger_source_record_id

FROM processed.bank_transactions AS b
LEFT JOIN processed.business_profiles AS p
    ON b.business_id = p.business_id;

COMMENT ON VIEW analytics.v_bank_transactions_enriched IS
'Transaction-level bank data enriched with SME profiles, standardized dates, financial amounts, reconciliation status and data-quality indicators. Net movement is not equivalent to closing cash balance.';

COMMIT;
