
-- ============================================================
-- Orey Analytics
-- Phase 06 — Cash Flow Intelligence
-- Module 07 — Profitability
--
-- Script: 004_consolidated_profitability.sql
--
-- Purpose:
-- Consolidate monthly profitability evidence, review flags,
-- and trend indicators into one business-level summary.
--
-- Dependencies:
--   analytics.v_monthly_profitability_review
--   analytics.v_monthly_profitability_trends
--
-- Important:
-- Provisional invoice-to-bill differences are NOT profit.
-- Accounting expenses and bank outflows remain unverified
-- until supporting evidence establishes otherwise.
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_consolidated_profitability AS

SELECT
    t.business_id,
    t.business_name,
    t.currency,

    MIN(t.month_start) AS first_observed_month,
    MAX(t.month_start) AS last_observed_month,
    COUNT(*) AS total_monthly_rows,

    COUNT(*) FILTER (
        WHERE t.has_revenue_record
    ) AS months_with_revenue_records,

    COUNT(*) FILTER (
        WHERE t.has_expense_record
    ) AS months_with_expense_records,

    COUNT(*) FILTER (
        WHERE t.has_both_record_types
    ) AS months_with_both_record_types,

    COUNT(*) FILTER (
        WHERE NOT t.has_revenue_record
           OR NOT t.has_expense_record
    ) AS months_with_incomplete_source_coverage,

    COUNT(*) FILTER (
        WHERE r.revenue_quality_review_required
    ) AS months_requiring_revenue_quality_review,

    COUNT(*) FILTER (
        WHERE r.expense_quality_review_required
    ) AS months_requiring_expense_quality_review,

    COUNT(*) FILTER (
        WHERE r.accounting_expenses_unverified
    ) AS months_with_unverified_accounting_expenses,

    COUNT(*) FILTER (
        WHERE r.bank_outflows_unverified
    ) AS months_with_unverified_bank_outflows,

    COUNT(*) FILTER (
        WHERE t.has_comparable_provisional_difference
    ) AS months_with_comparable_provisional_difference,

    COUNT(*) FILTER (
        WHERE t.provisional_difference_direction =
            'positive_provisional_difference'
    ) AS positive_provisional_difference_months,

    COUNT(*) FILTER (
        WHERE t.provisional_difference_direction =
            'negative_provisional_difference'
    ) AS negative_provisional_difference_months,

    COUNT(*) FILTER (
        WHERE t.provisional_difference_direction =
            'zero_provisional_difference'
    ) AS zero_provisional_difference_months,

    SUM(t.provisional_invoice_to_bill_difference)
        AS sum_of_provisional_invoice_to_bill_differences,

    AVG(t.provisional_invoice_to_bill_difference)
        AS average_provisional_invoice_to_bill_difference,

    COUNT(*) FILTER (
        WHERE t.rolling_3_observed_row_value_count = 3
    ) AS months_with_complete_three_difference_windows,

    COUNT(*) FILTER (
        WHERE t.rolling_window_is_three_consecutive_calendar_months
    ) AS months_with_three_consecutive_calendar_months,

    COUNT(DISTINCT t.accounting_basis)
        AS distinct_recorded_accounting_basis_count,

    STRING_AGG(
        DISTINCT t.accounting_basis,
        ', ' ORDER BY t.accounting_basis
    ) AS recorded_accounting_bases,

    CASE
        WHEN COUNT(*) FILTER (
            WHERE t.has_both_record_types
        ) = 0
            THEN 'no_months_with_both_record_types'

        WHEN COUNT(*) FILTER (
            WHERE r.accounting_expenses_unverified
        ) > 0
            THEN 'provisional_comparison_accounting_expenses_unverified'

        ELSE 'requires_profitability_evidence_review'
    END AS consolidated_profitability_evidence_status,

    'provisional_invoice_to_bill_comparison_not_profit'
        AS interpretation_status,

    CURRENT_TIMESTAMP AS view_generated_at

FROM analytics.v_monthly_profitability_trends AS t

LEFT JOIN analytics.v_monthly_profitability_review AS r
    ON  t.business_id = r.business_id
    AND t.currency = r.currency
    AND t.month_start = r.month_start

GROUP BY
    t.business_id,
    t.business_name,
    t.currency;


-- ============================================================
-- VALIDATION 1: BUSINESS-LEVEL SUMMARY
-- Expected: 5 rows, 5 businesses, 120 monthly rows.
-- ============================================================

SELECT
    COUNT(*) AS consolidated_rows,
    COUNT(DISTINCT business_id) AS distinct_businesses,
    SUM(total_monthly_rows) AS total_monthly_rows,

    SUM(months_with_revenue_records) AS revenue_months,
    SUM(months_with_expense_records) AS expense_months,
    SUM(months_with_both_record_types) AS months_with_both_sources,
    SUM(months_with_incomplete_source_coverage)
        AS incomplete_coverage_months,

    SUM(months_with_unverified_accounting_expenses)
        AS unverified_accounting_expense_months,

    SUM(months_with_unverified_bank_outflows)
        AS unverified_bank_outflow_months,

    SUM(months_with_comparable_provisional_difference)
        AS comparable_difference_months,

    SUM(months_with_complete_three_difference_windows)
        AS complete_three_difference_windows

FROM analytics.v_consolidated_profitability;


-- ============================================================
-- VALIDATION 2: DUPLICATE BUSINESS/CURRENCY GROUPS
-- Expected: zero rows.
-- ============================================================

SELECT
    business_id,
    currency,
    COUNT(*) AS row_count

FROM analytics.v_consolidated_profitability

GROUP BY
    business_id,
    currency

HAVING COUNT(*) > 1

ORDER BY
    business_id,
    currency;


-- ============================================================
-- VALIDATION 3: INTERPRETATION AND VERIFICATION STATUS
-- Expected: all 5 businesses use the explicit non-profit
-- interpretation; unverified evidence remains unverified.
-- ============================================================

SELECT
    consolidated_profitability_evidence_status,
    interpretation_status,
    COUNT(*) AS business_count,

    SUM(months_with_unverified_accounting_expenses)
        AS unverified_accounting_expense_months,

    SUM(months_with_unverified_bank_outflows)
        AS unverified_bank_outflow_months

FROM analytics.v_consolidated_profitability

GROUP BY
    consolidated_profitability_evidence_status,
    interpretation_status

ORDER BY
    consolidated_profitability_evidence_status,
    interpretation_status;
