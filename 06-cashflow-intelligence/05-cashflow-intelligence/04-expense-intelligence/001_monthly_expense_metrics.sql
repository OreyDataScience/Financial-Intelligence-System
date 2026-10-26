
-- ============================================================
-- Orey Analytics
-- Phase 06 — Cash Flow Intelligence
-- Module 04: Expense Intelligence
-- Script 001: Monthly Expense Metrics
--
-- Purpose:
-- Summarise supplier-bill activity by business, currency,
-- and bill month without modifying the source records.
--
-- Important:
-- Supplier bills are not necessarily accounting expenses.
-- Amounts paid recorded on bills are not verified bank outflows.
-- Outstanding balances are indicative and retain data-quality
-- limitations from the source records.
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_monthly_expense_metrics AS

WITH bill_monthly AS (
    SELECT
        b.business_id,
        bp.business_name,
        b.currency,
        DATE_TRUNC('month', b.bill_date_std)::date AS month_start,

        COUNT(*) AS supplier_bill_count,

        COUNT(*) FILTER (
            WHERE COALESCE(b.is_duplicate, FALSE) = FALSE
        ) AS non_duplicate_bill_count,

        COUNT(*) FILTER (
            WHERE COALESCE(b.is_duplicate, FALSE) = TRUE
        ) AS duplicate_bill_count,

        SUM(b.bill_amount) AS total_supplier_bill_amount,

        SUM(
            CASE
                WHEN COALESCE(b.is_duplicate, FALSE) = FALSE
                THEN b.bill_amount
                ELSE 0
            END
        ) AS non_duplicate_supplier_bill_amount,

        SUM(b.amount_paid) AS total_amount_paid_recorded_on_bills,

        SUM(
            CASE
                WHEN b.bill_amount IS NOT NULL
                     AND b.amount_paid IS NOT NULL
                THEN b.bill_amount - b.amount_paid
                ELSE NULL
            END
        ) AS total_indicative_outstanding_amount,

        COUNT(*) FILTER (
            WHERE b.bill_date_std IS NULL
        ) AS bills_missing_standardized_bill_date,

        COUNT(*) FILTER (
            WHERE b.due_date_std IS NULL
        ) AS bills_missing_standardized_due_date,

        COUNT(*) FILTER (
            WHERE COALESCE(b.missing_supplier_id, FALSE) = TRUE
        ) AS bills_missing_supplier_id,

        COUNT(*) FILTER (
            WHERE COALESCE(b.paid_amount_mismatch, FALSE) = TRUE
        ) AS bills_with_paid_amount_mismatch,

        COUNT(*) FILTER (
            WHERE COALESCE(b.payment_before_bill_flag, FALSE) = TRUE
        ) AS bills_with_payment_before_bill_date,

        COUNT(*) FILTER (
            WHERE COALESCE(b.is_duplicate, FALSE) = TRUE
        ) AS bills_flagged_as_duplicates,

        COUNT(*) FILTER (
            WHERE b.reconciliation_status IS NOT NULL
              AND b.reconciliation_status NOT IN (
                  'matched_bank',
                  'matched',
                  'not_applicable'
              )
        ) AS bills_with_other_reconciliation_statuses

    FROM processed.supplier_bills AS b

    LEFT JOIN processed.business_profiles AS bp
        ON bp.business_id = b.business_id

    WHERE b.bill_date_std IS NOT NULL

    GROUP BY
        b.business_id,
        bp.business_name,
        b.currency,
        DATE_TRUNC('month', b.bill_date_std)::date
)

SELECT
    business_id,
    business_name,
    currency,
    month_start,

    supplier_bill_count,
    non_duplicate_bill_count,
    duplicate_bill_count,

    total_supplier_bill_amount,
    non_duplicate_supplier_bill_amount,
    total_amount_paid_recorded_on_bills,
    total_indicative_outstanding_amount,

    bills_missing_standardized_bill_date,
    bills_missing_standardized_due_date,
    bills_missing_supplier_id,
    bills_with_paid_amount_mismatch,
    bills_with_payment_before_bill_date,
    bills_flagged_as_duplicates,
    bills_with_other_reconciliation_statuses,

    (
        bills_missing_standardized_due_date
        + bills_missing_supplier_id
        + bills_with_paid_amount_mismatch
        + bills_with_payment_before_bill_date
        + bills_flagged_as_duplicates
        + bills_with_other_reconciliation_statuses
    ) AS total_quality_flag_count,

    FALSE AS bank_outflows_verified,

    CURRENT_TIMESTAMP AS view_generated_at

FROM bill_monthly;
