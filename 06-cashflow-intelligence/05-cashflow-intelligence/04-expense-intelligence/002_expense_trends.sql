
-- ============================================================
-- Orey Analytics
-- Phase 06 — Cash Flow Intelligence
-- Module 04: Expense Intelligence
-- Script 002: Expense Trends
--
-- Purpose:
-- Calculate monthly changes and rolling three-month patterns
-- in supplier-bill activity.
--
-- Important:
-- These are supplier-bill activity measures, not confirmed
-- accounting expenses or verified bank outflows.
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_expense_trends AS

WITH base AS (
    SELECT
        e.*,

        LAG(e.month_start) OVER (
            PARTITION BY e.business_id, e.currency
            ORDER BY e.month_start
        ) AS previous_observed_month,

        LAG(e.total_supplier_bill_amount) OVER (
            PARTITION BY e.business_id, e.currency
            ORDER BY e.month_start
        ) AS previous_observed_bill_amount,

        LAG(e.non_duplicate_supplier_bill_amount) OVER (
            PARTITION BY e.business_id, e.currency
            ORDER BY e.month_start
        ) AS previous_observed_non_duplicate_bill_amount,

        LAG(e.total_amount_paid_recorded_on_bills) OVER (
            PARTITION BY e.business_id, e.currency
            ORDER BY e.month_start
        ) AS previous_observed_recorded_paid_amount

    FROM analytics.v_monthly_expense_metrics AS e
),

monthly_changes AS (
    SELECT
        *,

        CASE
            WHEN previous_observed_month =
                 (month_start - INTERVAL '1 month')::date
            THEN previous_observed_bill_amount
            ELSE NULL
        END AS previous_calendar_month_bill_amount,

        CASE
            WHEN previous_observed_month =
                 (month_start - INTERVAL '1 month')::date
            THEN previous_observed_non_duplicate_bill_amount
            ELSE NULL
        END AS previous_calendar_month_non_duplicate_bill_amount,

        CASE
            WHEN previous_observed_month =
                 (month_start - INTERVAL '1 month')::date
            THEN previous_observed_recorded_paid_amount
            ELSE NULL
        END AS previous_calendar_month_recorded_paid_amount

    FROM base
),

rolling AS (
    SELECT
        *,

        COUNT(total_supplier_bill_amount) OVER (
            PARTITION BY business_id, currency
            ORDER BY month_start
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ) AS observed_months_in_rolling_window,

        SUM(total_supplier_bill_amount) OVER (
            PARTITION BY business_id, currency
            ORDER BY month_start
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ) AS rolling_3_observed_month_bill_amount,

        SUM(non_duplicate_supplier_bill_amount) OVER (
            PARTITION BY business_id, currency
            ORDER BY month_start
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ) AS rolling_3_observed_month_non_duplicate_bill_amount,

        AVG(total_supplier_bill_amount) OVER (
            PARTITION BY business_id, currency
            ORDER BY month_start
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ) AS average_bill_amount_per_observed_month_3_rows

    FROM monthly_changes
)

SELECT
    business_id,
    business_name,
    currency,
    month_start,

    supplier_bill_count,
    total_supplier_bill_amount,
    non_duplicate_supplier_bill_amount,
    total_amount_paid_recorded_on_bills,
    total_indicative_outstanding_amount,

    previous_observed_month,
    previous_calendar_month_bill_amount,
    previous_calendar_month_non_duplicate_bill_amount,
    previous_calendar_month_recorded_paid_amount,

    total_supplier_bill_amount
        - previous_calendar_month_bill_amount
        AS month_over_month_bill_amount_change,

    CASE
        WHEN previous_calendar_month_bill_amount IS NOT NULL
         AND previous_calendar_month_bill_amount <> 0
        THEN (
            (total_supplier_bill_amount
                - previous_calendar_month_bill_amount)
            / ABS(previous_calendar_month_bill_amount)
        ) * 100
        ELSE NULL
    END AS month_over_month_bill_amount_change_pct,

    non_duplicate_supplier_bill_amount
        - previous_calendar_month_non_duplicate_bill_amount
        AS month_over_month_non_duplicate_bill_amount_change,

    CASE
        WHEN previous_calendar_month_non_duplicate_bill_amount IS NOT NULL
         AND previous_calendar_month_non_duplicate_bill_amount <> 0
        THEN (
            (non_duplicate_supplier_bill_amount
                - previous_calendar_month_non_duplicate_bill_amount)
            / ABS(previous_calendar_month_non_duplicate_bill_amount)
        ) * 100
        ELSE NULL
    END AS month_over_month_non_duplicate_bill_amount_change_pct,

    observed_months_in_rolling_window,
    rolling_3_observed_month_bill_amount,
    rolling_3_observed_month_non_duplicate_bill_amount,

    average_bill_amount_per_observed_month_3_rows,

    CASE
        WHEN observed_months_in_rolling_window = 3
        THEN TRUE
        ELSE FALSE
    END AS rolling_window_has_3_observed_rows,

    CASE
        WHEN previous_calendar_month_bill_amount IS NULL
        THEN TRUE
        ELSE FALSE
    END AS month_over_month_comparison_unavailable,

    FALSE AS accounting_expenses_verified,
    FALSE AS bank_outflows_verified,

    CURRENT_TIMESTAMP AS view_generated_at

FROM rolling;
