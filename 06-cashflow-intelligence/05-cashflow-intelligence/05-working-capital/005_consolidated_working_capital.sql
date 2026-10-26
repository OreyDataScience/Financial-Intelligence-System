
-- ============================================================
-- Orey Analytics
-- Phase 06 — Cash Flow Intelligence
-- Module 05 — Working Capital
-- Script 005: Consolidated Working Capital
--
-- Purpose:
-- Combine receivables, payables, aging and data-quality
-- indicators into one business-level working-capital view.
--
-- Important interpretation:
--   * Balances are derived from invoice and supplier-bill data.
--   * These figures are not verified bank balances.
--   * Net recorded working capital is not available cash.
--   * Flagged records are retained in the underlying views.
--   * Quality exposures can overlap and must not be summed
--     as if they were independent losses.
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_consolidated_working_capital AS

WITH receivables AS (
    SELECT
        business_id,
        business_name,
        currency,

        COUNT(*) AS invoice_record_count,

        COUNT(*) FILTER (
            WHERE status_adjusted_outstanding_amount > 0
        ) AS open_invoice_count,

        COUNT(*) FILTER (
            WHERE status_adjusted_outstanding_amount > 0
              AND is_past_due IS TRUE
        ) AS overdue_invoice_count,

        COUNT(*) FILTER (
            WHERE status_adjusted_outstanding_amount > 0
              AND due_date IS NULL
        ) AS open_invoice_missing_due_date_count,

        COALESCE(
            SUM(invoice_amount), 0
        ) AS recorded_invoice_amount,

        COALESCE(
            SUM(amount_paid), 0
        ) AS recorded_invoice_amount_paid,

        COALESCE(
            SUM(status_adjusted_outstanding_amount), 0
        ) AS recorded_outstanding_receivables,

        COALESCE(
            SUM(status_adjusted_outstanding_amount) FILTER (
                WHERE is_past_due IS TRUE
            ), 0
        ) AS recorded_overdue_receivables,

        COALESCE(
            SUM(status_adjusted_outstanding_amount) FILTER (
                WHERE due_date IS NULL
                  AND status_adjusted_outstanding_amount > 0
            ), 0
        ) AS receivables_missing_due_date_exposure,

        COALESCE(
            SUM(status_adjusted_outstanding_amount) FILTER (
                WHERE receivables_aging_band = 'overdue_1_30_days'
            ), 0
        ) AS receivables_overdue_1_30_days,

        COALESCE(
            SUM(status_adjusted_outstanding_amount) FILTER (
                WHERE receivables_aging_band = 'overdue_31_60_days'
            ), 0
        ) AS receivables_overdue_31_60_days,

        COALESCE(
            SUM(status_adjusted_outstanding_amount) FILTER (
                WHERE receivables_aging_band = 'overdue_61_90_days'
            ), 0
        ) AS receivables_overdue_61_90_days,

        COALESCE(
            SUM(status_adjusted_outstanding_amount) FILTER (
                WHERE receivables_aging_band = 'overdue_over_90_days'
            ), 0
        ) AS receivables_overdue_over_90_days,

        MAX(aging_as_of_date) AS aging_as_of_date

    FROM analytics.v_receivables_aging
    GROUP BY business_id, business_name, currency
),

payables AS (
    SELECT
        business_id,
        business_name,
        currency,

        COUNT(*) AS bill_record_count,

        COUNT(*) FILTER (
            WHERE status_adjusted_outstanding_amount > 0
        ) AS open_bill_count,

        COUNT(*) FILTER (
            WHERE status_adjusted_outstanding_amount > 0
              AND is_past_due IS TRUE
        ) AS overdue_bill_count,

        COUNT(*) FILTER (
            WHERE status_adjusted_outstanding_amount > 0
              AND due_date IS NULL
        ) AS open_bill_missing_due_date_count,

        COALESCE(
            SUM(bill_amount), 0
        ) AS recorded_bill_amount,

        COALESCE(
            SUM(amount_paid), 0
        ) AS recorded_bill_amount_paid,

        COALESCE(
            SUM(status_adjusted_outstanding_amount), 0
        ) AS recorded_outstanding_payables,

        COALESCE(
            SUM(status_adjusted_outstanding_amount) FILTER (
                WHERE is_past_due IS TRUE
            ), 0
        ) AS recorded_overdue_payables,

        COALESCE(
            SUM(status_adjusted_outstanding_amount) FILTER (
                WHERE due_date IS NULL
                  AND status_adjusted_outstanding_amount > 0
            ), 0
        ) AS payables_missing_due_date_exposure,

        COALESCE(
            SUM(status_adjusted_outstanding_amount) FILTER (
                WHERE payables_aging_band = 'overdue_1_30_days'
            ), 0
        ) AS payables_overdue_1_30_days,

        COALESCE(
            SUM(status_adjusted_outstanding_amount) FILTER (
                WHERE payables_aging_band = 'overdue_31_60_days'
            ), 0
        ) AS payables_overdue_31_60_days,

        COALESCE(
            SUM(status_adjusted_outstanding_amount) FILTER (
                WHERE payables_aging_band = 'overdue_61_90_days'
            ), 0
        ) AS payables_overdue_61_90_days,

        COALESCE(
            SUM(status_adjusted_outstanding_amount) FILTER (
                WHERE payables_aging_band = 'overdue_over_90_days'
            ), 0
        ) AS payables_overdue_over_90_days,

        MAX(aging_as_of_date) AS aging_as_of_date

    FROM analytics.v_payables_aging
    GROUP BY business_id, business_name, currency
),

