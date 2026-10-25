
-- ============================================================
-- Orey Analytics
-- Phase 06 — Cash Flow Intelligence
-- Module 02 — Liquidity
-- File: 003_payables_liquidity.sql
--
-- Purpose:
-- Calculate supplier-bill outstanding amounts and payment
-- indicators without modifying source data.
--
-- Important:
-- Outstanding bills are not guaranteed immediate cash outflows.
-- Missing data and reconciliation issues remain visible.
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_payables_liquidity AS

WITH bill_calculations AS (
    SELECT
        b.source_record_id,
        b.business_id,
        bp.business_name,
        b.bill_id,
        b.supplier_id,
        b.currency,

        b.bill_date_std AS bill_date,
        b.due_date_std AS due_date,
        b.payment_date_std AS payment_date,

        b.bill_status_standardized AS bill_status,

        b.bill_amount,
        b.amount_paid,

        GREATEST(
            b.bill_amount - b.amount_paid,
            0
        ) AS outstanding_amount,

        CASE
            WHEN b.due_date_std IS NOT NULL
             AND b.due_date_std < CURRENT_DATE
             AND b.bill_amount > b.amount_paid
            THEN TRUE
            ELSE FALSE
        END AS is_past_due,

        CASE
            WHEN b.due_date_std IS NULL
             AND b.bill_amount > b.amount_paid
            THEN TRUE
            ELSE FALSE
        END AS missing_due_date_with_outstanding,

        b.missing_supplier_id,
        b.paid_amount_mismatch,
        b.payment_before_bill_flag,
        b.is_duplicate,
        b.reconciliation_status,
        b.reconciliation_reason,
        b.matched_bank_source_record_id,
        b.match_confidence,
        b.matched_bank_amount,
        b.amount_difference,

        CASE
            WHEN b.bill_amount IS NULL
              OR b.amount_paid IS NULL
                THEN 'missing_monetary_data'

            WHEN b.paid_amount_mismatch = TRUE
                THEN 'payment_amount_mismatch'

            WHEN b.is_duplicate = TRUE
                THEN 'duplicate_flagged'

            WHEN b.missing_supplier_id = TRUE
                THEN 'missing_supplier_identity'

            WHEN b.reconciliation_status = 'ledger_conflict'
                THEN 'ledger_conflict'

            ELSE 'record_available_review_required'
        END AS payable_data_quality_status

    FROM processed.supplier_bills b

    LEFT JOIN processed.business_profiles bp
        ON bp.business_id = b.business_id
)

SELECT
    source_record_id,
    business_id,
    business_name,
    bill_id,
    supplier_id,
    currency,

    bill_date,
    due_date,
    payment_date,
    bill_status,

    bill_amount,
    amount_paid,
    outstanding_amount,

    CASE
        WHEN bill_status = 'paid'
            THEN 0::numeric
        ELSE outstanding_amount
    END AS status_adjusted_outstanding_amount,

    is_past_due,
    missing_due_date_with_outstanding,

    CASE
        WHEN bill_amount > 0
        THEN ROUND(
            100.0 * amount_paid / bill_amount,
            2
        )
        ELSE NULL
    END AS payment_percentage,

    missing_supplier_id,
    paid_amount_mismatch,
    payment_before_bill_flag,
    is_duplicate,

    reconciliation_status,
    reconciliation_reason,
    matched_bank_source_record_id,
    match_confidence,
    matched_bank_amount,
    amount_difference,

    payable_data_quality_status,

    CURRENT_TIMESTAMP AS view_generated_at

FROM bill_calculations;
