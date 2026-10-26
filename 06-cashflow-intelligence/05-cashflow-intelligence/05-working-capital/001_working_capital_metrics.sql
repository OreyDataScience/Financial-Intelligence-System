
-- ============================================================
-- Orey Analytics
-- Phase 06 — Cash Flow Intelligence
-- Module 05 — Working Capital
-- Script 001: Core Working Capital Metrics
--
-- Purpose:
-- Aggregate recorded receivables and payables by business
-- and currency, while preserving visibility of data-quality
-- issues and duplicate-flagged amounts.
--
-- Important:
-- These are derived invoice/bill metrics, not verified
-- accounting balances or confirmed cash availability.
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_working_capital_metrics AS

WITH receivables AS (
    SELECT
        business_id,
        currency,
        MAX(business_name) AS business_name,

        COUNT(*) AS invoice_record_count,

        COUNT(*) FILTER (
            WHERE status_adjusted_outstanding_amount > 0
        ) AS open_invoice_count,

        COUNT(*) FILTER (
            WHERE is_past_due IS TRUE
              AND status_adjusted_outstanding_amount > 0
        ) AS overdue_invoice_count,

        COUNT(*) FILTER (
            WHERE missing_due_date_with_outstanding IS TRUE
              AND status_adjusted_outstanding_amount > 0
        ) AS open_invoices_missing_due_date_count,

        COUNT(*) FILTER (
            WHERE is_duplicate IS TRUE
        ) AS duplicate_flagged_invoice_count,

        COUNT(*) FILTER (
            WHERE paid_amount_mismatch IS TRUE
        ) AS invoice_payment_mismatch_count,

        COUNT(*) FILTER (
            WHERE reconciliation_status = 'ledger_conflict'
        ) AS invoice_ledger_conflict_count,

        COUNT(*) FILTER (
            WHERE payment_before_invoice_flag IS TRUE
        ) AS payment_before_invoice_count,

        SUM(invoice_amount) AS recorded_invoice_amount,

        SUM(amount_paid) AS recorded_invoice_amount_paid,

        SUM(
            COALESCE(status_adjusted_outstanding_amount, 0)
        ) AS recorded_outstanding_receivables,

        SUM(
            COALESCE(status_adjusted_outstanding_amount, 0)
        ) FILTER (
            WHERE is_past_due IS TRUE
              AND status_adjusted_outstanding_amount > 0
        ) AS recorded_overdue_receivables,

        SUM(
            COALESCE(status_adjusted_outstanding_amount, 0)
        ) FILTER (
            WHERE is_duplicate IS TRUE
        ) AS duplicate_flagged_receivables_exposure,

        SUM(
            COALESCE(status_adjusted_outstanding_amount, 0)
        ) FILTER (
            WHERE paid_amount_mismatch IS TRUE
        ) AS payment_mismatch_receivables_exposure,

        SUM(
            COALESCE(status_adjusted_outstanding_amount, 0)
        ) FILTER (
            WHERE reconciliation_status = 'ledger_conflict'
        ) AS ledger_conflict_receivables_exposure

    FROM analytics.v_receivables_liquidity
    GROUP BY business_id, currency
),

payables AS (
    SELECT
        business_id,
        currency,
        MAX(business_name) AS business_name,

        COUNT(*) AS bill_record_count,

        COUNT(*) FILTER (
            WHERE status_adjusted_outstanding_amount > 0
        ) AS open_bill_count,

        COUNT(*) FILTER (
            WHERE is_past_due IS TRUE
              AND status_adjusted_outstanding_amount > 0
        ) AS overdue_bill_count,

        COUNT(*) FILTER (
            WHERE missing_due_date_with_outstanding IS TRUE
              AND status_adjusted_outstanding_amount > 0
        ) AS open_bills_missing_due_date_count,

        COUNT(*) FILTER (
            WHERE is_duplicate IS TRUE
        ) AS duplicate_flagged_bill_count,

        COUNT(*) FILTER (
            WHERE paid_amount_mismatch IS TRUE
        ) AS bill_payment_mismatch_count,

        COUNT(*) FILTER (
            WHERE reconciliation_status = 'ledger_conflict'
        ) AS bill_ledger_conflict_count,

        COUNT(*) FILTER (
            WHERE payment_before_bill_flag IS TRUE
        ) AS payment_before_bill_count,

        SUM(bill_amount) AS recorded_bill_amount,

        SUM(amount_paid) AS recorded_bill_amount_paid,

        SUM(
            COALESCE(status_adjusted_outstanding_amount, 0)
        ) AS recorded_outstanding_payables,

        SUM(
            COALESCE(status_adjusted_outstanding_amount, 0)
        ) FILTER (
            WHERE is_past_due IS TRUE
              AND status_adjusted_outstanding_amount > 0
        ) AS recorded_overdue_payables,

        SUM(
            COALESCE(status_adjusted_outstanding_amount, 0)
        ) FILTER (
            WHERE is_duplicate IS TRUE
        ) AS duplicate_flagged_payables_exposure,

        SUM(
            COALESCE(status_adjusted_outstanding_amount, 0)
        ) FILTER (
            WHERE paid_amount_mismatch IS TRUE
        ) AS payment_mismatch_payables_exposure,

        SUM(
            COALESCE(status_adjusted_outstanding_amount, 0)
        ) FILTER (
            WHERE reconciliation_status = 'ledger_conflict'
        ) AS ledger_conflict_payables_exposure

    FROM analytics.v_payables_liquidity
    GROUP BY business_id, currency
),

