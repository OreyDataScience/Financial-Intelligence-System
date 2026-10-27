
-- ============================================================
-- Orey Analytics
-- Phase 06 — Cash Flow Intelligence
-- Module 06 — Payment Behavior
-- Script 005: Consolidated Payment Behavior
--
-- Purpose:
-- Consolidate payment metrics, counterparty patterns,
-- and document quality indicators at business level.
--
-- Grain:
-- One row per business_id, currency, payment_direction.
--
-- Principles:
--   1. Aggregate counterparty patterns before joining.
--   2. Preserve recorded anomalies and missing identifiers.
--   3. Do not interpret recorded payments as verified cash.
--   4. Retain detailed diagnostics in the quality view.
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_consolidated_payment_behavior AS

WITH counterparty_patterns AS (

    -- --------------------------------------------------------
    -- Aggregate customer patterns to business level
    -- --------------------------------------------------------
    SELECT
        business_id,
        currency,
        'customer_receivable'::text AS payment_direction,

        COUNT(*) AS counterparty_pattern_group_count,

        SUM(invoice_record_count)
            AS pattern_document_record_count,

        SUM(distinct_invoice_id_count)
            AS grouped_distinct_document_id_count,

        SUM(invoices_with_paid_amount_at_least_invoice_amount)
            AS recorded_fully_paid_document_count,

        SUM(total_recorded_invoice_amount)
            AS pattern_recorded_document_amount,

        SUM(total_recorded_amount_paid)
            AS pattern_recorded_amount_paid,

        SUM(invoices_with_matched_bank_reference_count)
            AS pattern_matched_bank_reference_count,

        SUM(invoices_with_match_confidence_count)
            AS pattern_match_confidence_count

    FROM analytics.v_customer_payment_patterns

    GROUP BY
        business_id,
        currency

    UNION ALL

    -- --------------------------------------------------------
    -- Aggregate supplier patterns to business level
    -- --------------------------------------------------------
    SELECT
        business_id,
        currency,
        'supplier_payable'::text AS payment_direction,

        COUNT(*) AS counterparty_pattern_group_count,

        SUM(bill_record_count)
            AS pattern_document_record_count,

        SUM(distinct_bill_id_count)
            AS grouped_distinct_document_id_count,

        SUM(bills_with_paid_amount_at_least_bill_amount)
            AS recorded_fully_paid_document_count,

        SUM(total_recorded_bill_amount)
            AS pattern_recorded_document_amount,

        SUM(total_recorded_amount_paid)
            AS pattern_recorded_amount_paid,

        SUM(bills_with_matched_bank_reference_count)
            AS pattern_matched_bank_reference_count,

        SUM(bills_with_match_confidence_count)
            AS pattern_match_confidence_count

    FROM analytics.v_supplier_payment_patterns

    GROUP BY
        business_id,
        currency
)

