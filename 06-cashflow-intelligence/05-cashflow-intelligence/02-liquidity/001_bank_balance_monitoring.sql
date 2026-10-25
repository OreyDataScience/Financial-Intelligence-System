
-- ============================================================
-- Orey Analytics
-- Phase 06 — Cash Flow Intelligence
-- Module 02 — Liquidity
-- File: 001_bank_balance_monitoring.sql
--
-- Purpose:
-- Provide account-level bank balance evidence and data-quality
-- indicators for downstream liquidity analysis.
--
-- Design principles:
--   1. Preserve source transactions and recorded balances.
--   2. Never sum balance snapshots as if they were cash flows.
--   3. Select the latest available balance observation per account.
--   4. Expose balance coverage and reconciliation warnings.
--   5. Do not claim that the latest observation is a verified
--      current bank balance.
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_bank_balance_monitoring AS

WITH account_summary AS (
    SELECT
        business_id,
        bank_name,
        account_id,
        currency,

        COUNT(*) AS total_transactions,

        COUNT(*) FILTER (
            WHERE balance_after_transaction IS NOT NULL
        ) AS transactions_with_balance,

        COUNT(*) FILTER (
            WHERE balance_after_transaction IS NULL
        ) AS transactions_missing_balance,

        COUNT(*) FILTER (
            WHERE reconciliation_status = 'ledger_conflict'
        ) AS ledger_conflict_count,

        COUNT(*) FILTER (
            WHERE reconciliation_status = 'unmatched_needs_investigation'
        ) AS unresolved_transaction_count,

        COUNT(*) FILTER (
            WHERE is_reversal = TRUE
        ) AS reversal_count,

        MIN(transaction_date_std) AS first_transaction_date,
        MAX(transaction_date_std) AS last_transaction_date,

        ROUND(
            100.0 * COUNT(*) FILTER (
                WHERE balance_after_transaction IS NOT NULL
            ) / NULLIF(COUNT(*), 0),
            2
        ) AS balance_coverage_pct

    FROM processed.bank_transactions

    GROUP BY
        business_id,
        bank_name,
        account_id,
        currency
),

ranked_balance_observations AS (
    SELECT
        business_id,
        bank_name,
        account_id,
        currency,
        source_record_id,
        transaction_date_std,
        posting_date_std,
        balance_after_transaction,
        reconciliation_status,

        ROW_NUMBER() OVER (
            PARTITION BY business_id, bank_name, account_id, currency
            ORDER BY
                transaction_date_std DESC NULLS LAST,
                posting_date_std DESC NULLS LAST,
                source_record_id DESC
        ) AS observation_rank

    FROM processed.bank_transactions

    WHERE balance_after_transaction IS NOT NULL
)

SELECT
    s.business_id,
    bp.business_name,
    s.bank_name,
    s.account_id,
    s.currency,

    r.source_record_id AS latest_balance_source_record_id,
    r.transaction_date_std AS latest_balance_transaction_date,
    r.posting_date_std AS latest_balance_posting_date,
    r.balance_after_transaction AS latest_recorded_balance,
    r.reconciliation_status AS latest_balance_reconciliation_status,

    s.total_transactions,
    s.transactions_with_balance,
    s.transactions_missing_balance,
    s.balance_coverage_pct,

    s.ledger_conflict_count,
    s.unresolved_transaction_count,
    s.reversal_count,

    s.first_transaction_date,
    s.last_transaction_date,

    CASE
        WHEN r.balance_after_transaction IS NULL
            THEN 'no_balance_observation'

        WHEN s.balance_coverage_pct < 80
            THEN 'low_balance_coverage'

        WHEN s.ledger_conflict_count > 0
            THEN 'balance_evidence_has_ledger_conflicts'

        ELSE 'balance_observation_available_review_required'
    END AS balance_evidence_status,

    FALSE AS balance_history_verified,

    CURRENT_TIMESTAMP AS view_generated_at

FROM account_summary s

LEFT JOIN ranked_balance_observations r
    ON r.business_id = s.business_id
    AND r.bank_name = s.bank_name
    AND r.account_id = s.account_id
    AND r.currency = s.currency
    AND r.observation_rank = 1

LEFT JOIN processed.business_profiles bp
    ON bp.business_id = s.business_id;
