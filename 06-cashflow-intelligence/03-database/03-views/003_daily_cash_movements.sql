
BEGIN;

CREATE SCHEMA IF NOT EXISTS analytics;

CREATE OR REPLACE VIEW analytics.v_daily_cash_movements AS
SELECT
    b.business_id,
    b.business_name,
    b.industry,
    b.currency,
    b.transaction_date AS movement_date,

    -- Daily transaction activity
    COUNT(*) AS transaction_count,

    -- Daily inflows and outflows
    COALESCE(
        SUM(COALESCE(b.credit_amount, 0)),
        0
    ) AS total_credit_inflows,

    COALESCE(
        SUM(COALESCE(b.debit_amount, 0)),
        0
    ) AS total_debit_outflows,

    COALESCE(
        SUM(COALESCE(b.net_amount, 0)),
        0
    ) AS net_bank_movement,

    -- Reconciliation indicators
    COUNT(*) FILTER (
        WHERE b.reconciliation_status = 'matched_ledger'
    ) AS matched_ledger_count,

    COUNT(*) FILTER (
        WHERE b.reconciliation_status = 'ledger_conflict'
    ) AS ledger_conflict_count,

    COUNT(*) FILTER (
        WHERE b.reconciliation_status = 'unmatched_needs_investigation'
    ) AS unmatched_investigation_count,

    -- Data-quality indicators
    COUNT(*) FILTER (
        WHERE b.is_reversal IS TRUE
    ) AS reversal_count,

    COUNT(*) FILTER (
        WHERE b.possible_sign_inconsistency IS TRUE
    ) AS sign_inconsistency_count,

    COUNT(*) FILTER (
        WHERE
            b.reconciliation_status IN (
                'ledger_conflict',
                'unmatched_needs_investigation'
            )
            OR b.possible_sign_inconsistency IS TRUE
            OR NULLIF(
                BTRIM(COALESCE(b.review_reasons, '')),
                ''
            ) IS NOT NULL
    ) AS investigation_required_count

FROM analytics.v_bank_transactions_enriched AS b

GROUP BY
    b.business_id,
    b.business_name,
    b.industry,
    b.currency,
    b.transaction_date;

COMMENT ON VIEW analytics.v_daily_cash_movements IS
'Daily bank transaction summaries by SME and currency, including inflows, outflows, net movement and data-quality indicators. Net bank movement is not a closing cash balance. Days without transactions are not automatically represented.';

COMMIT;
