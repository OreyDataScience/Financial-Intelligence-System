
-- ============================================================
-- Orey Analytics
-- Phase 06 — Cash Flow Intelligence
-- Module 07 — Profitability
--
-- Script: 001_monthly_profitability_evidence.sql
--
-- Purpose:
-- Combine monthly invoice and supplier-bill evidence.
-- Preserve missing source months and accounting limitations.
-- Do not interpret invoice-to-bill differences as profit.
--
-- Dependencies:
--   analytics.v_consolidated_revenue
--   analytics.v_consolidated_expenses
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_monthly_profitability_evidence AS
SELECT
    COALESCE(r.business_id, e.business_id) AS business_id,
    COALESCE(r.business_name, e.business_name) AS business_name,
    COALESCE(r.currency, e.currency) AS currency,
    COALESCE(r.month_start, e.month_start) AS month_start,

    r.accounting_basis,
    r.accounting_interpretation_status,
    r.revenue_quality_status,

    r.invoice_record_count,
    r.distinct_invoice_count,
    r.total_invoiced_amount,
    r.total_invoice_recorded_payments,
    r.invoice_month_outstanding_amount,

    e.supplier_bill_count,
    e.non_duplicate_bill_count,
    e.duplicate_bill_count,
    e.total_supplier_bill_amount,
    e.non_duplicate_supplier_bill_amount,
    e.total_amount_paid_recorded_on_bills,
    e.total_indicative_outstanding_amount,
    e.total_quality_flag_count,

    (r.business_id IS NOT NULL) AS has_revenue_record,
    (e.business_id IS NOT NULL) AS has_expense_record,

    (
        r.business_id IS NOT NULL
        AND e.business_id IS NOT NULL
    ) AS has_both_record_types,

    CASE
        WHEN r.business_id IS NOT NULL
         AND e.business_id IS NOT NULL
            THEN 'revenue_and_expense_records_present'
        WHEN r.business_id IS NOT NULL
            THEN 'revenue_record_only'
        WHEN e.business_id IS NOT NULL
            THEN 'expense_record_only'
        ELSE 'no_source_records'
    END AS monthly_evidence_coverage_status,

    CASE
        WHEN r.business_id IS NOT NULL
         AND e.business_id IS NOT NULL
            THEN r.total_invoiced_amount
                 - e.non_duplicate_supplier_bill_amount
        ELSE NULL
    END AS provisional_invoice_to_bill_difference,

    'provisional_invoice_to_bill_difference_not_profit'
        AS comparison_interpretation,

    e.accounting_expenses_verified,
    e.bank_outflows_verified,

    CASE
        WHEN r.business_id IS NULL
            THEN 'no_revenue_view_record'
        WHEN r.accounting_basis IS NULL
            THEN 'accounting_basis_missing'
        ELSE 'accounting_basis_recorded'
    END AS accounting_basis_evidence_status,

    CASE
        WHEN r.business_id IS NOT NULL
         AND e.business_id IS NOT NULL
         AND r.revenue_quality_status =
             'no_flagged_quality_issues_in_monthly_scope'
         AND e.accounting_expenses_verified IS TRUE
            THEN 'revenue_quality_clear_expenses_verified'
        WHEN r.business_id IS NOT NULL
         AND e.business_id IS NOT NULL
            THEN 'review_required_before_profitability_claim'
        WHEN r.business_id IS NULL
            THEN 'revenue_evidence_missing_for_month'
        ELSE 'expense_evidence_missing_for_month'
    END AS profitability_evidence_status,

    CURRENT_TIMESTAMP AS view_generated_at

FROM analytics.v_consolidated_revenue AS r
FULL OUTER JOIN analytics.v_consolidated_expenses AS e
    ON r.business_id = e.business_id
    AND r.currency = e.currency
    AND r.month_start = e.month_start;


-- ============================================================
-- VALIDATION
-- Expected based on the validated current dataset:
--   120 monthly rows
--   5 businesses
--   111 revenue rows
--   98 expense rows
--   89 rows with both record types
--   22 revenue-only rows
--   9 expense-only rows
--   0 verified accounting-expense rows
--   0 verified bank-outflow rows
-- ============================================================

SELECT
    COUNT(*) AS total_monthly_rows,
    COUNT(DISTINCT business_id) AS distinct_businesses,

    COUNT(*) FILTER (
        WHERE has_revenue_record
    ) AS months_with_revenue_records,

    COUNT(*) FILTER (
        WHERE has_expense_record
    ) AS months_with_expense_records,

    COUNT(*) FILTER (
        WHERE has_both_record_types
    ) AS months_with_both_record_types,

    COUNT(*) FILTER (
        WHERE has_revenue_record
          AND NOT has_expense_record
    ) AS revenue_only_months,

    COUNT(*) FILTER (
        WHERE has_expense_record
          AND NOT has_revenue_record
    ) AS expense_only_months,

    COUNT(*) FILTER (
        WHERE accounting_expenses_verified IS TRUE
    ) AS verified_accounting_expense_rows,

    COUNT(*) FILTER (
        WHERE bank_outflows_verified IS TRUE
    ) AS verified_bank_outflow_rows

FROM analytics.v_monthly_profitability_evidence;
