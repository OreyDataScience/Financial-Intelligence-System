
-- ============================================================
-- Orey Analytics
-- Phase 06 — Cash Flow Intelligence
-- Module 02 — Liquidity
-- File: 004_liquidity_coverage.sql
--
-- Purpose:
-- Consolidate receivables, payables and bank-balance evidence
-- into business-level liquidity exposure indicators.
--
-- Important:
-- Receivables are not guaranteed cash inflows.
-- Payables are not necessarily immediate cash outflows.
-- Recorded bank balances are not treated as verified cash.
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_liquidity_coverage AS

WITH receivables AS (
    SELECT
        business_id,
        currency,

        COUNT(*) FILTER (
            WHERE status_adjusted_outstanding_amount > 0
        ) AS open_invoice_count,

        COUNT(*) FILTER (
            WHERE is_past_due = TRUE
              AND status_adjusted_outstanding_amount > 0
        ) AS overdue_invoice_count,

        COUNT(*) FILTER (
            WHERE missing_due_date_with_outstanding = TRUE
              AND status_adjusted_outstanding_amount > 0
        ) AS outstanding_invoices_missing_due_date_count,

        SUM(status_adjusted_outstanding_amount)
            AS total_outstanding_receivables,

        SUM(status_adjusted_outstanding_amount) FILTER (
            WHERE is_past_due = TRUE
        ) AS overdue_receivables

    FROM analytics.v_receivables_liquidity
    GROUP BY business_id, currency
),

payables AS (
    SELECT
        business_id,
        currency,

        COUNT(*) FILTER (
            WHERE status_adjusted_outstanding_amount > 0
        ) AS open_bill_count,

        COUNT(*) FILTER (
            WHERE is_past_due = TRUE
              AND status_adjusted_outstanding_amount > 0
        ) AS overdue_bill_count,

        SUM(status_adjusted_outstanding_amount)
            AS total_outstanding_payables,

        SUM(status_adjusted_outstanding_amount) FILTER (
            WHERE is_past_due = TRUE
        ) AS overdue_payables

    FROM analytics.v_payables_liquidity
    GROUP BY business_id, currency
),

business_currency_keys AS (
    SELECT business_id, currency
    FROM analytics.v_bank_balance_monitoring

    UNION

    SELECT business_id, currency
    FROM receivables

    UNION

    SELECT business_id, currency
    FROM payables
)

SELECT
    k.business_id,
    bp.business_name,
    k.currency,

    bb.bank_name,
    bb.account_id,

    bb.latest_recorded_balance,
    bb.latest_balance_source_record_id,
    bb.latest_balance_transaction_date,
    bb.latest_balance_posting_date,
    bb.latest_balance_reconciliation_status,

    bb.balance_coverage_pct,
    bb.ledger_conflict_count,
    bb.unresolved_transaction_count,
    bb.reversal_count,
    bb.balance_evidence_status,
    bb.balance_history_verified,

    COALESCE(r.open_invoice_count, 0)
        AS open_invoice_count,

    COALESCE(r.overdue_invoice_count, 0)
        AS overdue_invoice_count,

    COALESCE(
        r.outstanding_invoices_missing_due_date_count, 0
    ) AS outstanding_invoices_missing_due_date_count,

    COALESCE(r.total_outstanding_receivables, 0::numeric)
        AS total_outstanding_receivables,

    COALESCE(r.overdue_receivables, 0::numeric)
        AS overdue_receivables,

    COALESCE(p.open_bill_count, 0)
        AS open_bill_count,

    COALESCE(p.overdue_bill_count, 0)
        AS overdue_bill_count,

    COALESCE(p.total_outstanding_payables, 0::numeric)
        AS total_outstanding_payables,

    COALESCE(p.overdue_payables, 0::numeric)
        AS overdue_payables,

    CASE
        WHEN COALESCE(p.total_outstanding_payables, 0) > 0
        THEN ROUND(
            COALESCE(r.total_outstanding_receivables, 0)
            / p.total_outstanding_payables,
            4
        )
        ELSE NULL
    END AS receivables_to_payables_coverage_ratio,

    COALESCE(r.total_outstanding_receivables, 0::numeric)
      - COALESCE(p.total_outstanding_payables, 0::numeric)
        AS net_receivables_after_payables,

    CASE
        WHEN bb.business_id IS NULL
            THEN 'no_bank_balance_record'
        WHEN bb.balance_history_verified = FALSE
            THEN 'bank_balance_not_verified'
        ELSE 'bank_balance_evidence_available'
    END AS cash_evidence_status,

    CURRENT_TIMESTAMP AS view_generated_at

FROM business_currency_keys k

LEFT JOIN processed.business_profiles bp
    ON bp.business_id = k.business_id

LEFT JOIN analytics.v_bank_balance_monitoring bb
    ON bb.business_id = k.business_id
   AND bb.currency = k.currency

LEFT JOIN receivables r
    ON r.business_id = k.business_id
   AND r.currency = k.currency

LEFT JOIN payables p
    ON p.business_id = k.business_id
   AND p.currency = k.currency;
