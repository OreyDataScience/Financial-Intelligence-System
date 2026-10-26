
-- ============================================================
-- Orey Analytics
-- Phase 06 — Cash Flow Intelligence
-- Module 03 — Revenue Intelligence
-- File: 002_revenue_trends.sql
--
-- Purpose:
-- Measure invoice activity and recorded-payment trends.
--
-- Note:
-- These are trends in invoice records, not verified bank cash
-- collections or guaranteed accounting revenue.
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_revenue_trends AS

WITH monthly AS (
    SELECT
        business_id,
        business_name,
        accounting_basis,
        currency,
        month_start,

        total_invoiced_amount,
        total_invoice_recorded_payments,
        invoice_record_count,
        distinct_customers,
        invoice_month_outstanding_amount,

        LAG(month_start) OVER (
            PARTITION BY business_id, currency
            ORDER BY month_start
        ) AS previous_month_start,

        LAG(total_invoiced_amount) OVER (
            PARTITION BY business_id, currency
            ORDER BY month_start
        ) AS previous_month_invoiced_amount,

        LAG(total_invoice_recorded_payments) OVER (
            PARTITION BY business_id, currency
            ORDER BY month_start
        ) AS previous_month_recorded_payments

    FROM analytics.v_monthly_revenue_metrics
),

changes AS (
    SELECT
        *,

        total_invoiced_amount
          - previous_month_invoiced_amount
            AS invoiced_amount_change,

        CASE
            WHEN previous_month_start =
                 (month_start - INTERVAL '1 month')::date
             AND previous_month_invoiced_amount <> 0
            THEN ROUND(
                100.0
                * (
                    total_invoiced_amount
                    - previous_month_invoiced_amount
                )
                / ABS(previous_month_invoiced_amount),
                2
            )
            ELSE NULL
        END AS invoiced_amount_change_pct,

        total_invoice_recorded_payments
          - previous_month_recorded_payments
            AS recorded_payments_change,

        CASE
            WHEN previous_month_start =
                 (month_start - INTERVAL '1 month')::date
             AND previous_month_recorded_payments <> 0
            THEN ROUND(
                100.0
                * (
                    total_invoice_recorded_payments
                    - previous_month_recorded_payments
                )
                / ABS(previous_month_recorded_payments),
                2
            )
            ELSE NULL
        END AS recorded_payments_change_pct,

        CASE
            WHEN previous_month_start =
                 (month_start - INTERVAL '1 month')::date
            THEN TRUE
            ELSE FALSE
        END AS has_consecutive_month_history

    FROM monthly
),

rolling AS (
    SELECT
        *,

        COUNT(*) OVER (
            PARTITION BY business_id, currency
            ORDER BY month_start
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ) AS rows_in_3_month_window,

        SUM(total_invoiced_amount) OVER (
            PARTITION BY business_id, currency
            ORDER BY month_start
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ) AS invoiced_amount_3_month_sum,

        AVG(total_invoiced_amount) OVER (
            PARTITION BY business_id, currency
            ORDER BY month_start
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ) AS invoiced_amount_3_month_average,

        SUM(total_invoice_recorded_payments) OVER (
            PARTITION BY business_id, currency
            ORDER BY month_start
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ) AS recorded_payments_3_month_sum,

        COUNT(*) FILTER (
            WHERE has_consecutive_month_history
              AND invoiced_amount_change < 0
        ) OVER (
            PARTITION BY business_id, currency
            ORDER BY month_start
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ) AS invoiced_decline_months_in_3_month_window

    FROM changes
),

streaks AS (
    SELECT
        *,

        CASE
            WHEN invoiced_amount_change < 0
             AND has_consecutive_month_history
            THEN ROW_NUMBER() OVER (
                PARTITION BY business_id, currency
                ORDER BY month_start
            )
              - ROW_NUMBER() OVER (
                    PARTITION BY business_id, currency,
                        CASE
                            WHEN invoiced_amount_change < 0
                             AND has_consecutive_month_history
                            THEN 1
                            ELSE 0
                        END
                    ORDER BY month_start
                )
            ELSE NULL
        END AS decline_streak_group

    FROM rolling
)

SELECT
    business_id,
    business_name,
    accounting_basis,
    currency,
    month_start,

    total_invoiced_amount,
    previous_month_invoiced_amount,
    invoiced_amount_change,
    invoiced_amount_change_pct,

    total_invoice_recorded_payments,
    previous_month_recorded_payments,
    recorded_payments_change,
    recorded_payments_change_pct,

    invoice_record_count,
    distinct_customers,
    invoice_month_outstanding_amount,

    has_consecutive_month_history,

    invoiced_amount_3_month_sum,
    invoiced_amount_3_month_average,
    recorded_payments_3_month_sum,

    rows_in_3_month_window = 3
        AS has_3_month_row_window,

    invoiced_decline_months_in_3_month_window,

    CASE
        WHEN has_consecutive_month_history
         AND invoiced_amount_change < 0
        THEN TRUE
        ELSE FALSE
    END AS invoiced_amount_declined,

    CASE
        WHEN has_consecutive_month_history
         AND invoiced_amount_change < 0
         AND invoiced_decline_months_in_3_month_window = 3
        THEN TRUE
        ELSE FALSE
    END AS invoicing_declined_for_3_month_window,

    CASE
        WHEN previous_month_start IS NULL
            THEN 'no_previous_observation'
        WHEN has_consecutive_month_history = FALSE
            THEN 'gap_in_monthly_observations'
        WHEN previous_month_invoiced_amount = 0
            THEN 'previous_invoiced_amount_zero'
        ELSE 'month_over_month_comparison_available'
    END AS trend_comparison_status,

    CURRENT_TIMESTAMP AS view_generated_at

FROM streaks;
