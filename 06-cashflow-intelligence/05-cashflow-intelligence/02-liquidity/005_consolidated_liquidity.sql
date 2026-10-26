
-- ============================================================
-- Orey Analytics
-- Phase 06 — Cash Flow Intelligence
-- Module 02 — Liquidity
-- File: 005_consolidated_liquidity.sql
--
-- Purpose:
-- Provide a consolidated business-level liquidity view.
--
-- Design principles:
-- - Preserve source-level data quality warnings.
-- - Do not treat unverified bank balances as confirmed cash.
-- - Do not treat receivables as guaranteed inflows.
-- - Do not treat all payables as immediate outflows.
-- - Keep liquidity exposure measures distinct from cash balance.
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_consolidated_liquidity AS

SELECT
    lc.business_id,
    lc.business_name,
    lc.currency,

    -- Bank-balance evidence
    lc.bank_name,
    lc.account_id,
    lc.latest_recorded_balance,
    lc.latest_balance_transaction_date,
    lc.latest_balance_posting_date,
    lc.latest_balance_reconciliation_status,
    lc.balance_coverage_pct,
    lc.ledger_conflict_count,
    lc.unresolved_transaction_count,
    lc.reversal_count,
    lc.balance_evidence_status,
    lc.balance_history_verified,
    lc.cash_evidence_status,

    -- Receivables
    lc.open_invoice_count,
    lc.overdue_invoice_count,
    lc.outstanding_invoices_missing_due_date_count,
    lc.total_outstanding_receivables,
    lc.overdue_receivables,

    -- Payables
    lc.open_bill_count,
    lc.overdue_bill_count,
    lc.total_outstanding_payables,
    lc.overdue_payables,

    -- Exposure indicators
    lc.receivables_to_payables_coverage_ratio,
    lc.net_receivables_after_payables,

    -- Conservative interpretation
    CASE
        WHEN lc.balance_history_verified = FALSE
            THEN 'cash_position_not_verified'
        WHEN lc.latest_recorded_balance IS NULL
            THEN 'cash_balance_unavailable'
        ELSE 'recorded_balance_requires_interpretation'
    END AS liquidity_interpretation_status,

    CASE
        WHEN lc.outstanding_invoices_missing_due_date_count > 0
            THEN 'receivables_include_missing_due_dates'
        ELSE 'receivables_due_dates_available_for_outstanding_items'
    END AS receivables_timing_status,

    CURRENT_TIMESTAMP AS view_generated_at

FROM analytics.v_liquidity_coverage lc;
