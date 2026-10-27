
-- ============================================================
-- Orey Analytics
-- Phase 06 — Cash Flow Intelligence
-- Module 06 — Payment Behavior
-- Script 006: Payment Behavior Validation
--
-- Purpose:
-- Validate consolidated payment-behavior coverage,
-- reconciliation, quality-flag consistency and evidence limits.
--
-- This script does not modify source data or silently repair
-- inconsistencies.
-- ============================================================

-- 1. Consolidated coverage
SELECT
    COUNT(*) AS row_count,
    COUNT(DISTINCT business_id) AS business_count,
    COUNT(DISTINCT payment_direction) AS direction_count,
    COUNT(*) FILTER (
        WHERE payment_direction = 'customer_receivable'
    ) AS customer_receivable_rows,
    COUNT(*) FILTER (
        WHERE payment_direction = 'supplier_payable'
    ) AS supplier_payable_rows
FROM analytics.v_consolidated_payment_behavior;


-- 2. Expected business/payment-direction coverage
SELECT
    business_id,
    COUNT(*) AS row_count,
    COUNT(DISTINCT payment_direction) AS direction_count,
    STRING_AGG(
        payment_direction,
        ', ' ORDER BY payment_direction
    ) AS payment_directions
FROM analytics.v_consolidated_payment_behavior
GROUP BY business_id
HAVING COUNT(*) <> 2
    OR COUNT(DISTINCT payment_direction) <> 2
ORDER BY business_id;


-- 3. Metrics-to-counterparty pattern document reconciliation
SELECT
    business_id,
    currency,
    payment_direction,
    document_record_count,
    pattern_document_record_count,
    metrics_pattern_record_count_difference
FROM analytics.v_consolidated_payment_behavior
WHERE metrics_pattern_record_count_difference <> 0
ORDER BY business_id, payment_direction;


-- 4. Document amount and recorded paid amount reconciliation
SELECT
    business_id,
    currency,
    payment_direction,
    metrics_pattern_document_amount_difference,
    metrics_pattern_paid_amount_difference
FROM analytics.v_consolidated_payment_behavior
WHERE ABS(
        COALESCE(metrics_pattern_document_amount_difference, 0)
    ) > 0.02
   OR ABS(
        COALESCE(metrics_pattern_paid_amount_difference, 0)
    ) > 0.02
ORDER BY business_id, payment_direction;


-- 5. Core metrics-to-quality-view reconciliation
SELECT
    business_id,
    currency,
    payment_direction,
    payment_before_document_flag_count,
    quality_payment_before_document_flag_count,
    payment_amount_mismatch_count,
    quality_payment_amount_mismatch_count,
    duplicate_flagged_document_count,
    quality_duplicate_flagged_document_count,
    ledger_conflict_count,
    quality_ledger_conflict_count,
    unmatched_investigation_count,
    quality_unmatched_investigation_count
FROM analytics.v_consolidated_payment_behavior
WHERE payment_before_document_flag_count
          <> quality_payment_before_document_flag_count
   OR payment_amount_mismatch_count
          <> quality_payment_amount_mismatch_count
   OR duplicate_flagged_document_count
          <> quality_duplicate_flagged_document_count
   OR ledger_conflict_count
          <> quality_ledger_conflict_count
   OR unmatched_investigation_count
          <> quality_unmatched_investigation_count
ORDER BY business_id, payment_direction;


-- 6. Review unresolved payment-behavior quality indicators
SELECT
    business_id,
    currency,
    payment_direction,
    document_record_count,
    quality_missing_counterparty_id_count,
    missing_document_date_count,
    quality_missing_due_date_count,
    missing_payment_date_count,
    quality_payment_before_document_flag_count,
    recorded_paid_amount_exceeds_document_amount_count,
    quality_matched_bank_reference_count,
    quality_match_confidence_count
FROM analytics.v_consolidated_payment_behavior
WHERE quality_missing_counterparty_id_count > 0
   OR missing_document_date_count > 0
   OR quality_missing_due_date_count > 0
   OR missing_payment_date_count > 0
   OR quality_payment_before_document_flag_count > 0
   OR recorded_paid_amount_exceeds_document_amount_count > 0
ORDER BY business_id, payment_direction;


-- 7. Check for impossible or suspicious count relationships
SELECT
    business_id,
    currency,
    payment_direction,
    document_record_count,
    records_with_recorded_payment,
    recorded_early_payment_count,
    recorded_on_due_date_payment_count,
    recorded_late_payment_count,
    missing_payment_date_count
FROM analytics.v_consolidated_payment_behavior
WHERE records_with_recorded_payment > document_record_count
   OR recorded_early_payment_count > records_with_recorded_payment
   OR recorded_on_due_date_payment_count > records_with_recorded_payment
   OR recorded_late_payment_count > records_with_recorded_payment
   OR missing_payment_date_count > document_record_count
ORDER BY business_id, payment_direction;


-- 8. Consolidated financial evidence and coverage summary
SELECT
    payment_direction,
    SUM(document_record_count) AS total_document_records,
    SUM(records_with_recorded_payment) AS records_with_payment_dates,
    SUM(recorded_early_payment_count) AS recorded_early_payments,
    SUM(recorded_on_due_date_payment_count)
        AS recorded_on_due_date_payments,
    SUM(recorded_late_payment_count) AS recorded_late_payments,
    SUM(payment_before_document_flag_count)
        AS payment_before_document_flags,
    SUM(missing_payment_date_count) AS missing_payment_dates,
    SUM(quality_missing_counterparty_id_count)
        AS missing_counterparty_ids,
    SUM(quality_matched_bank_reference_count)
        AS matched_bank_reference_records,
    MIN(financial_evidence_basis) AS financial_evidence_basis
FROM analytics.v_consolidated_payment_behavior
GROUP BY payment_direction
ORDER BY payment_direction;


-- 9. Validation run timestamp
SELECT CURRENT_TIMESTAMP AS validation_run_at;
