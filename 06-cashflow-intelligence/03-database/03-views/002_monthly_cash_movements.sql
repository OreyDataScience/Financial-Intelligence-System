
BEGIN;

CREATE SCHEMA IF NOT EXISTS analytics;

CREATE OR REPLACE VIEW analytics.v_monthly_cash_movements AS
SELECT
    b.business_id,
    p.business_name,
    p.industry,
    b.currency,
    DATE_TRUNC('month', b.transaction_date)::date AS month_start,

    -- Cash movement amounts
    COUNT(*) AS transaction_count,

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

    -- Transaction classifications and data quality
    COUNT(*) FILTER (
        WHERE b.is_operational IS TRUE
    ) AS operational_flagged_transaction_count,

    COUNT(*) FILTER (
        WHERE b.reconciliation_status = 'matched_ledger'
    ) AS matched_ledger_count,

    COUNT(*) FILTER (
        WHERE b.reconciliation_status = 'ledger_conflict'
    ) AS ledger_conflict_count,

    COUNT(*) FILTER (
        WHERE b.reconciliation_status = 'unmatched_needs_investigation'
    ) AS unmatched_investigation_count,

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
            OR NULLIF(BTRIM(COALESCE(b.review_reasons, '')), '') IS NOT NULL
    ) AS investigation_required_count,

    COUNT(*) FILTER (
        WHERE b.is_netted_pair IS TRUE
    ) AS netted_pair_transaction_count

FROM analytics.v_bank_transactions_enriched AS b

LEFT JOIN processed.business_profiles AS p
    ON b.business_id = p.business_id

GROUP BY
    b.business_id,
    p.business_name,
    p.industry,
    b.currency,
    DATE_TRUNC('month', b.transaction_date)::date;

COMMENT ON VIEW analytics.v_monthly_cash_movements IS
'Monthly bank transaction summaries by SME and currency, including credit inflows, debit outflows, net bank movement, transaction classifications and investigation indicators. Net bank movement is not a closing cash balance. Different currencies must not be aggregated without conversion.';

COMMIT;