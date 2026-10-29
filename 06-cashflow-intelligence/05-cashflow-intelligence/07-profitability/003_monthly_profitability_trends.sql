
-- ============================================================
-- Orey Analytics
-- Phase 06 — Cash Flow Intelligence
-- Module 07 — Profitability
--
-- Script: 003_monthly_profitability_trends.sql
--
-- Purpose:
-- Analyse provisional invoice-to-bill differences over time.
-- Preserve the established 45-column view contract.
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
        p.business_id,
        p.business_name,
        p.currency,
        p.month_start,
        p.accounting_basis,
        p.accounting_interpretation_status,
        p.revenue_quality_status,
        p.invoice_record_count,
        p.distinct_invoice_count,
        p.total_invoiced_amount,
        p.total_invoice_recorded_payments,
        p.invoice_month_outstanding_amount,
        p.supplier_bill_count,
        p.non_duplicate_bill_count,
        p.duplicate_bill_count,
        p.total_supplier_bill_amount,
        p.non_duplicate_supplier_bill_amount,
        p.total_amount_paid_recorded_on_bills,
        p.total_indicative_outstanding_amount,
        p.total_quality_flag_count,
        p.has_revenue_record,
        p.has_expense_record,
        p.has_both_record_types,
        p.monthly_evidence_coverage_status,
        p.provisional_invoice_to_bill_difference,
        p.comparison_interpretation,
        p.accounting_expenses_verified,
        p.bank_outflows_verified,
        p.accounting_basis_evidence_status,
        p.profitability_evidence_status,
        p.view_generated_at,

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
            ROWS BETWEEN 1 PRECEDING AND 1 PRECEDING
        ) AS previous_observed_row_difference,

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
    business_id,
    business_name,
    currency,
    month_start,
    accounting_basis,
    accounting_interpretation_status,
    revenue_quality_status,
    invoice_record_count,
    distinct_invoice_count,
    total_invoiced_amount,
    total_invoice_recorded_payments,
    invoice_month_outstanding_amount,
    supplier_bill_count,
    non_duplicate_bill_count,
    duplicate_bill_count,
    total_supplier_bill_amount,
    non_duplicate_supplier_bill_amount,
    total_amount_paid_recorded_on_bills,
    total_indicative_outstanding_amount,
    total_quality_flag_count,
    has_revenue_record,
    has_expense_record,
    has_both_record_types,
    monthly_evidence_coverage_status,
    provisional_invoice_to_bill_difference,
    comparison_interpretation,
    accounting_expenses_verified,
    bank_outflows_verified,
    accounting_basis_evidence_status,
    profitability_evidence_status,
    view_generated_at,
    previous_observed_month,
    previous_observed_difference,
    previous_observed_row_difference,
    rolling_3_observed_row_average,
    rolling_3_observed_row_value_count,
    third_observed_month_start,
    has_previous_calendar_month,
    rolling_window_is_three_consecutive_calendar_months,

    CASE
        WHEN has_previous_calendar_month IS TRUE
        THEN provisional_invoice_to_bill_difference
             - previous_observed_difference
        ELSE NULL
    END AS calendar_month_difference_change,

    CASE
        WHEN has_previous_calendar_month IS TRUE
         AND provisional_invoice_to_bill_difference IS NOT NULL
         AND previous_observed_difference IS NOT NULL
         AND previous_observed_difference <> 0
        THEN (
            (
                provisional_invoice_to_bill_difference
                - previous_observed_difference
            ) / ABS(previous_observed_difference)
        ) * 100
        ELSE NULL
    END AS calendar_month_difference_change_pct,

    CASE
        WHEN rolling_3_observed_row_value_count = 3
        THEN rolling_3_observed_row_average
        ELSE NULL
    END AS rolling_3_observed_row_average_complete,

    CASE
        WHEN has_both_record_types IS TRUE
         AND provisional_invoice_to_bill_difference > 0
        THEN 'positive_provisional_difference'

        WHEN has_both_record_types IS TRUE
         AND provisional_invoice_to_bill_difference < 0
        THEN 'negative_provisional_difference'

        WHEN has_both_record_types IS TRUE
         AND provisional_invoice_to_bill_difference = 0
        THEN 'zero_provisional_difference'

        WHEN has_both_record_types IS TRUE
        THEN 'difference_unavailable'

        ELSE 'comparison_unavailable'
    END AS provisional_difference_direction,

    (
        has_both_record_types IS TRUE
        AND provisional_invoice_to_bill_difference IS NOT NULL
    ) AS has_comparable_provisional_difference,

    'provisional_invoice_to_bill_difference_not_profit'
        AS trend_interpretation

FROM calendar_checks;


-- ============================================================
-- VALIDATION
-- ============================================================

SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT business_id) AS businesses,
    COUNT(*) FILTER (
        WHERE has_both_record_types IS TRUE
    ) AS rows_with_both_record_types,
    COUNT(*) FILTER (
        WHERE has_comparable_provisional_difference IS TRUE
    ) AS comparable_difference_rows,
    COUNT(*) FILTER (
        WHERE has_previous_calendar_month IS TRUE
    ) AS rows_with_previous_calendar_month,
    COUNT(*) FILTER (
        WHERE rolling_3_observed_row_value_count = 3
    ) AS complete_three_observed_row_windows,
    COUNT(*) FILTER (
        WHERE rolling_window_is_three_consecutive_calendar_months IS TRUE
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
    ) AS unavailable_comparisons,
    COUNT(*) FILTER (
        WHERE trend_interpretation IS DISTINCT FROM
            'provisional_invoice_to_bill_difference_not_profit'
    ) AS interpretation_label_failures
FROM analytics.v_monthly_profitability_trends;
