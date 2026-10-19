
BEGIN;

CREATE OR REPLACE VIEW analytics.v_monthly_cash_movements AS
SELECT
    b.business_id,
    p.business_name,
    p.industry,
    b.currency,
    DATE_TRUNC('month', b.transaction_date::timestamp)::date AS month_start,

    COUNT(*) AS transaction_count,

    COALESCE(SUM(COALESCE(b.credit_amount, 0)), 0)
        AS total_credit_inflows,

    COALESCE(SUM(COALESCE(b.debit_amount, 0)), 0)
        AS total_debit_outflows,

    COALESCE(SUM(COALESCE(b.net_amount, 0)), 0)
        AS net_bank_movement,

    COUNT(*) FILTER (WHERE b.is_operational IS TRUE)
        AS operational_flagged_transaction_count,

    COUNT(*) FILTER (
        WHERE b.reconciliation_status = 'matched_ledger'
    ) AS matched_ledger_count,

    COUNT(*) FILTER (
        WHERE b.reconciliation_status = 'ledger_conflict'
    ) AS ledger_conflict_count,

    COUNT(*) FILTER (
        WHERE b.reconciliation_status = 'unmatched_needs_investigation'
    ) AS unmatched_investigation_count,

    COUNT(*) FILTER (WHERE b.is_reversal IS TRUE)
        AS reversal_count,

    COUNT(*) FILTER (
        WHERE b.possible_sign_inconsistency IS TRUE
    ) AS sign_inconsistency_count,

    COUNT(*) FILTER (
        WHERE b.reconciliation_status IN (
            'ledger_conflict',
            'unmatched_needs_investigation'
        )
        OR b.possible_sign_inconsistency IS TRUE
        OR NULLIF(BTRIM(COALESCE(b.review_reasons, '')), '') IS NOT NULL
    ) AS investigation_required_count,

    COUNT(*) FILTER (WHERE b.is_netted_pair IS TRUE)
        AS netted_pair_transaction_count,

    COUNT(b.debit_amount) AS debit_transaction_count,

    COUNT(b.credit_amount) AS credit_transaction_count,

    COUNT(*) FILTER (
        WHERE b.debit_amount IS NULL
          AND b.credit_amount IS NULL
    ) AS transactions_missing_both_amounts_count,

    (
        COUNT(b.debit_amount) = 0
    ) AS no_debit_records_flag,

    (
        COUNT(b.credit_amount) = 0
    ) AS no_credit_records_flag

FROM analytics.v_bank_transactions_enriched b
LEFT JOIN processed.business_profiles p
    ON b.business_id = p.business_id
GROUP BY
    b.business_id,
    p.business_name,
    p.industry,
    b.currency,
    DATE_TRUNC('month', b.transaction_date::timestamp)::date;

COMMIT;
