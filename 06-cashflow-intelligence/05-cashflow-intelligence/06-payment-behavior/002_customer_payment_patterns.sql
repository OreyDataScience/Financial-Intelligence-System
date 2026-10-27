
-- ============================================================
-- Orey Analytics
-- Phase 06 — Cash Flow Intelligence
-- Module 06 — Payment Behavior
-- Script 002: Customer Payment Patterns
--
-- Purpose:
-- Analyse customer-level recorded invoice payment timing,
-- payment completion, and data-quality exceptions.
--
-- Important:
-- Recorded invoice payments are not independently verified
-- cash movements. Source records remain unchanged.
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_customer_payment_patterns AS

WITH customer_invoices AS (
    SELECT
        business_id,
        currency,
        customer_id,
        source_record_id,
        invoice_id,
        invoice_date_std AS invoice_date,
        due_date_std AS due_date,
        payment_date_std AS payment_date,
        invoice_amount,
        amount_paid,
        invoice_status_standardized,
        is_duplicate,
        paid_amount_mismatch,
        payment_before_invoice_flag,
        reconciliation_status,
        matched_bank_source_record_id,
        match_confidence
    FROM processed.invoices
),

classified AS (
    SELECT
        *,
        CASE
            WHEN payment_date IS NOT NULL
             AND due_date IS NOT NULL
                THEN payment_date - due_date
            ELSE NULL
        END AS days_from_due_date_to_payment,

        CASE
            WHEN payment_date IS NOT NULL
             AND invoice_date IS NOT NULL
                THEN payment_date - invoice_date
            ELSE NULL
        END AS days_from_invoice_to_payment,

        CASE
            WHEN COALESCE(amount_paid, 0) >=
                 COALESCE(invoice_amount, 0)
             AND COALESCE(invoice_amount, 0) > 0
                THEN TRUE
            ELSE FALSE
        END AS recorded_as_fully_paid,

        (
            customer_id IS NULL
            OR BTRIM(customer_id) = ''
        ) AS missing_customer_id

    FROM customer_invoices
)

SELECT
    business_id,
    currency,
    customer_id,

    COUNT(*) AS invoice_record_count,

    COUNT(DISTINCT invoice_id) AS distinct_invoice_id_count,

    COUNT(*) FILTER (
        WHERE payment_date IS NOT NULL
    ) AS invoices_with_recorded_payment_date,

    COUNT(*) FILTER (
        WHERE recorded_as_fully_paid
    ) AS invoices_with_paid_amount_at_least_invoice_amount,

    COUNT(*) FILTER (
        WHERE payment_date IS NOT NULL
          AND due_date IS NOT NULL
          AND payment_date < due_date
    ) AS recorded_early_payment_count,

    COUNT(*) FILTER (
        WHERE payment_date IS NOT NULL
          AND due_date IS NOT NULL
          AND payment_date = due_date
    ) AS recorded_on_due_date_payment_count,

    COUNT(*) FILTER (
        WHERE payment_date IS NOT NULL
          AND due_date IS NOT NULL
          AND payment_date > due_date
    ) AS recorded_late_payment_count,

    ROUND(
        AVG(days_from_due_date_to_payment::numeric) FILTER (
            WHERE payment_date IS NOT NULL
              AND due_date IS NOT NULL
        ),
        2
    ) AS avg_days_from_due_date_to_payment,

    ROUND(
        PERCENTILE_CONT(0.5) WITHIN GROUP (
            ORDER BY days_from_due_date_to_payment
        ) FILTER (
            WHERE days_from_due_date_to_payment IS NOT NULL
        )::numeric,
        2
    ) AS median_days_from_due_date_to_payment,

    ROUND(
        SUM(COALESCE(invoice_amount, 0)),
        2
    ) AS total_recorded_invoice_amount,

    ROUND(
        SUM(COALESCE(amount_paid, 0)),
        2
    ) AS total_recorded_amount_paid,

    COUNT(*) FILTER (
        WHERE paid_amount_mismatch IS TRUE
    ) AS payment_amount_mismatch_count,

    COUNT(*) FILTER (
        WHERE payment_before_invoice_flag IS TRUE
    ) AS payment_before_invoice_flag_count,

    COUNT(*) FILTER (
        WHERE is_duplicate IS TRUE
    ) AS duplicate_flagged_invoice_count,

    COUNT(*) FILTER (
        WHERE reconciliation_status = 'ledger_conflict'
    ) AS ledger_conflict_count,

    COUNT(*) FILTER (
        WHERE reconciliation_status =
              'unmatched_needs_investigation'
    ) AS unmatched_investigation_count,

    COUNT(*) FILTER (
        WHERE matched_bank_source_record_id IS NOT NULL
    ) AS invoices_with_matched_bank_reference_count,

    COUNT(*) FILTER (
        WHERE match_confidence IS NOT NULL
    ) AS invoices_with_match_confidence_count,

    'Recorded invoice fields; not independently verified cash'
        AS financial_evidence_basis,

    CURRENT_TIMESTAMP AS view_generated_at

FROM classified

GROUP BY
    business_id,
    currency,
    customer_id;
