
-- ============================================================
-- Orey Analytics
-- Phase 06 — Cash Flow Intelligence
-- Module 06 — Payment Behavior
-- Script 001: Payment Behavior Metrics
--
-- Purpose:
-- Summarise recorded customer invoice and supplier-bill
-- payment timing, payment amounts, and quality exceptions.
--
-- Important:
-- Recorded document payments are not necessarily verified
-- bank cash movements. Source records are not modified.
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_payment_behavior_metrics AS

WITH payment_documents AS (

    -- --------------------------------------------------------
    -- Customer invoices
    -- --------------------------------------------------------
    SELECT
        source_record_id,
        business_id,
        currency,
        'customer_receivable'::text AS payment_direction,
        customer_id AS counterparty_id,
        invoice_date_std AS document_date,
        due_date_std AS due_date,
        payment_date_std AS payment_date,
        invoice_amount AS document_amount,
        amount_paid AS recorded_amount_paid,
        is_duplicate,
        paid_amount_mismatch AS payment_amount_mismatch,
        payment_before_invoice_flag AS payment_before_document,
        reconciliation_status,
        matched_bank_source_record_id,
        match_confidence
    FROM processed.invoices

    UNION ALL

    -- --------------------------------------------------------
    -- Supplier bills
    -- --------------------------------------------------------
    SELECT
        source_record_id,
        business_id,
        currency,
        'supplier_payable'::text AS payment_direction,
        supplier_id AS counterparty_id,
        bill_date_std AS document_date,
        due_date_std AS due_date,
        payment_date_std AS payment_date,
        bill_amount AS document_amount,
        amount_paid AS recorded_amount_paid,
        is_duplicate,
        paid_amount_mismatch AS payment_amount_mismatch,
        payment_before_bill_flag AS payment_before_document,
        reconciliation_status,
        matched_bank_source_record_id,
        match_confidence
    FROM processed.supplier_bills
),

classified AS (
    SELECT
        *,

        (
            payment_date IS NOT NULL
            AND recorded_amount_paid > 0
        ) AS has_recorded_payment,

        CASE
            WHEN payment_date IS NULL
              OR due_date IS NULL
                THEN NULL
            ELSE payment_date - due_date
        END AS days_from_due_date_to_payment,

        CASE
            WHEN payment_date IS NULL
              OR document_date IS NULL
                THEN NULL
            ELSE payment_date - document_date
        END AS days_from_document_to_payment,

        (
            counterparty_id IS NULL
            OR BTRIM(counterparty_id) = ''
        ) AS missing_counterparty_id,

        (
            reconciliation_status = 'ledger_conflict'
        ) AS has_ledger_conflict,

        (
            reconciliation_status = 'unmatched_needs_investigation'
        ) AS needs_reconciliation_investigation

    FROM payment_documents
)

SELECT
    business_id,
    currency,
    payment_direction,

    COUNT(*) AS document_record_count,

    COUNT(*) FILTER (
        WHERE has_recorded_payment
    ) AS records_with_recorded_payment,

    COUNT(*) FILTER (
        WHERE payment_date IS NOT NULL
          AND COALESCE(recorded_amount_paid, 0) <= 0
    ) AS payment_date_without_positive_paid_amount_count,

    COUNT(*) FILTER (
        WHERE COALESCE(recorded_amount_paid, 0) > 0
          AND payment_date IS NULL
    ) AS positive_paid_amount_without_payment_date_count,

    COUNT(*) FILTER (
        WHERE payment_date IS NOT NULL
          AND due_date IS NULL
    ) AS payments_with_missing_due_date_count,

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
        AVG(days_from_document_to_payment::numeric) FILTER (
            WHERE has_recorded_payment
              AND days_from_document_to_payment IS NOT NULL
        ),
        2
    ) AS avg_days_document_to_payment,

    ROUND(
        AVG(days_from_due_date_to_payment::numeric) FILTER (
            WHERE has_recorded_payment
              AND days_from_due_date_to_payment IS NOT NULL
        ),
        2
    ) AS avg_days_from_due_date_to_payment,

    ROUND(
        PERCENTILE_CONT(0.5) WITHIN GROUP (
            ORDER BY days_from_document_to_payment
        ) FILTER (
            WHERE has_recorded_payment
              AND days_from_document_to_payment IS NOT NULL
        )::numeric,
        2
    ) AS median_days_document_to_payment,

    ROUND(
        SUM(COALESCE(recorded_amount_paid, 0)),
        2
    ) AS total_recorded_amount_paid,

    ROUND(
        SUM(COALESCE(document_amount, 0)),
        2
    ) AS total_recorded_document_amount,

    COUNT(*) FILTER (
        WHERE payment_before_document IS TRUE
    ) AS payment_before_document_flag_count,

    COUNT(*) FILTER (
        WHERE payment_amount_mismatch IS TRUE
    ) AS payment_amount_mismatch_count,

    COUNT(*) FILTER (
        WHERE is_duplicate IS TRUE
    ) AS duplicate_flagged_document_count,

    COUNT(*) FILTER (
        WHERE has_ledger_conflict
    ) AS ledger_conflict_count,

    COUNT(*) FILTER (
        WHERE needs_reconciliation_investigation
    ) AS unmatched_investigation_count,

    COUNT(*) FILTER (
        WHERE missing_counterparty_id
    ) AS missing_counterparty_id_count,

    COUNT(*) FILTER (
        WHERE matched_bank_source_record_id IS NOT NULL
    ) AS records_with_matched_bank_reference_count,

    COUNT(*) FILTER (
        WHERE match_confidence IS NOT NULL
    ) AS records_with_match_confidence_count,

    'Recorded invoice and supplier-bill fields; not independently verified cash'
        AS financial_evidence_basis,

    CURRENT_TIMESTAMP AS view_generated_at

FROM classified

GROUP BY
    business_id,
    currency,
    payment_direction;
