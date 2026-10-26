-- ============================================================
-- Orey Analytics
-- Phase 06 — Cash Flow Intelligence
-- Module 04: Expense Intelligence
-- Script 005: Consolidated Expenses
--
-- Purpose:
-- Consolidate monthly supplier-bill metrics, trends, supplier
-- concentration, and expense-quality indicators.
--
-- Grain:
-- One row per business_id + currency + month_start.
--
-- Important limitations:
-- - Supplier-bill amounts are not verified accounting expenses.
-- - Amounts recorded as paid on bills are not verified bank outflows.
-- - Quality totals are business/currency-level, not month-specific.
-- - Original source records remain unchanged.
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_consolidated_expenses AS

WITH quality_by_business_currency AS (
    SELECT
        q.business_id,
        q.currency,

        COUNT(*) AS business_currency_total_bill_records,

        SUM(CASE
            WHEN q.requires_quality_review_flag THEN 1
            ELSE 0
        END) AS business_currency_records_requiring_quality_review,

        SUM(CASE
            WHEN q.missing_supplier_id_flag THEN 1
            ELSE 0
        END) AS business_currency_bills_missing_supplier_id,

        SUM(CASE
            WHEN q.paid_amount_mismatch_flag THEN 1
            ELSE 0
        END) AS business_currency_bills_with_paid_amount_mismatch,

        SUM(CASE
            WHEN q.duplicate_bill_flag THEN 1
            ELSE 0
        END) AS business_currency_duplicate_bills,

        SUM(CASE
            WHEN q.missing_standardized_bill_date_flag THEN 1
            ELSE 0
        END) AS business_currency_bills_missing_standardized_bill_date,

        SUM(CASE
            WHEN q.missing_standardized_due_date_flag THEN 1
            ELSE 0
        END) AS business_currency_bills_missing_standardized_due_date,

        SUM(CASE
            WHEN q.unparsed_payment_date_flag THEN 1
            ELSE 0
        END) AS business_currency_bills_with_unparsed_payment_date,

        SUM(CASE
            WHEN q.payment_before_bill_flag THEN 1
            ELSE 0
        END) AS business_currency_bills_flagged_payment_before_bill,

        SUM(CASE
            WHEN q.negative_bill_amount_flag THEN 1
            ELSE 0
        END) AS business_currency_bills_with_negative_bill_amount,

        SUM(CASE
            WHEN q.negative_amount_paid_flag THEN 1
            ELSE 0
        END) AS business_currency_bills_with_negative_amount_paid,

        SUM(CASE
            WHEN q.amount_paid_exceeds_bill_amount_flag THEN 1
            ELSE 0
        END) AS business_currency_bills_where_paid_exceeds_bill,

        SUM(CASE
            WHEN q.due_date_before_bill_date_flag THEN 1
            ELSE 0
        END) AS business_currency_bills_with_due_date_before_bill_date,

        SUM(CASE
            WHEN q.payment_date_before_bill_date_flag THEN 1
            ELSE 0
        END) AS business_currency_bills_with_payment_date_before_bill_date,

        SUM(CASE
            WHEN q.reconciliation_requires_review_flag THEN 1
            ELSE 0
        END) AS business_currency_bills_requiring_reconciliation_review,

        SUM(CASE
            WHEN q.incomplete_bank_match_evidence_flag THEN 1
            ELSE 0
        END) AS business_currency_bills_with_incomplete_bank_match_evidence,

        SUM(CASE
            WHEN q.bank_match_amount_difference_flag THEN 1
            ELSE 0
        END) AS business_currency_bills_with_bank_match_amount_difference,

        SUM(CASE
            WHEN q.negative_indicative_balance_flag THEN 1
            ELSE 0
        END) AS business_currency_bills_with_negative_indicative_balance

    FROM analytics.v_expense_quality AS q

    GROUP BY
        q.business_id,
        q.currency
)