business_currency_keys AS (
    SELECT business_id, currency FROM receivables

    UNION

    SELECT business_id, currency FROM payables
)

SELECT
    k.business_id,
    COALESCE(r.business_name, p.business_name) AS business_name,
    k.currency,

    -- Receivables
    COALESCE(r.invoice_record_count, 0)
        AS invoice_record_count,

    COALESCE(r.open_invoice_count, 0)
        AS open_invoice_count,

    COALESCE(r.overdue_invoice_count, 0)
        AS overdue_invoice_count,

    COALESCE(r.open_invoices_missing_due_date_count, 0)
        AS open_invoices_missing_due_date_count,

    COALESCE(r.duplicate_flagged_invoice_count, 0)
        AS duplicate_flagged_invoice_count,

    COALESCE(r.invoice_payment_mismatch_count, 0)
        AS invoice_payment_mismatch_count,

    COALESCE(r.invoice_ledger_conflict_count, 0)
        AS invoice_ledger_conflict_count,

    COALESCE(r.payment_before_invoice_count, 0)
        AS payment_before_invoice_count,

    COALESCE(r.recorded_invoice_amount, 0)
        AS recorded_invoice_amount,

    COALESCE(r.recorded_invoice_amount_paid, 0)
        AS recorded_invoice_amount_paid,

    COALESCE(r.recorded_outstanding_receivables, 0)
        AS recorded_outstanding_receivables,

    COALESCE(r.recorded_overdue_receivables, 0)
        AS recorded_overdue_receivables,

    COALESCE(r.duplicate_flagged_receivables_exposure, 0)
        AS duplicate_flagged_receivables_exposure,

    COALESCE(r.payment_mismatch_receivables_exposure, 0)
        AS payment_mismatch_receivables_exposure,

    COALESCE(r.ledger_conflict_receivables_exposure, 0)
        AS ledger_conflict_receivables_exposure,

    -- Payables
    COALESCE(p.bill_record_count, 0)
        AS bill_record_count,

    COALESCE(p.open_bill_count, 0)
        AS open_bill_count,

    COALESCE(p.overdue_bill_count, 0)
        AS overdue_bill_count,

    COALESCE(p.open_bills_missing_due_date_count, 0)
        AS open_bills_missing_due_date_count,

    COALESCE(p.duplicate_flagged_bill_count, 0)
        AS duplicate_flagged_bill_count,

    COALESCE(p.bill_payment_mismatch_count, 0)
        AS bill_payment_mismatch_count,

    COALESCE(p.bill_ledger_conflict_count, 0)
        AS bill_ledger_conflict_count,

    COALESCE(p.payment_before_bill_count, 0)
        AS payment_before_bill_count,

    COALESCE(p.recorded_bill_amount, 0)
        AS recorded_bill_amount,

    COALESCE(p.recorded_bill_amount_paid, 0)
        AS recorded_bill_amount_paid,

    COALESCE(p.recorded_outstanding_payables, 0)
        AS recorded_outstanding_payables,

    COALESCE(p.recorded_overdue_payables, 0)
        AS recorded_overdue_payables,

    COALESCE(p.duplicate_flagged_payables_exposure, 0)
        AS duplicate_flagged_payables_exposure,

    COALESCE(p.payment_mismatch_payables_exposure, 0)
        AS payment_mismatch_payables_exposure,

    COALESCE(p.ledger_conflict_payables_exposure, 0)
        AS ledger_conflict_payables_exposure,

    -- Derived comparison; not verified accounting working capital.
    COALESCE(r.recorded_outstanding_receivables, 0)
        - COALESCE(p.recorded_outstanding_payables, 0)
        AS net_recorded_receivables_after_payables,

    CASE
        WHEN COALESCE(p.recorded_outstanding_payables, 0) > 0
        THEN ROUND(
            COALESCE(r.recorded_outstanding_receivables, 0)
            / p.recorded_outstanding_payables,
            4
        )
        ELSE NULL
    END AS receivables_to_payables_ratio,

    CURRENT_TIMESTAMP AS view_generated_at

FROM business_currency_keys k

LEFT JOIN receivables r
    ON r.business_id = k.business_id
   AND r.currency = k.currency

LEFT JOIN payables p
    ON p.business_id = k.business_id
   AND p.currency = k.currency;
