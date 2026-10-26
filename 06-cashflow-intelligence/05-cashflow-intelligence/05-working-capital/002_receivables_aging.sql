
-- ============================================================
-- Orey Analytics
-- Phase 06 — Cash Flow Intelligence
-- Module 05 — Working Capital
-- Script 002: Receivables Aging
--
-- Purpose:
-- Classify invoice records by due-date aging and expose
-- outstanding balances and data-quality concerns.
--
-- Important:
-- Aging uses CURRENT_DATE and is therefore a current snapshot.
-- Missing due dates are not treated as current or overdue.
-- Invoice payment records are not proof of bank receipts.
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_receivables_aging AS

WITH aging_base AS (
    SELECT
        source_record_id,
        business_id,
        business_name,
        invoice_id,
        customer_id,
        currency,
        invoice_date,
        due_date,
        payment_date,
        invoice_status,
        invoice_amount,
        amount_paid,
        outstanding_amount,
        status_adjusted_outstanding_amount,
        is_past_due,
        missing_due_date_with_outstanding,
        missing_due_date,
        paid_amount_mismatch,
        payment_before_invoice_flag,
        is_duplicate,
        reconciliation_status,
        reconciliation_reason,
        matched_bank_source_record_id,
        match_confidence,
        matched_bank_amount,
        amount_difference,
        receivable_data_quality_status,

        CASE
            WHEN due_date IS NULL THEN NULL
            ELSE CURRENT_DATE - due_date
        END AS days_from_due_date

    FROM analytics.v_receivables_liquidity
)

SELECT
    source_record_id,
    business_id,
    business_name,
    invoice_id,
    customer_id,
    currency,
    invoice_date,
    due_date,
    payment_date,
    invoice_status,
    invoice_amount,
    amount_paid,
    outstanding_amount,
    status_adjusted_outstanding_amount,

    days_from_due_date,

    CASE
        WHEN due_date IS NULL
            THEN 'due_date_missing'
        WHEN status_adjusted_outstanding_amount <= 0
            THEN 'no_outstanding_balance'
        WHEN due_date >= CURRENT_DATE
            THEN 'not_yet_due'
        WHEN days_from_due_date BETWEEN 1 AND 30
            THEN 'overdue_1_30_days'
        WHEN days_from_due_date BETWEEN 31 AND 60
            THEN 'overdue_31_60_days'
        WHEN days_from_due_date BETWEEN 61 AND 90
            THEN 'overdue_61_90_days'
        WHEN days_from_due_date > 90
            THEN 'overdue_over_90_days'
        ELSE 'requires_review'
    END AS receivables_aging_band,

    CASE
        WHEN due_date IS NULL
             AND status_adjusted_outstanding_amount > 0
            THEN 'outstanding_due_date_missing'
        WHEN due_date IS NULL
            THEN 'due_date_missing_no_adjusted_outstanding'
        WHEN status_adjusted_outstanding_amount <= 0
            THEN 'no_adjusted_outstanding'
        WHEN due_date < CURRENT_DATE
            THEN 'overdue'
        ELSE 'not_yet_due'
    END AS receivables_due_status,

    is_past_due,
    missing_due_date_with_outstanding,
    missing_due_date,
    paid_amount_mismatch,
    payment_before_invoice_flag,
    is_duplicate,
    reconciliation_status,
    reconciliation_reason,
    matched_bank_source_record_id,
    match_confidence,
    matched_bank_amount,
    amount_difference,
    receivable_data_quality_status,

    CURRENT_DATE AS aging_as_of_date,
    CURRENT_TIMESTAMP AS view_generated_at

FROM aging_base;