SELECT
    -- Business and monthly reporting keys.
    m.business_id,
    m.business_name,
    m.currency,
    m.month_start,

    -- Monthly expense metrics.
    m.supplier_bill_count,
    m.non_duplicate_bill_count,
    m.duplicate_bill_count,
    m.total_supplier_bill_amount,
    m.non_duplicate_supplier_bill_amount,
    m.total_amount_paid_recorded_on_bills,
    m.total_indicative_outstanding_amount,

    -- Monthly quality indicators.
    m.bills_missing_standardized_bill_date,
    m.bills_missing_standardized_due_date,
    m.bills_missing_supplier_id,
    m.bills_with_paid_amount_mismatch,
    m.bills_with_payment_before_bill_date,
    m.bills_flagged_as_duplicates,
    m.bills_with_other_reconciliation_statuses,
    m.total_quality_flag_count,

    -- Expense trend metrics.
    t.previous_observed_month,
    t.previous_calendar_month_bill_amount,
    t.previous_calendar_month_non_duplicate_bill_amount,
    t.previous_calendar_month_recorded_paid_amount,
    t.month_over_month_bill_amount_change,
    t.month_over_month_bill_amount_change_pct,
    t.month_over_month_non_duplicate_bill_amount_change,
    t.month_over_month_non_duplicate_bill_amount_change_pct,
    t.observed_months_in_rolling_window,
    t.rolling_3_observed_month_bill_amount,
    t.rolling_3_observed_month_non_duplicate_bill_amount,
    t.average_bill_amount_per_observed_month_3_rows,
    t.rolling_window_has_3_observed_rows,
    t.month_over_month_comparison_unavailable,

    -- Supplier concentration metrics.
    s.total_non_duplicate_bill_amount,
    s.identifiable_positive_supplier_bill_amount,
    s.identifiable_supplier_count,
    s.missing_supplier_group_count,
    s.bills_with_missing_supplier_id,
    s.positive_supplier_count,
    s.largest_supplier_share_pct,
    s.supplier_concentration_hhi,
    s.supplier_concentration_band,
    s.total_bill_amount_non_positive_or_missing,
    s.supplier_identity_incomplete,

    -- Business/currency-level quality totals.
    -- These are not restricted to the current month.
    q.business_currency_total_bill_records,
    q.business_currency_records_requiring_quality_review,
    q.business_currency_bills_missing_supplier_id,
    q.business_currency_bills_with_paid_amount_mismatch,
    q.business_currency_duplicate_bills,
    q.business_currency_bills_missing_standardized_bill_date,
    q.business_currency_bills_missing_standardized_due_date,
    q.business_currency_bills_with_unparsed_payment_date,
    q.business_currency_bills_flagged_payment_before_bill,
    q.business_currency_bills_with_negative_bill_amount,
    q.business_currency_bills_with_negative_amount_paid,
    q.business_currency_bills_where_paid_exceeds_bill,
    q.business_currency_bills_with_due_date_before_bill_date,
    q.business_currency_bills_with_payment_date_before_bill_date,
    q.business_currency_bills_requiring_reconciliation_review,
    q.business_currency_bills_with_incomplete_bank_match_evidence,
    q.business_currency_bills_with_bank_match_amount_difference,
    q.business_currency_bills_with_negative_indicative_balance,

    -- Verification safeguards.
    FALSE AS accounting_expenses_verified,
    FALSE AS bank_outflows_verified,

    CURRENT_TIMESTAMP AS view_generated_at

FROM analytics.v_monthly_expense_metrics AS m

LEFT JOIN analytics.v_expense_trends AS t
    ON  t.business_id = m.business_id
    AND t.currency = m.currency
    AND t.month_start = m.month_start

LEFT JOIN analytics.v_supplier_concentration AS s
    ON  s.business_id = m.business_id
    AND s.currency = m.currency
    AND s.month_start = m.month_start

LEFT JOIN quality_by_business_currency AS q
    ON  q.business_id = m.business_id
    AND q.currency = m.currency;