combined AS (
    SELECT
        COALESCE(r.business_id, p.business_id) AS business_id,
        COALESCE(r.business_name, p.business_name) AS business_name,
        COALESCE(r.currency, p.currency) AS currency,

        COALESCE(r.invoice_record_count, 0)
            AS invoice_record_count,
        COALESCE(p.bill_record_count, 0)
            AS bill_record_count,

        COALESCE(r.open_invoice_count, 0)
            AS open_invoice_count,
        COALESCE(p.open_bill_count, 0)
            AS open_bill_count,

        COALESCE(r.overdue_invoice_count, 0)
            AS overdue_invoice_count,
        COALESCE(p.overdue_bill_count, 0)
            AS overdue_bill_count,

        COALESCE(r.open_invoice_missing_due_date_count, 0)
            AS open_invoice_missing_due_date_count,
        COALESCE(p.open_bill_missing_due_date_count, 0)
            AS open_bill_missing_due_date_count,

        COALESCE(r.recorded_invoice_amount, 0)
            AS recorded_invoice_amount,
        COALESCE(r.recorded_invoice_amount_paid, 0)
            AS recorded_invoice_amount_paid,
        COALESCE(r.recorded_outstanding_receivables, 0)
            AS recorded_outstanding_receivables,
        COALESCE(r.recorded_overdue_receivables, 0)
            AS recorded_overdue_receivables,
        COALESCE(r.receivables_missing_due_date_exposure, 0)
            AS receivables_missing_due_date_exposure,

        COALESCE(r.receivables_overdue_1_30_days, 0)
            AS receivables_overdue_1_30_days,
        COALESCE(r.receivables_overdue_31_60_days, 0)
            AS receivables_overdue_31_60_days,
        COALESCE(r.receivables_overdue_61_90_days, 0)
            AS receivables_overdue_61_90_days,
        COALESCE(r.receivables_overdue_over_90_days, 0)
            AS receivables_overdue_over_90_days,

        COALESCE(p.recorded_bill_amount, 0)
            AS recorded_bill_amount,
        COALESCE(p.recorded_bill_amount_paid, 0)
            AS recorded_bill_amount_paid,
        COALESCE(p.recorded_outstanding_payables, 0)
            AS recorded_outstanding_payables,
        COALESCE(p.recorded_overdue_payables, 0)
            AS recorded_overdue_payables,
        COALESCE(p.payables_missing_due_date_exposure, 0)
            AS payables_missing_due_date_exposure,

        COALESCE(p.payables_overdue_1_30_days, 0)
            AS payables_overdue_1_30_days,
        COALESCE(p.payables_overdue_31_60_days, 0)
            AS payables_overdue_31_60_days,
        COALESCE(p.payables_overdue_61_90_days, 0)
            AS payables_overdue_61_90_days,
        COALESCE(p.payables_overdue_over_90_days, 0)
            AS payables_overdue_over_90_days,

        GREATEST(
            r.aging_as_of_date,
            p.aging_as_of_date
        ) AS aging_as_of_date

    FROM receivables r
    FULL OUTER JOIN payables p
        ON r.business_id = p.business_id
       AND r.currency = p.currency
)

SELECT
    c.*,

    recorded_outstanding_receivables
        - recorded_outstanding_payables
        AS net_recorded_receivables_after_payables,

    CASE
        WHEN recorded_outstanding_payables > 0
        THEN recorded_outstanding_receivables
             / recorded_outstanding_payables
        ELSE NULL
    END AS receivables_to_payables_ratio,

    CASE
        WHEN recorded_outstanding_receivables = 0
         AND recorded_outstanding_payables = 0
            THEN 'no_recorded_outstanding_balances'
        WHEN recorded_outstanding_receivables = 0
            THEN 'payables_exceed_receivables'
        WHEN recorded_outstanding_payables = 0
            THEN 'receivables_only'
        WHEN recorded_outstanding_receivables
             > recorded_outstanding_payables
            THEN 'receivables_exceed_payables'
        WHEN recorded_outstanding_receivables
             < recorded_outstanding_payables
            THEN 'payables_exceed_receivables'
        ELSE 'recorded_receivables_equal_payables'
    END AS recorded_working_capital_position,

    'invoice_and_supplier_bill_records_not_verified_cash'
        AS financial_evidence_basis,

    CURRENT_TIMESTAMP AS view_generated_at

FROM combined c;
