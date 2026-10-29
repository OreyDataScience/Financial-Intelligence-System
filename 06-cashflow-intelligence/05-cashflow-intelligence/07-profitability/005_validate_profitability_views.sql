
-- ============================================================
-- Orey Analytics
-- Phase 06 — Cash Flow Intelligence
-- Module 07 — Profitability Intelligence
--
-- Script 005: Validate Profitability Views
--
-- Purpose:
-- Validate existence, row counts, coverage, evidence status,
-- trend calculations and consolidated profitability outputs.
--
-- Read-only validation. Does not modify any views or data.
-- ============================================================


-- ============================================================
-- VALIDATION 1: Confirm all four expected views exist
-- ============================================================

SELECT
    expected.view_name,
    CASE
        WHEN actual.viewname IS NOT NULL THEN 'present'
        ELSE 'missing'
    END AS view_status
FROM (
    VALUES
        ('v_monthly_profitability_evidence'),
        ('v_monthly_profitability_review'),
        ('v_monthly_profitability_trends'),
        ('v_consolidated_profitability')
) AS expected(view_name)
LEFT JOIN pg_views AS actual
    ON actual.schemaname = 'analytics'
   AND actual.viewname = expected.view_name
ORDER BY expected.view_name;


-- ============================================================
-- VALIDATION 2: Evidence and review row counts
-- ============================================================

SELECT
    'v_monthly_profitability_evidence' AS view_name,
    COUNT(*) AS row_count,
    COUNT(DISTINCT business_id) AS businesses
FROM analytics.v_monthly_profitability_evidence

UNION ALL

SELECT
    'v_monthly_profitability_review',
    COUNT(*),
    COUNT(DISTINCT business_id)
FROM analytics.v_monthly_profitability_review

UNION ALL

SELECT
    'v_monthly_profitability_trends',
    COUNT(*),
    COUNT(DISTINCT business_id)
FROM analytics.v_monthly_profitability_trends

UNION ALL

SELECT
    'v_consolidated_profitability',
    COUNT(*),
    COUNT(DISTINCT business_id)
FROM analytics.v_consolidated_profitability

ORDER BY view_name;


-- ============================================================
-- VALIDATION 3: Monthly evidence coverage
-- ============================================================

SELECT
    COUNT(*) AS monthly_rows,
    COUNT(DISTINCT business_id) AS businesses,
    COUNT(*) FILTER (
        WHERE has_revenue_record
    ) AS revenue_record_months,
    COUNT(*) FILTER (
        WHERE has_expense_record
    ) AS expense_record_months,
    COUNT(*) FILTER (
        WHERE has_both_record_types
    ) AS months_with_both_record_types,
    COUNT(*) FILTER (
        WHERE NOT has_both_record_types
    ) AS months_without_both_record_types
FROM analytics.v_monthly_profitability_review;


-- ============================================================
-- VALIDATION 4: Evidence limitations
-- ============================================================

SELECT
    COUNT(*) AS monthly_rows,
    COUNT(*) FILTER (
        WHERE accounting_expenses_unverified
    ) AS accounting_expenses_unverified_months,
    COUNT(*) FILTER (
        WHERE bank_outflows_unverified
    ) AS bank_outflows_unverified_months,
    COUNT(*) FILTER (
        WHERE accounting_expenses_verified
    ) AS accounting_expenses_verified_months,
    COUNT(*) FILTER (
        WHERE bank_outflows_verified
    ) AS bank_outflows_verified_months
FROM analytics.v_monthly_profitability_review;


-- ============================================================
-- VALIDATION 5: Trend calculations and comparability
-- ============================================================

SELECT
    COUNT(*) AS trend_rows,
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
        WHERE trend_interpretation IS NULL
           OR trend_interpretation = ''
    ) AS missing_trend_interpretations
FROM analytics.v_monthly_profitability_trends;


-- ============================================================
-- VALIDATION 6: Consolidated summary totals
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
        AS complete_three_difference_windows,
    SUM(months_with_three_consecutive_calendar_months)
        AS consecutive_calendar_months
FROM analytics.v_consolidated_profitability;


-- ============================================================
-- VALIDATION 7: Consolidated uniqueness and interpretation
-- ============================================================

SELECT
    COUNT(*) AS consolidated_rows,
    COUNT(DISTINCT business_id) AS distinct_businesses,
    COUNT(*) FILTER (
        WHERE interpretation_status IS DISTINCT FROM
            'provisional_invoice_to_bill_comparison_not_profit'
    ) AS interpretation_label_failures
FROM analytics.v_consolidated_profitability;


-- ============================================================
-- VALIDATION 8: Duplicate business/currency groups
-- Expected: zero rows
-- ============================================================

SELECT
    business_id,
    currency,
    COUNT(*) AS duplicate_rows
FROM analytics.v_consolidated_profitability
GROUP BY
    business_id,
    currency
HAVING COUNT(*) > 1;


-- ============================================================
-- VALIDATION 9: Consolidated evidence-status distribution
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
