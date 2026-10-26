
-- ============================================================
-- Orey Analytics
-- Phase 06 — Cash Flow Intelligence
-- Module 05 — Working Capital
-- Script 004: Working Capital Quality
--
-- Purpose:
-- Summarise working-capital data-quality indicators by
-- business and currency.
--
-- Design principles:
--   1. Preserve source records and reported amounts.
--   2. Do not silently remove duplicates or alter balances.
--   3. Separate missing information from reconciliation issues.
--   4. Treat flags as investigation indicators, not proof
--      that fraud, error, or loss has occurred.
--   5. Do not equate invoices or supplier bills with verified
--      bank movements.
--   6. Return zero for exposure aggregates when no rows match.
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_working_capital_quality AS

WITH receivables_quality AS (
    SELECT
        business_id,
        business_name,
        currency,

        COUNT(*) AS invoice_record_count,

        COUNT(*) FILTER (
            WHERE due_date IS NULL
        ) AS invoices_missing_due_date,

        COUNT(*) FILTER (
            WHERE missing_due_date_with_outstanding IS TRUE
        ) AS open_invoices_missing_due_date,

        COUNT(*) FILTER (
            WHERE is_duplicate IS TRUE
        ) AS duplicate_flagged_invoices,

        COUNT(*) FILTER (
            WHERE paid_amount_mismatch IS TRUE
        ) AS invoice_payment_mismatch_flags,

        COUNT(*) FILTER (
            WHERE payment_before_invoice_flag IS TRUE
        ) AS payments_before_invoice_flags,

        COUNT(*) FILTER (
            WHERE reconciliation_status = 'ledger_conflict'
        ) AS invoice_ledger_conflicts,

        COUNT(*) FILTER (
            WHERE reconciliation_status = 'unmatched_needs_investigation'
        ) AS invoices_unmatched_needing_investigation,

        COUNT(*) FILTER (
            WHERE status_adjusted_outstanding_amount > 0
              AND due_date IS NULL
        ) AS open_invoices_without_due_dates,

        COALESCE(
            SUM(status_adjusted_outstanding_amount) FILTER (
                WHERE is_duplicate IS TRUE
            ), 0
        ) AS duplicate_invoice_outstanding_exposure,

        COALESCE(
            SUM(status_adjusted_outstanding_amount) FILTER (
                WHERE paid_amount_mismatch IS TRUE
            ), 0
        ) AS invoice_payment_mismatch_exposure,

        COALESCE(
            SUM(status_adjusted_outstanding_amount) FILTER (
                WHERE reconciliation_status = 'ledger_conflict'
            ), 0
        ) AS invoice_ledger_conflict_exposure,

        COALESCE(
            SUM(status_adjusted_outstanding_amount) FILTER (
                WHERE reconciliation_status = 'unmatched_needs_investigation'
            ), 0
        ) AS unmatched_invoice_outstanding_exposure,

        COALESCE(
            SUM(status_adjusted_outstanding_amount) FILTER (
                WHERE status_adjusted_outstanding_amount > 0
                  AND due_date IS NULL
            ), 0
        ) AS open_invoices_missing_due_date_exposure,

        MAX(aging_as_of_date) AS aging_as_of_date

    FROM analytics.v_receivables_aging
    GROUP BY business_id, business_name, currency
),

payables_quality AS (
    SELECT
        business_id,
        business_name,
        currency,

        COUNT(*) AS bill_record_count,

        COUNT(*) FILTER (
            WHERE due_date IS NULL
        ) AS bills_missing_due_date,

        COUNT(*) FILTER (
            WHERE missing_due_date_with_outstanding IS TRUE
        ) AS open_bills_missing_due_date,

        COUNT(*) FILTER (
            WHERE missing_supplier_id IS TRUE
        ) AS bills_missing_supplier_id,

        COUNT(*) FILTER (
            WHERE is_duplicate IS TRUE
        ) AS duplicate_flagged_bills,

        COUNT(*) FILTER (
            WHERE paid_amount_mismatch IS TRUE
        ) AS bill_payment_mismatch_flags,

        COUNT(*) FILTER (
            WHERE payment_before_bill_flag IS TRUE
        ) AS payments_before_bill_flags,

        COUNT(*) FILTER (
            WHERE reconciliation_status = 'ledger_conflict'
        ) AS bill_ledger_conflicts,

        COUNT(*) FILTER (
            WHERE reconciliation_status = 'unmatched_needs_investigation'
        ) AS bills_unmatched_needing_investigation,

        COUNT(*) FILTER (
            WHERE status_adjusted_outstanding_amount > 0
              AND due_date IS NULL
        ) AS open_bills_without_due_dates,

        COALESCE(
            SUM(status_adjusted_outstanding_amount) FILTER (
                WHERE is_duplicate IS TRUE
            ), 0
        ) AS duplicate_bill_outstanding_exposure,

        COALESCE(
            SUM(status_adjusted_outstanding_amount) FILTER (
                WHERE paid_amount_mismatch IS TRUE
            ), 0
        ) AS bill_payment_mismatch_exposure,

        COALESCE(
            SUM(status_adjusted_outstanding_amount) FILTER (
                WHERE reconciliation_status = 'ledger_conflict'
            ), 0
        ) AS bill_ledger_conflict_exposure,

        COALESCE(
            SUM(status_adjusted_outstanding_amount) FILTER (
                WHERE reconciliation_status = 'unmatched_needs_investigation'
            ), 0
        ) AS unmatched_bill_outstanding_exposure,

        COALESCE(
            SUM(status_adjusted_outstanding_amount) FILTER (
                WHERE status_adjusted_outstanding_amount > 0
                  AND due_date IS NULL
            ), 0
        ) AS open_bills_missing_due_date_exposure,

        MAX(aging_as_of_date) AS aging_as_of_date

    FROM analytics.v_payables_aging
    GROUP BY business_id, business_name, currency
),

