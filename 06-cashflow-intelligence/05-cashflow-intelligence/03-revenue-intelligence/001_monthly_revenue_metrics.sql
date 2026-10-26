
-- ============================================================
-- Orey Analytics
-- Phase 06 — Cash Flow Intelligence
-- Module 03 — Revenue Intelligence
-- File: 001_monthly_revenue_metrics.sql
--
-- Purpose:
-- Produce monthly invoice-based revenue activity metrics.
--
-- Important distinctions:
-- - Invoice amounts are not automatically accounting revenue.
-- - Amounts paid against invoices are not independently verified
--   bank collections.
-- - Source records are never modified by this view.
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_monthly_revenue_metrics AS

WITH invoice_base AS (
    SELECT
        i.source_record_id,
        i.business_id,
        bp.business_name,
        bp.accounting_basis,

        i.invoice_id,
        i.customer_id,
        i.currency,

        i.invoice_date_std AS invoice_date,
        i.due_date_std AS due_date,
        i.payment_date_std AS payment_date,

        i.invoice_status_standardized AS invoice_status,

        i.invoice_amount,
        i.amount_paid,

        GREATEST(
            COALESCE(i.invoice_amount, 0)
            - COALESCE(i.amount_paid, 0),
            0
        ) AS outstanding_amount,

        i.missing_due_date,
        i.paid_amount_mismatch,
        i.payment_before_invoice_flag,
        i.is_duplicate,
        i.reconciliation_status,
        i.reconciliation_reason,
        i.matched_bank_source_record_id,
        i.match_confidence,
        i.matched_bank_amount,
        i.amount_difference,

        CASE
            WHEN i.invoice_date_std IS NULL
                THEN NULL
            ELSE DATE_TRUNC(
                'month',
                i.invoice_date_std
            )::date
        END AS invoice_month,

        CASE
            WHEN i.payment_date_std IS NULL
                THEN NULL
            ELSE DATE_TRUNC(
                'month',
                i.payment_date_std
            )::date
        END AS payment_month

    FROM processed.invoices i

    LEFT JOIN processed.business_profiles bp
        ON bp.business_id = i.business_id
),

monthly_invoicing AS (
    SELECT
        business_id,
        business_name,
        accounting_basis,
        currency,
        invoice_month AS month_start,

        COUNT(*) AS invoice_record_count,

        COUNT(DISTINCT invoice_id)
            AS distinct_invoice_count,

        COUNT(DISTINCT customer_id)
            AS distinct_customers,

        SUM(invoice_amount)
            AS total_invoiced_amount,

        AVG(invoice_amount)
            AS average_invoice_amount,

        COUNT(*) FILTER (
            WHERE invoice_status = 'paid'
        ) AS paid_invoice_count,

        COUNT(*) FILTER (
            WHERE invoice_status = 'partially_paid'
        ) AS partially_paid_invoice_count,

        COUNT(*) FILTER (
            WHERE invoice_status = 'unpaid'
        ) AS unpaid_invoice_count,

        COUNT(*) FILTER (
            WHERE invoice_status = 'overdue'
        ) AS overdue_invoice_count,

        SUM(outstanding_amount)
            AS invoice_month_outstanding_amount,

        COUNT(*) FILTER (
            WHERE invoice_date IS NULL
        ) AS missing_invoice_date_count,

        COUNT(*) FILTER (
            WHERE invoice_amount IS NULL
        ) AS missing_invoice_amount_count,

        COUNT(*) FILTER (
            WHERE is_duplicate = TRUE
        ) AS duplicate_flagged_count,

        COUNT(*) FILTER (
            WHERE paid_amount_mismatch = TRUE
        ) AS payment_mismatch_count,

        COUNT(*) FILTER (
            WHERE payment_before_invoice_flag = TRUE
        ) AS payment_before_invoice_count,

        COUNT(*) FILTER (
            WHERE reconciliation_status = 'ledger_conflict'
        ) AS ledger_conflict_count,

        COUNT(*) FILTER (
            WHERE missing_due_date = TRUE
              AND outstanding_amount > 0
        ) AS outstanding_missing_due_date_count

    FROM invoice_base
    WHERE invoice_month IS NOT NULL
    GROUP BY
        business_id,
        business_name,
        accounting_basis,
        currency,
        invoice_month
),

monthly_collections AS (
    SELECT
        business_id,
        currency,
        payment_month AS month_start,

        COUNT(*) FILTER (
            WHERE amount_paid > 0
        ) AS invoices_with_payment_count,

        SUM(amount_paid)
            AS total_invoice_recorded_payments,

        SUM(amount_paid) FILTER (
            WHERE invoice_status = 'paid'
        ) AS payments_on_paid_invoices,

        SUM(amount_paid) FILTER (
            WHERE invoice_status = 'partially_paid'
        ) AS payments_on_partially_paid_invoices,

        COUNT(*) FILTER (
            WHERE payment_before_invoice_flag = TRUE
        ) AS payment_timing_issue_count

    FROM invoice_base
    WHERE payment_month IS NOT NULL
    GROUP BY
        business_id,
        currency,
        payment_month
)

SELECT
    m.business_id,
    m.business_name,
    m.accounting_basis,
    m.currency,
    m.month_start,

    m.invoice_record_count,
    m.distinct_invoice_count,
    m.distinct_customers,

    m.total_invoiced_amount,
    m.average_invoice_amount,

    m.paid_invoice_count,
    m.partially_paid_invoice_count,
    m.unpaid_invoice_count,
    m.overdue_invoice_count,

    m.invoice_month_outstanding_amount,

    COALESCE(
        c.invoices_with_payment_count, 0
    ) AS invoices_with_payment_count,

    COALESCE(
        c.total_invoice_recorded_payments, 0::numeric
    ) AS total_invoice_recorded_payments,

    COALESCE(
        c.payments_on_paid_invoices, 0::numeric
    ) AS payments_on_paid_invoices,

    COALESCE(
        c.payments_on_partially_paid_invoices, 0::numeric
    ) AS payments_on_partially_paid_invoices,

    CASE
        WHEN m.total_invoiced_amount > 0
        THEN ROUND(
            100.0
            * COALESCE(c.total_invoice_recorded_payments, 0)
            / m.total_invoiced_amount,
            2
        )
        ELSE NULL
    END AS recorded_payments_to_invoiced_amount_pct,

    m.missing_invoice_date_count,
    m.missing_invoice_amount_count,
    m.duplicate_flagged_count,
    m.payment_mismatch_count,
    m.payment_before_invoice_count,
    m.ledger_conflict_count,
    m.outstanding_missing_due_date_count,

    COALESCE(
        c.payment_timing_issue_count, 0
    ) AS payment_timing_issue_count,

    CASE
        WHEN m.accounting_basis = 'Cash'
            THEN 'cash_basis_invoice_activity'
        WHEN m.accounting_basis = 'Accrual'
            THEN 'accrual_basis_invoice_activity'
        ELSE 'accounting_basis_unknown'
    END AS accounting_interpretation_status,

    CURRENT_TIMESTAMP AS view_generated_at

FROM monthly_invoicing m

LEFT JOIN monthly_collections c
    ON c.business_id = m.business_id
   AND c.currency = m.currency
   AND c.month_start = m.month_start;
