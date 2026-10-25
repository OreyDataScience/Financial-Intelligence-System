
-- ============================================================
-- Orey Analytics
-- Phase 06 — Cash Flow Intelligence
-- Module 02 — Liquidity
-- File: 002_receivables_liquidity.sql
--
-- Purpose:
-- Calculate invoice-level outstanding receivables and
-- collection indicators without modifying source data.
--
-- Important:
-- Outstanding invoices are not guaranteed future cash.
-- Missing due dates and reconciliation issues remain visible.
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_receivables_liquidity AS

WITH invoice_calculations AS (
    SELECT
        i.source_record_id,
        i.business_id,
        bp.business_name,
        i.invoice_id,
        i.customer_id,
        i.currency,

        i.invoice_date_std AS invoice_date,
        i.due_date_std AS due_date,
        i.payment_date_std AS payment_date,

        i.invoice_status_standardized AS invoice_status,

        i.invoice_amount,
        i.amount_paid,

        GREATEST(
            i.invoice_amount - i.amount_paid,
            0
        ) AS outstanding_amount,

        CASE
            WHEN i.due_date_std IS NOT NULL
             AND i.due_date_std < CURRENT_DATE
             AND i.invoice_amount > i.amount_paid
            THEN TRUE
            ELSE FALSE
        END AS is_past_due,

        CASE
            WHEN i.due_date_std IS NULL
             AND i.invoice_amount > i.amount_paid
            THEN TRUE
            ELSE FALSE
        END AS missing_due_date_with_outstanding,

        i.missing_due_date,
        i.paid_amount_mismatch,
        i.payment_before_invoice_flag,
        i.is_duplicate,
        i.reconciliation_status,
        i.reconciliation_reason,
        i.matched_bank_source_record_id,
        i.match_confidence,
        i.matched_bank_amount,
        i.amount_difference,

        CASE
            WHEN i.invoice_amount IS NULL
              OR i.amount_paid IS NULL
                THEN 'missing_monetary_data'

            WHEN i.paid_amount_mismatch = TRUE
                THEN 'payment_amount_mismatch'

            WHEN i.is_duplicate = TRUE
                THEN 'duplicate_flagged'

            WHEN i.due_date_std IS NULL
             AND i.invoice_amount > i.amount_paid
                THEN 'outstanding_due_date_missing'

            WHEN i.reconciliation_status = 'ledger_conflict'
                THEN 'ledger_conflict'

            ELSE 'record_available_review_required'
        END AS receivable_data_quality_status

    FROM processed.invoices i

    LEFT JOIN processed.business_profiles bp
        ON bp.business_id = i.business_id
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

    CASE
        WHEN invoice_status = 'paid'
            THEN 0::numeric
        ELSE outstanding_amount
    END AS status_adjusted_outstanding_amount,

    is_past_due,
    missing_due_date_with_outstanding,

    CASE
        WHEN invoice_amount > 0
        THEN ROUND(
            100.0 * amount_paid / invoice_amount,
            2
        )
        ELSE NULL
    END AS collection_percentage,

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

    CURRENT_TIMESTAMP AS view_generated_at

FROM invoice_calculations;
