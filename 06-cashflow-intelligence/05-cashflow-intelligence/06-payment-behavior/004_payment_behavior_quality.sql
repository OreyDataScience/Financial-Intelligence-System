
-- ============================================================
-- Orey Analytics
-- Phase 06 — Cash Flow Intelligence
-- Module 06 — Payment Behavior
-- Script 004: Payment Behavior Quality
--
-- Purpose:
-- Consolidate quality and reconciliation indicators from
-- customer invoices and supplier bills.
--
-- Principles:
--   1. Preserve source records and anomalies.
--   2. Flag issues rather than silently correcting them.
--   3. Do not equate recorded payments with verified cash.
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_payment_behavior_quality AS

WITH payment_documents AS (

    -- --------------------------------------------------------
    -- Customer invoices
    -- --------------------------------------------------------
    SELECT
        business_id,
        currency,
        'customer_receivable'::text AS payment_direction,
        source_record_id,
        invoice_id AS document_id,
        invoice_date_std AS document_date,
        due_date_std AS due_date,
        payment_date_std AS payment_date,
        invoice_amount AS document_amount,
        amount_paid,

        (
            customer_id IS NULL
            OR BTRIM(customer_id) = ''
        ) AS missing_counterparty_id,

        (
            invoice_date_std IS NULL
        ) AS missing_document_date,

        (
            missing_due_date IS TRUE
            OR due_date_std IS NULL
        ) AS missing_due_date,

        payment_before_invoice_flag
            AS payment_before_document_flag,

        paid_amount_mismatch,
        is_duplicate,
        reconciliation_status,
        matched_bank_source_record_id,
        match_confidence

    FROM processed.invoices

    UNION ALL

    -- --------------------------------------------------------
    -- Supplier bills
    -- --------------------------------------------------------
    SELECT
        business_id,
        currency,
        'supplier_payable'::text AS payment_direction,
        source_record_id,
        bill_id AS document_id,
        bill_date_std AS document_date,
        due_date_std AS due_date,
        payment_date_std AS payment_date,
        bill_amount AS document_amount,
        amount_paid,

        (
            missing_supplier_id IS TRUE
            OR supplier_id IS NULL
            OR BTRIM(supplier_id) = ''
        ) AS missing_counterparty_id,

        (
            bill_date_std IS NULL
        ) AS missing_document_date,

        (
            due_date_std IS NULL
        ) AS missing_due_date,

        payment_before_bill_flag
            AS payment_before_document_flag,

        paid_amount_mismatch,
        is_duplicate,
        reconciliation_status,
        matched_bank_source_record_id,
        match_confidence

    FROM processed.supplier_bills
),

quality_flags AS (
    SELECT
        *,

        (
            payment_date IS NOT NULL
            AND COALESCE(amount_paid, 0) <= 0
        ) AS payment_date_without_positive_amount,

        (
            payment_date IS NULL
            AND COALESCE(amount_paid, 0) > 0
        ) AS positive_amount_without_payment_date,

        (
            document_amount IS NOT NULL
            AND amount_paid IS NOT NULL
            AND amount_paid > document_amount
        ) AS recorded_paid_amount_exceeds_document_amount

    FROM payment_documents
)

SELECT
    business_id,
    currency,
    payment_direction,

    COUNT(*) AS document_record_count,

    COUNT(DISTINCT document_id)
        AS distinct_document_id_count,

    COUNT(*) FILTER (
        WHERE missing_counterparty_id
    ) AS missing_counterparty_id_count,

    COUNT(*) FILTER (
        WHERE missing_document_date
    ) AS missing_document_date_count,

    COUNT(*) FILTER (
        WHERE missing_due_date
    ) AS missing_due_date_count,

    COUNT(*) FILTER (
        WHERE payment_date IS NULL
    ) AS missing_payment_date_count,

    COUNT(*) FILTER (
        WHERE payment_date IS NOT NULL
    ) AS recorded_payment_date_count,

    COUNT(*) FILTER (
        WHERE payment_date_without_positive_amount
    ) AS payment_date_without_positive_amount_count,

    COUNT(*) FILTER (
        WHERE positive_amount_without_payment_date
    ) AS positive_amount_without_payment_date_count,

    COUNT(*) FILTER (
        WHERE payment_before_document_flag IS TRUE
    ) AS payment_before_document_flag_count,

    COUNT(*) FILTER (
        WHERE paid_amount_mismatch IS TRUE
    ) AS payment_amount_mismatch_count,

    COUNT(*) FILTER (
        WHERE recorded_paid_amount_exceeds_document_amount
    ) AS recorded_paid_amount_exceeds_document_amount_count,

    COUNT(*) FILTER (
        WHERE is_duplicate IS TRUE
    ) AS duplicate_flagged_document_count,

    COUNT(*) FILTER (
        WHERE reconciliation_status = 'ledger_conflict'
    ) AS ledger_conflict_count,

    COUNT(*) FILTER (
        WHERE reconciliation_status =
              'unmatched_needs_investigation'
    ) AS unmatched_investigation_count,

    COUNT(*) FILTER (
        WHERE matched_bank_source_record_id IS NOT NULL
    ) AS documents_with_matched_bank_reference_count,

    COUNT(*) FILTER (
        WHERE match_confidence IS NOT NULL
    ) AS documents_with_match_confidence_count,

    'Recorded invoice and supplier-bill fields; '
        || 'quality flags are investigation signals, '
        || 'not independent proof of cash settlement'
        AS financial_evidence_basis,

    CURRENT_TIMESTAMP AS view_generated_at

FROM quality_flags

GROUP BY
    business_id,
    currency,
    payment_direction;
