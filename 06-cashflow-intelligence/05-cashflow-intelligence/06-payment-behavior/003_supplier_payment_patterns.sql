
-- ============================================================
-- Orey Analytics
-- Phase 06 — Cash Flow Intelligence
-- Module 06 — Payment Behavior
-- Script 003: Supplier Payment Patterns
--
-- Purpose:
-- Analyse supplier-level recorded bill payment timing,
-- payment completion, and data-quality exceptions.
--
-- Important:
-- Recorded supplier-bill payments are not independently
-- verified cash movements. Source records remain unchanged.
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_supplier_payment_patterns AS

WITH supplier_bills AS (
    SELECT
        business_id,
        currency,
        supplier_id,
        source_record_id,
        bill_id,
        bill_date_std AS bill_date,
        due_date_std AS due_date,
        payment_date_std AS payment_date,
        bill_amount,
        amount_paid,
        bill_status_standardized,
        missing_supplier_id,
        is_duplicate,
        paid_amount_mismatch,
        payment_before_bill_flag,
        reconciliation_status,
        matched_bank_source_record_id,
        match_confidence
    FROM processed.supplier_bills
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
             AND bill_date IS NOT NULL
                THEN payment_date - bill_date
            ELSE NULL
        END AS days_from_bill_to_payment,

        CASE
            WHEN COALESCE(amount_paid, 0) >=
                 COALESCE(bill_amount, 0)
             AND COALESCE(bill_amount, 0) > 0
                THEN TRUE
            ELSE FALSE
        END AS recorded_as_fully_paid,

        (
            supplier_id IS NULL
            OR BTRIM(supplier_id) = ''
        ) AS missing_supplier_id_calculated

    FROM supplier_bills
)

SELECT
    business_id,
    currency,
    supplier_id,

    COUNT(*) AS bill_record_count,

    COUNT(DISTINCT bill_id) AS distinct_bill_id_count,

    COUNT(*) FILTER (
        WHERE payment_date IS NOT NULL
    ) AS bills_with_recorded_payment_date,

    COUNT(*) FILTER (
        WHERE recorded_as_fully_paid
    ) AS bills_with_paid_amount_at_least_bill_amount,

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
        SUM(COALESCE(bill_amount, 0)),
        2
    ) AS total_recorded_bill_amount,

    ROUND(
        SUM(COALESCE(amount_paid, 0)),
        2
    ) AS total_recorded_amount_paid,

    COUNT(*) FILTER (
        WHERE paid_amount_mismatch IS TRUE
    ) AS payment_amount_mismatch_count,

    COUNT(*) FILTER (
        WHERE payment_before_bill_flag IS TRUE
    ) AS payment_before_bill_flag_count,

    COUNT(*) FILTER (
        WHERE is_duplicate IS TRUE
    ) AS duplicate_flagged_bill_count,

    COUNT(*) FILTER (
        WHERE missing_supplier_id IS TRUE
           OR missing_supplier_id_calculated
    ) AS missing_supplier_id_count,

    COUNT(*) FILTER (
        WHERE reconciliation_status = 'ledger_conflict'
    ) AS ledger_conflict_count,

    COUNT(*) FILTER (
        WHERE reconciliation_status =
              'unmatched_needs_investigation'
    ) AS unmatched_investigation_count,

    COUNT(*) FILTER (
        WHERE matched_bank_source_record_id IS NOT NULL
    ) AS bills_with_matched_bank_reference_count,

    COUNT(*) FILTER (
        WHERE match_confidence IS NOT NULL
    ) AS bills_with_match_confidence_count,

    'Recorded supplier-bill fields; not independently verified cash'
        AS financial_evidence_basis,

    CURRENT_TIMESTAMP AS view_generated_at

FROM classified

GROUP BY
    business_id,
    currency,
    supplier_id;