combined AS (
    SELECT
        COALESCE(r.business_id, p.business_id) AS business_id,
        COALESCE(r.business_name, p.business_name) AS business_name,
        COALESCE(r.currency, p.currency) AS currency,

        COALESCE(r.invoice_record_count, 0) AS invoice_record_count,
        COALESCE(p.bill_record_count, 0) AS bill_record_count,

        COALESCE(r.invoices_missing_due_date, 0)
            AS invoices_missing_due_date,
        COALESCE(r.open_invoices_missing_due_date, 0)
            AS open_invoices_missing_due_date,
        COALESCE(p.bills_missing_due_date, 0)
            AS bills_missing_due_date,
        COALESCE(p.open_bills_missing_due_date, 0)
            AS open_bills_missing_due_date,

        COALESCE(p.bills_missing_supplier_id, 0)
            AS bills_missing_supplier_id,

        COALESCE(r.duplicate_flagged_invoices, 0)
            AS duplicate_flagged_invoices,
        COALESCE(p.duplicate_flagged_bills, 0)
            AS duplicate_flagged_bills,

        COALESCE(r.invoice_payment_mismatch_flags, 0)
            AS invoice_payment_mismatch_flags,
        COALESCE(p.bill_payment_mismatch_flags, 0)
            AS bill_payment_mismatch_flags,

        COALESCE(r.payments_before_invoice_flags, 0)
            AS payments_before_invoice_flags,
        COALESCE(p.payments_before_bill_flags, 0)
            AS payments_before_bill_flags,

        COALESCE(r.invoice_ledger_conflicts, 0)
            AS invoice_ledger_conflicts,
        COALESCE(p.bill_ledger_conflicts, 0)
            AS bill_ledger_conflicts,

        COALESCE(r.invoices_unmatched_needing_investigation, 0)
            AS invoices_unmatched_needing_investigation,
        COALESCE(p.bills_unmatched_needing_investigation, 0)
            AS bills_unmatched_needing_investigation,

        COALESCE(r.open_invoices_without_due_dates, 0)
            AS open_invoices_without_due_dates,
        COALESCE(p.open_bills_without_due_dates, 0)
            AS open_bills_without_due_dates,

        COALESCE(r.duplicate_invoice_outstanding_exposure, 0)
            AS duplicate_invoice_outstanding_exposure,
        COALESCE(r.invoice_payment_mismatch_exposure, 0)
            AS invoice_payment_mismatch_exposure,
        COALESCE(r.invoice_ledger_conflict_exposure, 0)
            AS invoice_ledger_conflict_exposure,
        COALESCE(r.unmatched_invoice_outstanding_exposure, 0)
            AS unmatched_invoice_outstanding_exposure,
        COALESCE(r.open_invoices_missing_due_date_exposure, 0)
            AS open_invoices_missing_due_date_exposure,

        COALESCE(p.duplicate_bill_outstanding_exposure, 0)
            AS duplicate_bill_outstanding_exposure,
        COALESCE(p.bill_payment_mismatch_exposure, 0)
            AS bill_payment_mismatch_exposure,
        COALESCE(p.bill_ledger_conflict_exposure, 0)
            AS bill_ledger_conflict_exposure,
        COALESCE(p.unmatched_bill_outstanding_exposure, 0)
            AS unmatched_bill_outstanding_exposure,
        COALESCE(p.open_bills_missing_due_date_exposure, 0)
            AS open_bills_missing_due_date_exposure,

        GREATEST(
            r.aging_as_of_date,
            p.aging_as_of_date
        ) AS aging_as_of_date

    FROM receivables_quality r
    FULL OUTER JOIN payables_quality p
        ON r.business_id = p.business_id
       AND r.currency = p.currency
)

SELECT
    *,

    invoice_record_count + bill_record_count
        AS total_document_records,

    duplicate_flagged_invoices + duplicate_flagged_bills
        AS total_duplicate_flagged_records,

    invoice_payment_mismatch_flags + bill_payment_mismatch_flags
        AS total_payment_mismatch_flags,

    invoice_ledger_conflicts + bill_ledger_conflicts
        AS total_ledger_conflict_records,

    invoices_unmatched_needing_investigation
        + bills_unmatched_needing_investigation
        AS total_unmatched_investigation_records,

    open_invoices_missing_due_date_exposure
        AS receivables_missing_due_date_exposure,

    open_bills_missing_due_date_exposure
        AS payables_missing_due_date_exposure,

    CURRENT_TIMESTAMP AS view_generated_at

FROM combined;
