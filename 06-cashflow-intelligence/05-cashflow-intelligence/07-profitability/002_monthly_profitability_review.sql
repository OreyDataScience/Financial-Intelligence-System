
-- ============================================================
-- Orey Analytics
-- Phase 06 — Cash Flow Intelligence
-- Module 07 — Profitability
--
-- Script: 002_monthly_profitability_review.sql
--
-- Purpose:
-- Flag revenue-quality issues, expense-quality issues,
-- unverified accounting expenses and unverified bank outflows.
--
-- Dependency:
--   analytics.v_monthly_profitability_evidence
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_monthly_profitability_review AS
SELECT
    p.*,

    (
        p.has_revenue_record
        AND p.revenue_quality_status =
            'revenue_data_quality_review_required'
    ) AS revenue_quality_review_required,

    (
        p.has_expense_record
        AND COALESCE(p.total_quality_flag_count, 0) > 0
    ) AS expense_quality_review_required,

    (
        p.has_expense_record
        AND p.accounting_expenses_verified IS NOT TRUE
    ) AS accounting_expenses_unverified,

    (
        p.has_expense_record
        AND p.bank_outflows_verified IS NOT TRUE
    ) AS bank_outflows_unverified,

    CASE
        WHEN NOT p.has_revenue_record
          OR NOT p.has_expense_record
            THEN 'incomplete_source_coverage'

        WHEN p.accounting_basis IS NULL
            THEN 'accounting_basis_missing'

        WHEN p.revenue_quality_status =
                 'revenue_data_quality_review_required'
         AND COALESCE(p.total_quality_flag_count, 0) > 0
            THEN 'revenue_and_expense_quality_review_required'

        WHEN p.revenue_quality_status =
                 'revenue_data_quality_review_required'
            THEN 'revenue_quality_review_required'

        WHEN COALESCE(p.total_quality_flag_count, 0) > 0
            THEN 'expense_quality_review_required'

        WHEN p.accounting_expenses_verified IS NOT TRUE
            THEN 'accounting_expenses_unverified'

        ELSE 'eligible_for_profitability_methodology_review'
    END AS detailed_review_status

FROM analytics.v_monthly_profitability_evidence AS p;


-- ============================================================
-- VALIDATION
-- ============================================================

SELECT
    detailed_review_status,
    COUNT(*) AS monthly_rows,

    COUNT(*) FILTER (
        WHERE revenue_quality_review_required
    ) AS revenue_quality_review_rows,

    COUNT(*) FILTER (
        WHERE expense_quality_review_required
    ) AS expense_quality_review_rows,

    COUNT(*) FILTER (
        WHERE accounting_expenses_unverified
    ) AS accounting_expenses_unverified_rows,

    COUNT(*) FILTER (
        WHERE bank_outflows_unverified
    ) AS bank_outflows_unverified_rows

FROM analytics.v_monthly_profitability_review
GROUP BY detailed_review_status
ORDER BY monthly_rows DESC, detailed_review_status;