SELECT
    m.business_id,
    m.currency,
    m.payment_direction,

    -- --------------------------------------------------------
    -- Core payment behavior metrics
    -- --------------------------------------------------------
    m.document_record_count,
    m.records_with_recorded_payment,

    m.recorded_early_payment_count,
    m.recorded_on_due_date_payment_count,
    m.recorded_late_payment_count,

    m.avg_days_document_to_payment,
    m.avg_days_from_due_date_to_payment,
    m.median_days_document_to_payment,

    m.total_recorded_document_amount,
    m.total_recorded_amount_paid,

    m.payment_before_document_flag_count,
    m.payment_amount_mismatch_count,
    m.duplicate_flagged_document_count,
    m.ledger_conflict_count,
    m.unmatched_investigation_count,
    m.missing_counterparty_id_count,

    m.payment_date_without_positive_paid_amount_count,
    m.positive_paid_amount_without_payment_date_count,
    m.payments_with_missing_due_date_count,

    -- --------------------------------------------------------
    -- Counterparty-level pattern summaries
    -- --------------------------------------------------------
    COALESCE(
        p.counterparty_pattern_group_count, 0
    ) AS counterparty_pattern_group_count,

    COALESCE(
        p.pattern_document_record_count, 0
    ) AS pattern_document_record_count,

    COALESCE(
        p.grouped_distinct_document_id_count, 0
    ) AS grouped_distinct_document_id_count,

    COALESCE(
        p.recorded_fully_paid_document_count, 0
    ) AS recorded_fully_paid_document_count,

    COALESCE(
        p.pattern_recorded_document_amount, 0
    ) AS pattern_recorded_document_amount,

    COALESCE(
        p.pattern_recorded_amount_paid, 0
    ) AS pattern_recorded_amount_paid,

    COALESCE(
        p.pattern_matched_bank_reference_count, 0
    ) AS pattern_matched_bank_reference_count,

    COALESCE(
        p.pattern_match_confidence_count, 0
    ) AS pattern_match_confidence_count,

    -- --------------------------------------------------------
    -- Quality indicators
    -- --------------------------------------------------------
    COALESCE(
        q.distinct_document_id_count, 0
    ) AS quality_distinct_document_id_count,

    COALESCE(
        q.missing_counterparty_id_count, 0
    ) AS quality_missing_counterparty_id_count,

    COALESCE(
        q.missing_document_date_count, 0
    ) AS missing_document_date_count,

    COALESCE(
        q.missing_due_date_count, 0
    ) AS quality_missing_due_date_count,

    COALESCE(
        q.missing_payment_date_count, 0
    ) AS missing_payment_date_count,

    COALESCE(
        q.recorded_payment_date_count, 0
    ) AS quality_recorded_payment_date_count,

    COALESCE(
        q.payment_date_without_positive_amount_count, 0
    ) AS quality_payment_date_without_positive_amount_count,

    COALESCE(
        q.positive_amount_without_payment_date_count, 0
    ) AS quality_positive_amount_without_payment_date_count,

    COALESCE(
        q.payment_before_document_flag_count, 0
    ) AS quality_payment_before_document_flag_count,

    COALESCE(
        q.payment_amount_mismatch_count, 0
    ) AS quality_payment_amount_mismatch_count,

    COALESCE(
        q.recorded_paid_amount_exceeds_document_amount_count, 0
    ) AS recorded_paid_amount_exceeds_document_amount_count,

    COALESCE(
        q.duplicate_flagged_document_count, 0
    ) AS quality_duplicate_flagged_document_count,

    COALESCE(
        q.ledger_conflict_count, 0
    ) AS quality_ledger_conflict_count,

    COALESCE(
        q.unmatched_investigation_count, 0
    ) AS quality_unmatched_investigation_count,

    COALESCE(
        q.documents_with_matched_bank_reference_count, 0
    ) AS quality_matched_bank_reference_count,

    COALESCE(
        q.documents_with_match_confidence_count, 0
    ) AS quality_match_confidence_count,

    -- --------------------------------------------------------
    -- Reconciliation checks between existing analytical views
    -- --------------------------------------------------------
    m.document_record_count
        - COALESCE(p.pattern_document_record_count, 0)
        AS metrics_pattern_record_count_difference,

    m.total_recorded_document_amount
        - COALESCE(p.pattern_recorded_document_amount, 0)
        AS metrics_pattern_document_amount_difference,

    m.total_recorded_amount_paid
        - COALESCE(p.pattern_recorded_amount_paid, 0)
        AS metrics_pattern_paid_amount_difference,

    -- --------------------------------------------------------
    -- Evidence and refresh metadata
    -- --------------------------------------------------------
    m.financial_evidence_basis,

    q.view_generated_at AS quality_view_generated_at,

    CURRENT_TIMESTAMP AS view_generated_at

FROM analytics.v_payment_behavior_metrics AS m

LEFT JOIN counterparty_patterns AS p
    ON  p.business_id = m.business_id
    AND p.currency IS NOT DISTINCT FROM m.currency
    AND p.payment_direction = m.payment_direction

LEFT JOIN analytics.v_payment_behavior_quality AS q
    ON  q.business_id = m.business_id
    AND q.currency IS NOT DISTINCT FROM m.currency
    AND q.payment_direction = m.payment_direction;
