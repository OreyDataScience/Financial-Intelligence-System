
-- ============================================================
-- Orey Analytics
-- Phase 06 — Cash Flow Intelligence
-- Module 07 — Profitability
--
-- Script: 003_monthly_profitability_trends.sql
--
-- Purpose:
-- Analyse changes in provisional invoice-to-bill differences.
-- Distinguish calendar-month comparisons from observed-row
-- rolling windows.
--
-- Dependency:
--   analytics.v_monthly_profitability_evidence
--
-- Interpretation:
--   Invoice-to-bill differences are not verified profit.
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_monthly_profitability_trends AS

WITH monthly AS (
    SELECT
        p.*,

        LAG(p.month_start) OVER (
            PARTITION BY p.business_id, p.currency
            ORDER BY p.month_start
        ) AS previous_observed_month,

        LAG(p.provisional_invoice_to_bill_difference) OVER (
            PARTITION BY p.business_id, p.currency
            ORDER BY p.month_start
        ) AS previous_observed_difference,

        AVG(p.provisional_invoice_to_bill_difference) OVER (
            PARTITION BY p.business_id, p.currency
            ORDER BY p.month_start
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ) AS rolling_3_observed_row_average,

        COUNT(p.provisional_invoice_to_bill_difference) OVER (
            PARTITION BY p.business_id, p.currency
            ORDER BY p.month_start
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ) AS rolling_3_observed_row_value_count,

        LAG(p.month_start, 2) OVER (
            PARTITION BY p.business_id, p.currency
            ORDER BY p.month_start
        ) AS third_observed_month_start

    FROM analytics.v_monthly_profitability_evidence AS p
),

calendar_checks AS (
    SELECT
        m.*,

        (
            m.previous_observed_month =
                (m.month_start - INTERVAL '1 month')::date
        ) AS has_previous_calendar_month,

        (
            m.third_observed_month_start =
                (m.month_start - INTERVAL '2 months')::date
            AND m.previous_observed_month =
                (m.month_start - INTERVAL '1 month')::date
        ) AS rolling_window_is_three_consecutive_calendar_months

    FROM monthly AS m
)

SELECT
    c.*,

    CASE
        WHEN c.has_previous_calendar_month IS TRUE
            THEN c.provisional_invoice_to_bill_difference
                 - c.previous_observed_difference
        ELSE NULL
    END AS calendar_month_difference_change,

    CASE
        WHEN c.has_previous_calendar_month IS TRUE
         AND c.provisional_invoice_to_bill_difference IS NOT NULL
         AND c.previous_observed_difference IS NOT NULL
         AND c.previous_observed_difference <> 0
            THEN (
                (
                    c.provisional_invoice_to_bill_difference
                    - c.previous_observed_difference
                ) / ABS(c.previous_observed_difference)
            ) * 100
        ELSE NULL
    END AS calendar_month_difference_change_pct,

    CASE
        WHEN c.rolling_3_observed_row_value_count = 3
            THEN c.rolling_3_observed_row_average
        ELSE NULL
    END AS rolling_3_observed_row_average_complete,

    CASE
        WHEN c.has_both_record_types IS TRUE
         AND c.provisional_invoice_to_bill_difference IS NOT NULL
         AND c.provisional_invoice_to_bill_difference > 0
            THEN 'positive_provisional_difference'

        WHEN c.has_both_record_types IS TRUE
         AND c.provisional_invoice_to_bill_difference IS NOT NULL
         AND c.provisional_invoice_to_bill_difference < 0
            THEN 'negative_provisional_difference'

        WHEN c.has_both_record_types IS TRUE
         AND c.provisional_invoice_to_bill_difference = 0
            THEN 'zero_provisional_difference'

        WHEN c.has_both_record_types IS TRUE
            THEN 'difference_unavailable'

        ELSE 'comparison_unavailable'
    END AS provisional_difference_direction,

    (
        c.has_both_record_types IS TRUE
        AND c.provisional_invoice_to_bill_difference IS NOT NULL
    ) AS has_comparable_provisional_difference,

    'provisional_invoice_to_bill_difference_not_profit'
        AS trend_interpretation

FROM calendar_checks AS c;


-- ============================================================
-- VALIDATION
-- ============================================================

SELECT
    COUNT(*) AS total_rows,

    COUNT(DISTINCT business_id) AS businesses,

    COUNT(*) FILTER (
        WHERE has_both_record_types
    ) AS rows_with_both_record_types,

    COUNT(*) FILTER (
        WHERE has_comparable_provisional_difference
    ) AS comparable_difference_rows,

    COUNT(*) FILTER (
        WHERE has_previous_calendar_month
    ) AS rows_with_previous_calendar_month,

    COUNT(*) FILTER (
        WHERE rolling_3_observed_row_value_count = 3
    ) AS complete_three_observed_row_windows,

    COUNT(*) FILTER (
        WHERE rolling_window_is_three_consecutive_calendar_months
    ) AS consecutive_three_calendar_month_windows,

    COUNT(*) FILTER (
        WHERE provisional_difference_direction =
            'positive_provisional_difference'
    ) AS positive_differences,

    COUNT(*) FILTER (
        WHERE provisional_difference_direction =
            'negative_provisional_difference'
    ) AS negative_differences,

    COUNT(*) FILTER (
        WHERE provisional_difference_direction =
            'comparison_unavailable'
    ) AS unavailable_comparisons

FROM analytics.v_monthly_profitability_trends;
