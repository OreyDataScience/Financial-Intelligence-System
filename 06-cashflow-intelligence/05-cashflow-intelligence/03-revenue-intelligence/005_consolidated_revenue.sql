
-- ============================================================
-- Orey Analytics
-- Phase 06 — Cash Flow Intelligence
-- Module 03 — Revenue Intelligence
-- File: 005_consolidated_revenue.sql
--
-- Purpose:
-- Consolidate revenue activity, trends, customer concentration,
-- and data-quality indicators into one monthly business view.
--
-- Important:
-- Invoice-based activity is not automatically verified revenue
-- or confirmed bank collections.
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_consolidated_revenue AS

WITH monthly_quality AS (
    SELECT
        business_id,
        currency,
        DATE_TRUNC(
            'month',
            standardized_invoice_date
        )::date AS month_start,

        COUNT(*) AS quality_checked_invoice_count,

        COUNT(*) FILTER (
            WHERE has_revenue_data_quality_issue = TRUE
        ) AS flagged_invoice_count,

        COUNT(*) FILTER (
            WHERE missing_customer_identity = TRUE
        ) AS missing_customer_identity_count,

        COUNT(*) FILTER (
            WHERE missing_standardized_invoice_date = TRUE
        ) AS missing_invoice_date_count,

        COUNT(*) FILTER (
            WHERE missing_invoice_amount = TRUE
        ) AS missing_invoice_amount_count,

        COUNT(*) FILTER (
            WHERE missing_amount_paid = TRUE
        ) AS missing_amount_paid_count,

        COUNT(*) FILTER (
            WHERE payment_exceeds_invoice_amount = TRUE
        ) AS payment_exceeds_invoice_count,

        COUNT(*) FILTER (
            WHERE due_date_before_invoice = TRUE
        ) AS due_date_before_invoice_count,

        COUNT(*) FILTER (
            WHERE paid_status_with_remaining_balance = TRUE
        ) AS paid_status_balance_mismatch_count

    FROM analytics.v_revenue_quality
    WHERE standardized_invoice_date IS NOT NULL
    GROUP BY
        business_id,
        currency,
        DATE_TRUNC(
            'month',
            standardized_invoice_date
        )::date
)

SELECT
    m.business_id,
    m.business_name,
    m.accounting_basis,
    m.currency,
    m.month_start,

    -- Monthly invoice activity
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

    -- Payment activity by payment date
    m.invoices_with_payment_count,
    m.total_invoice_recorded_payments,
    m.payments_on_paid_invoices,
    m.payments_on_partially_paid_invoices,
    m.recorded_payments_to_invoiced_amount_pct,

    -- Trends
    t.previous_month_invoiced_amount,
    t.invoiced_amount_change,
    t.invoiced_amount_change_pct,
    t.previous_month_recorded_payments,
    t.recorded_payments_change,
    t.recorded_payments_change_pct,
    t.has_consecutive_month_history,
    t.invoiced_amount_3_month_sum,
    t.invoiced_amount_3_month_average,
    t.recorded_payments_3_month_sum,
    t.has_3_month_row_window,
    t.invoiced_decline_months_in_3_month_window,
    t.invoiced_amount_declined,
    t.invoicing_declined_for_3_month_window,
    t.trend_comparison_status,

    -- Customer concentration
    c.identified_customer_groups,
    c.unidentified_customer_groups,
    c.top_customer_invoiced_amount,
    c.top_customer_share_pct,
    c.top_3_identified_customer_share_pct,
    c.identified_customer_hhi_10000_scale,
    c.identified_customer_invoiced_amount,
    c.unidentified_customer_invoiced_amount,
    c.concentration_data_status,

    -- Data quality
    COALESCE(q.quality_checked_invoice_count, 0)
        AS quality_checked_invoice_count,

    COALESCE(q.flagged_invoice_count, 0)
        AS flagged_invoice_count,

    COALESCE(q.missing_customer_identity_count, 0)
        AS missing_customer_identity_count,

    COALESCE(q.missing_invoice_date_count, 0)
        AS missing_invoice_date_count,

    COALESCE(q.missing_invoice_amount_count, 0)
        AS missing_invoice_amount_count,

    COALESCE(q.missing_amount_paid_count, 0)
        AS missing_amount_paid_count,

    COALESCE(q.payment_exceeds_invoice_count, 0)
        AS payment_exceeds_invoice_count,

    COALESCE(q.due_date_before_invoice_count, 0)
        AS due_date_before_invoice_count,

    COALESCE(q.paid_status_balance_mismatch_count, 0)
        AS paid_status_balance_mismatch_count,

    m.accounting_interpretation_status,

    CASE
        WHEN COALESCE(q.flagged_invoice_count, 0) > 0
            THEN 'revenue_data_quality_review_required'
        ELSE 'no_flagged_quality_issues_in_monthly_scope'
    END AS revenue_quality_status,

    CURRENT_TIMESTAMP AS view_generated_at

FROM analytics.v_monthly_revenue_metrics m

LEFT JOIN analytics.v_revenue_trends t
    ON t.business_id = m.business_id
   AND t.currency = m.currency
   AND t.month_start = m.month_start

LEFT JOIN analytics.v_revenue_concentration c
    ON c.business_id = m.business_id
   AND c.currency = m.currency
   AND c.month_start = m.month_start

LEFT JOIN monthly_quality q
    ON q.business_id = m.business_id
   AND q.currency = m.currency
   AND q.month_start = m.month_start;
