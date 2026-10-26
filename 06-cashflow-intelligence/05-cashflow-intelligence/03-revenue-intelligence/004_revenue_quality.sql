
-- ============================================================
-- Orey Analytics
-- Phase 06 — Cash Flow Intelligence
-- Module 03 — Revenue Intelligence
-- File: 004_revenue_quality.sql
--
-- Purpose:
-- Expose invoice-level data-quality and reconciliation risks.
--
-- Design:
-- - Preserve original source records.
-- - Do not silently correct or exclude flagged records.
-- - Keep issue indicators separate for transparent review.
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_revenue_quality AS

SELECT
    i.source_record_id,
    i.business_id,
    bp.business_name,
    bp.accounting_basis,

    i.invoice_id,
    i.customer_id,
    i.currency,

    i.invoice_date,
    i.due_date,
    i.payment_date,

    i.invoice_date_std AS standardized_invoice_date,
    i.due_date_std AS standardized_due_date,
    i.payment_date_std AS standardized_payment_date,

    i.invoice_status,
    i.invoice_status_standardized,

    i.invoice_amount,
    i.amount_paid,

    GREATEST(
        COALESCE(i.invoice_amount, 0)
        - COALESCE(i.amount_paid, 0),
        0
    ) AS calculated_outstanding_amount,

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
        WHEN i.invoice_date_std IS NULL
            THEN TRUE
        ELSE FALSE
    END AS missing_standardized_invoice_date,

    CASE
        WHEN i.invoice_amount IS NULL
            THEN TRUE
        ELSE FALSE
    END AS missing_invoice_amount,

    CASE
        WHEN i.amount_paid IS NULL
            THEN TRUE
        ELSE FALSE
    END AS missing_amount_paid,

    CASE
        WHEN i.customer_id IS NULL
          OR BTRIM(i.customer_id) = ''
            THEN TRUE
        ELSE FALSE
    END AS missing_customer_identity,

    CASE
        WHEN i.invoice_amount < 0
          OR i.amount_paid < 0
            THEN TRUE
        ELSE FALSE
    END AS negative_monetary_value,

    CASE
        WHEN i.amount_paid > i.invoice_amount
         AND i.invoice_amount IS NOT NULL
         AND i.amount_paid IS NOT NULL
            THEN TRUE
        ELSE FALSE
    END AS payment_exceeds_invoice_amount,

    CASE
        WHEN i.payment_date_std IS NOT NULL
         AND i.invoice_date_std IS NOT NULL
         AND i.payment_date_std < i.invoice_date_std
            THEN TRUE
        ELSE FALSE
    END AS standardized_payment_before_invoice,

    CASE
        WHEN i.due_date_std IS NOT NULL
         AND i.invoice_date_std IS NOT NULL
         AND i.due_date_std < i.invoice_date_std
            THEN TRUE
        ELSE FALSE
    END AS due_date_before_invoice,

    CASE
        WHEN i.invoice_status_standardized IN (
            'unpaid', 'overdue', 'partially_paid'
        )
         AND i.invoice_amount IS NOT NULL
         AND i.amount_paid IS NOT NULL
         AND i.invoice_amount = i.amount_paid
            THEN TRUE
        ELSE FALSE
    END AS outstanding_status_with_fully_paid_amount,

    CASE
        WHEN i.invoice_status_standardized = 'paid'
         AND i.invoice_amount IS NOT NULL
         AND i.amount_paid IS NOT NULL
         AND i.amount_paid < i.invoice_amount
            THEN TRUE
        ELSE FALSE
    END AS paid_status_with_remaining_balance,

    (
        i.invoice_date_std IS NULL
        OR i.invoice_amount IS NULL
        OR i.amount_paid IS NULL
        OR i.missing_due_date = TRUE
        OR i.paid_amount_mismatch = TRUE
        OR i.payment_before_invoice_flag = TRUE
        OR i.is_duplicate = TRUE
        OR i.reconciliation_status = 'ledger_conflict'
        OR i.customer_id IS NULL
        OR BTRIM(i.customer_id) = ''
        OR i.invoice_amount < 0
        OR i.amount_paid < 0
        OR i.amount_paid > i.invoice_amount
        OR (
            i.due_date_std IS NOT NULL
            AND i.invoice_date_std IS NOT NULL
            AND i.due_date_std < i.invoice_date_std
        )
    ) AS has_revenue_data_quality_issue,

    CASE
        WHEN i.source_record_id IS NULL
            THEN 'source_record_identity_missing'
        WHEN i.invoice_amount IS NULL
          OR i.amount_paid IS NULL
            THEN 'missing_monetary_data'
        WHEN i.paid_amount_mismatch = TRUE
            THEN 'payment_amount_mismatch'
        WHEN i.is_duplicate = TRUE
            THEN 'duplicate_flagged'
        WHEN i.reconciliation_status = 'ledger_conflict'
            THEN 'ledger_conflict'
        WHEN i.invoice_date_std IS NULL
            THEN 'missing_invoice_date'
        WHEN i.missing_due_date = TRUE
            THEN 'missing_due_date'
        WHEN i.payment_before_invoice_flag = TRUE
            THEN 'payment_timing_flag'
        WHEN i.customer_id IS NULL
          OR BTRIM(i.customer_id) = ''
            THEN 'missing_customer_identity'
        WHEN i.invoice_amount < 0
          OR i.amount_paid < 0
          OR i.amount_paid > i.invoice_amount
            THEN 'monetary_value_review'
        ELSE 'record_available_review_required'
    END AS primary_quality_status,

    CURRENT_TIMESTAMP AS view_generated_at

FROM processed.invoices i

LEFT JOIN processed.business_profiles bp
    ON bp.business_id = i.business_id;
