
-- ============================================================
-- Orey Analytics
-- Phase 06 — Cash Flow Intelligence
-- Module 04: Expense Intelligence
-- Script 004: Expense Quality
--
-- Purpose:
-- Expose supplier-bill data-quality and reconciliation risks.
--
-- Source records remain unchanged.
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_expense_quality AS

SELECT
    b.source_record_id,
    b.business_id,
    bp.business_name,
    b.bill_id,
    b.supplier_id,
    b.currency,

    b.bill_date,
    b.bill_date_std,
    b.due_date,
    b.due_date_std,
    b.payment_date,
    b.payment_date_std,

    b.bill_amount,
    b.amount_paid,

    b.bill_amount - b.amount_paid
        AS indicative_bill_balance,

    b.bill_status,
    b.bill_status_standardized,

    b.reconciliation_status,
    b.reconciliation_reason,
    b.matched_bank_source_record_id,
    b.match_confidence,
    b.matched_bank_amount,
    b.amount_difference,

    b.missing_supplier_id
        AS missing_supplier_id_flag,

    b.paid_amount_mismatch
        AS paid_amount_mismatch_flag,

    b.payment_before_bill_flag,
    b.is_duplicate AS duplicate_bill_flag,

    (b.bill_date_std IS NULL)
        AS missing_standardized_bill_date_flag,

    (b.due_date_std IS NULL)
        AS missing_standardized_due_date_flag,

    (b.payment_date IS NOT NULL
        AND b.payment_date_std IS NULL)
        AS unparsed_payment_date_flag,

    (b.bill_amount IS NULL)
        AS missing_bill_amount_flag,

    (b.amount_paid IS NULL)
        AS missing_amount_paid_flag,

    (
        b.bill_amount < 0
    ) AS negative_bill_amount_flag,

    (
        b.amount_paid < 0
    ) AS negative_amount_paid_flag,

    (
        b.amount_paid > b.bill_amount
    ) AS amount_paid_exceeds_bill_amount_flag,

    (
        b.bill_date_std IS NOT NULL
        AND b.due_date_std IS NOT NULL
        AND b.due_date_std < b.bill_date_std
    ) AS due_date_before_bill_date_flag,

    (
        b.payment_date_std IS NOT NULL
        AND b.bill_date_std IS NOT NULL
        AND b.payment_date_std < b.bill_date_std
    ) AS payment_date_before_bill_date_flag,

    (
        b.reconciliation_status NOT IN (
            'matched_bank',
            'matched',
            'not_applicable'
        )
    ) AS reconciliation_requires_review_flag,

    (
        b.matched_bank_source_record_id IS NOT NULL
        AND (
            b.match_confidence IS NULL
            OR b.matched_bank_amount IS NULL
        )
    ) AS incomplete_bank_match_evidence_flag,

    (
        b.amount_difference IS NOT NULL
        AND b.amount_difference <> 0
    ) AS bank_match_amount_difference_flag,

    (
        b.bill_amount - b.amount_paid < 0
    ) AS negative_indicative_balance_flag,

    (
        b.missing_supplier_id
        OR b.paid_amount_mismatch
        OR b.payment_before_bill_flag
        OR b.is_duplicate
        OR b.bill_date_std IS NULL
        OR b.due_date_std IS NULL
        OR (
            b.payment_date IS NOT NULL
            AND b.payment_date_std IS NULL
        )
        OR b.bill_amount < 0
        OR b.amount_paid < 0
        OR b.amount_paid > b.bill_amount
        OR (
            b.due_date_std IS NOT NULL
            AND b.due_date_std < b.bill_date_std
        )
        OR (
            b.payment_date_std IS NOT NULL
            AND b.payment_date_std < b.bill_date_std
        )
        OR b.reconciliation_status NOT IN (
            'matched_bank',
            'matched',
            'not_applicable'
        )
        OR (
            b.amount_difference IS NOT NULL
            AND b.amount_difference <> 0
        )
    ) AS requires_quality_review_flag,

    FALSE AS accounting_expense_verified,
    FALSE AS bank_outflow_verified,

    CURRENT_TIMESTAMP AS view_generated_at

FROM processed.supplier_bills AS b

LEFT JOIN processed.business_profiles AS bp
    ON bp.business_id = b.business_id;
