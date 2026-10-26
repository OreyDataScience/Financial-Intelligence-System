-- ============================================================
-- Orey Analytics
-- Phase 06 — Cash Flow Intelligence
-- Module 05 — Working Capital
-- Script 006 — Working Capital Validation
--
-- Read-only validation of analytics Working Capital views.
-- No source data is modified, deleted, or repaired.
--
-- Evidence basis:
-- Invoice and supplier-bill records are not verified cash.
-- ============================================================

WITH
receivables AS (
    SELECT
        business_id,
        currency,
        COUNT(*) AS record_count,
        COALESCE(SUM(status_adjusted_outstanding_amount), 0)
            AS outstanding_balance,
        COALESCE(
            SUM(status_adjusted_outstanding_amount)
            FILTER (WHERE is_past_due IS TRUE), 0
        ) AS overdue_balance,
        COUNT(*) FILTER (WHERE is_past_due IS TRUE)
            AS overdue_count,
        COALESCE(
            SUM(status_adjusted_outstanding_amount)
            FILTER (
                WHERE due_date IS NULL
                  AND status_adjusted_outstanding_amount > 0
            ), 0
        ) AS missing_due_date_exposure,
        COUNT(*) FILTER (
            WHERE due_date IS NULL
              AND status_adjusted_outstanding_amount > 0
        ) AS open_missing_due_date_count,
        COUNT(*) FILTER (WHERE is_duplicate IS TRUE)
            AS duplicate_count,
        COUNT(*) FILTER (WHERE paid_amount_mismatch IS TRUE)
            AS payment_mismatch_count,
        COUNT(*) FILTER (WHERE payment_before_invoice_flag IS TRUE)
            AS payment_before_document_count,
        COUNT(*) FILTER (
            WHERE reconciliation_status = 'ledger_conflict'
        ) AS ledger_conflict_count,
        COUNT(*) FILTER (
            WHERE reconciliation_status = 'unmatched_needs_investigation'
        ) AS unmatched_count,
        COUNT(*) FILTER (
            WHERE receivables_aging_band IS NULL
               OR receivables_aging_band NOT IN (
                    'due_date_missing',
                    'no_outstanding_balance',
                    'not_yet_due',
                    'overdue_1_30_days',
                    'overdue_31_60_days',
                    'overdue_61_90_days',
                    'overdue_over_90_days',
                    'requires_review'
               )
        ) AS aging_band_errors,
        COUNT(*) FILTER (
            WHERE due_date IS NULL
              AND receivables_aging_band IS DISTINCT FROM 'due_date_missing'
        ) AS missing_date_band_errors,
        COUNT(*) FILTER (
            WHERE due_date IS NOT NULL
              AND receivables_aging_band = 'due_date_missing'
        ) AS unexpected_missing_date_band_count,
        COUNT(*) FILTER (
            WHERE is_past_due IS DISTINCT FROM (
                due_date IS NOT NULL
                AND due_date < CURRENT_DATE
                AND invoice_amount > amount_paid
            )
        ) AS overdue_flag_errors
    FROM analytics.v_receivables_aging
    GROUP BY business_id, currency
),

payables AS (
    SELECT
        business_id,
        currency,
        COUNT(*) AS record_count,
        COALESCE(SUM(status_adjusted_outstanding_amount), 0)
            AS outstanding_balance,
        COALESCE(
            SUM(status_adjusted_outstanding_amount)
            FILTER (WHERE is_past_due IS TRUE), 0
        ) AS overdue_balance,
        COUNT(*) FILTER (WHERE is_past_due IS TRUE)
            AS overdue_count,
        COALESCE(
            SUM(status_adjusted_outstanding_amount)
            FILTER (
                WHERE due_date IS NULL
                  AND status_adjusted_outstanding_amount > 0
            ), 0
        ) AS missing_due_date_exposure,
        COUNT(*) FILTER (
            WHERE due_date IS NULL
              AND status_adjusted_outstanding_amount > 0
        ) AS open_missing_due_date_count,
        COUNT(*) FILTER (WHERE is_duplicate IS TRUE)
            AS duplicate_count,
        COUNT(*) FILTER (WHERE paid_amount_mismatch IS TRUE)
            AS payment_mismatch_count,
        COUNT(*) FILTER (WHERE payment_before_bill_flag IS TRUE)
            AS payment_before_document_count,
        COUNT(*) FILTER (
            WHERE reconciliation_status = 'ledger_conflict'
        ) AS ledger_conflict_count,
        COUNT(*) FILTER (
            WHERE reconciliation_status = 'unmatched_needs_investigation'
        ) AS unmatched_count,
        COUNT(*) FILTER (
            WHERE payables_aging_band IS NULL
               OR payables_aging_band NOT IN (
                    'due_date_missing',
                    'no_outstanding_balance',
                    'not_yet_due',
                    'overdue_1_30_days',
                    'overdue_31_60_days',
                    'overdue_61_90_days',
                    'overdue_over_90_days',
                    'requires_review'
               )
        ) AS aging_band_errors,
        COUNT(*) FILTER (
            WHERE due_date IS NULL
              AND payables_aging_band IS DISTINCT FROM 'due_date_missing'
        ) AS missing_date_band_errors,
        COUNT(*) FILTER (
            WHERE due_date IS NOT NULL
              AND payables_aging_band = 'due_date_missing'
        ) AS unexpected_missing_date_band_count,
        COUNT(*) FILTER (
            WHERE is_past_due IS DISTINCT FROM (
                due_date IS NOT NULL
                AND due_date < CURRENT_DATE
                AND bill_amount > amount_paid
            )
        ) AS overdue_flag_errors
    FROM analytics.v_payables_aging
    GROUP BY business_id, currency
),

consolidated AS (
    SELECT *
    FROM analytics.v_consolidated_working_capital
),

quality AS (
    SELECT *
    FROM analytics.v_working_capital_quality
),

checks AS (
    -- Check that both source views contain records.
    SELECT
        'Receivables source groups present' AS check_name,
        CASE WHEN COUNT(*) > 0 THEN 'PASS' ELSE 'FAIL' END AS status,
        COUNT(*)::text AS observed_value,
        '> 0' AS expected_value,
        'Grouped business/currency combinations in the receivables view.'
            AS details
    FROM receivables

    UNION ALL

    SELECT
        'Payables source groups present',
        CASE WHEN COUNT(*) > 0 THEN 'PASS' ELSE 'FAIL' END,
        COUNT(*)::text,
        '> 0',
        'Grouped business/currency combinations in the payables view.'
    FROM payables

    UNION ALL

    -- Record-count reconciliation.
    SELECT
        'Receivables record counts reconcile',
        'FAIL',
        COALESCE(r.record_count::text, 'MISSING'),
        COALESCE(c.invoice_record_count::text, 'MISSING'),
        'Aging-view row count versus consolidated invoice_record_count.'
    FROM receivables r
    FULL JOIN consolidated c USING (business_id, currency)
    WHERE r.record_count IS DISTINCT FROM c.invoice_record_count

    UNION ALL

    SELECT
        'Payables record counts reconcile',
        'FAIL',
        COALESCE(p.record_count::text, 'MISSING'),
        COALESCE(c.bill_record_count::text, 'MISSING'),
        'Aging-view row count versus consolidated bill_record_count.'
    FROM payables p
    FULL JOIN consolidated c USING (business_id, currency)
    WHERE p.record_count IS DISTINCT FROM c.bill_record_count

    UNION ALL

    -- Balance reconciliation.
    SELECT
        'Receivables balances reconcile',
        'FAIL',
        ROUND(r.outstanding_balance, 2)::text,
        ROUND(c.recorded_outstanding_receivables, 2)::text,
        'Status-adjusted receivables versus consolidated receivables.'
    FROM receivables r
    JOIN consolidated c USING (business_id, currency)
    WHERE ABS(r.outstanding_balance
              - c.recorded_outstanding_receivables) >= 0.01

    UNION ALL

    SELECT
        'Payables balances reconcile',
        'FAIL',
        ROUND(p.outstanding_balance, 2)::text,
        ROUND(c.recorded_outstanding_payables, 2)::text,
        'Status-adjusted payables versus consolidated payables.'
    FROM payables p
    JOIN consolidated c USING (business_id, currency)
    WHERE ABS(p.outstanding_balance
              - c.recorded_outstanding_payables) >= 0.01

    UNION ALL

    SELECT
        'Net recorded position reconciles',
        'FAIL',
        ROUND(net_recorded_receivables_after_payables, 2)::text,
        ROUND(recorded_outstanding_receivables
              - recorded_outstanding_payables, 2)::text,
        'Net recorded position equals receivables less payables.'
    FROM consolidated
    WHERE ABS(
        net_recorded_receivables_after_payables
        - (recorded_outstanding_receivables
           - recorded_outstanding_payables)
    ) >= 0.01

    UNION ALL

    -- Missing due-date exposure reconciliation.
    SELECT
        'Receivables missing-date exposure reconciles',
        'FAIL',
        ROUND(r.missing_due_date_exposure, 2)::text,
        ROUND(c.receivables_missing_due_date_exposure, 2)::text,
        'Open receivables with missing due dates.'
    FROM receivables r
    JOIN consolidated c USING (business_id, currency)
    WHERE ABS(
        r.missing_due_date_exposure
        - c.receivables_missing_due_date_exposure
    ) >= 0.01

    UNION ALL

    SELECT
        'Payables missing-date exposure reconciles',
        'FAIL',
        ROUND(p.missing_due_date_exposure, 2)::text,
        ROUND(c.payables_missing_due_date_exposure, 2)::text,
        'Open payables with missing due dates.'
    FROM payables p
    JOIN consolidated c USING (business_id, currency)
    WHERE ABS(
        p.missing_due_date_exposure
        - c.payables_missing_due_date_exposure
    ) >= 0.01

    UNION ALL

    SELECT
        'Receivables missing-date counts reconcile',
        'FAIL',
        r.open_missing_due_date_count::text,
        c.open_invoice_missing_due_date_count::text,
        'Open invoices missing due dates.'
    FROM receivables r
    JOIN consolidated c USING (business_id, currency)
    WHERE r.open_missing_due_date_count
          IS DISTINCT FROM c.open_invoice_missing_due_date_count

    UNION ALL

    SELECT
        'Payables missing-date counts reconcile',
        'FAIL',
        p.open_missing_due_date_count::text,
        c.open_bill_missing_due_date_count::text,
        'Open bills missing due dates.'
    FROM payables p
    JOIN consolidated c USING (business_id, currency)
    WHERE p.open_missing_due_date_count
          IS DISTINCT FROM c.open_bill_missing_due_date_count

    UNION ALL

    -- Aging classifications.
    SELECT
        'Receivables aging classifications',
        CASE WHEN SUM(
            aging_band_errors
            + missing_date_band_errors
            + unexpected_missing_date_band_count
        ) = 0 THEN 'PASS' ELSE 'FAIL' END,
        SUM(aging_band_errors)::text || ' invalid/missing bands; '
        || SUM(missing_date_band_errors)::text || ' missing-date errors; '
        || SUM(unexpected_missing_date_band_count)::text
        || ' unexpected missing-date bands',
        'All counts = 0',
        'Validates actual receivables_aging_band values.'
    FROM receivables

    UNION ALL

    SELECT
        'Payables aging classifications',
        CASE WHEN SUM(
            aging_band_errors
            + missing_date_band_errors
            + unexpected_missing_date_band_count
        ) = 0 THEN 'PASS' ELSE 'FAIL' END,
        SUM(aging_band_errors)::text || ' invalid/missing bands; '
        || SUM(missing_date_band_errors)::text || ' missing-date errors; '
        || SUM(unexpected_missing_date_band_count)::text
        || ' unexpected missing-date bands',
        'All counts = 0',
        'Validates actual payables_aging_band values.'
    FROM payables

    UNION ALL

    -- Overdue flag consistency.
    SELECT
        'Receivables overdue flags',
        CASE WHEN SUM(overdue_flag_errors) = 0
             THEN 'PASS' ELSE 'FAIL' END,
        SUM(overdue_flag_errors)::text,
        '0',
        'Missing due dates are not classified as overdue by this check.'
    FROM receivables

    UNION ALL

    SELECT
        'Payables overdue flags',
        CASE WHEN SUM(overdue_flag_errors) = 0
             THEN 'PASS' ELSE 'FAIL' END,
        SUM(overdue_flag_errors)::text,
        '0',
        'Missing due dates are not classified as overdue by this check.'
    FROM payables

    UNION ALL

    -- Quality versus consolidated counts.
    SELECT
        'Quality view document counts reconcile',
        'FAIL',
        'quality invoices=' || q.invoice_record_count
        || '; consolidated invoices=' || c.invoice_record_count
        || '; quality bills=' || q.bill_record_count
        || '; consolidated bills=' || c.bill_record_count,
        'Invoice and bill counts agree',
        'Compares the quality view with the consolidated view.'
    FROM quality q
    FULL JOIN consolidated c USING (business_id, currency)
    WHERE q.invoice_record_count IS DISTINCT FROM c.invoice_record_count
       OR q.bill_record_count IS DISTINCT FROM c.bill_record_count
       OR q.business_id IS NULL
       OR c.business_id IS NULL

    UNION ALL

    -- Required values.
    SELECT
        'Consolidated required values',
        CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
        COUNT(*)::text,
        '0 rows with null required values',
        'Checks business, currency, counts, balances and missing-date exposure.'
    FROM consolidated
    WHERE business_id IS NULL
       OR currency IS NULL
       OR invoice_record_count IS NULL
       OR bill_record_count IS NULL
       OR recorded_outstanding_receivables IS NULL
       OR recorded_outstanding_payables IS NULL
       OR net_recorded_receivables_after_payables IS NULL
       OR receivables_missing_due_date_exposure IS NULL
       OR payables_missing_due_date_exposure IS NULL

    UNION ALL

    SELECT
        'Consolidated business/currency uniqueness',
        CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
        COUNT(*)::text,
        '0 duplicate business/currency keys',
        'Each business and currency combination should appear once.'
    FROM (
        SELECT business_id, currency
        FROM consolidated
        GROUP BY business_id, currency
        HAVING COUNT(*) > 1
    ) d

    UNION ALL

    -- Exceptions remain visible as WARN, not data-changing operations.
    SELECT
        'Receivables quality exceptions',
        CASE WHEN SUM(
            duplicate_count + payment_mismatch_count
            + payment_before_document_count
            + ledger_conflict_count + unmatched_count
        ) = 0 THEN 'PASS' ELSE 'WARN' END,
        'duplicates=' || SUM(duplicate_count)
        || '; payment mismatches=' || SUM(payment_mismatch_count)
        || '; payment-before-invoice=' || SUM(payment_before_document_count)
        || '; ledger conflicts=' || SUM(ledger_conflict_count)
        || '; unmatched=' || SUM(unmatched_count),
        'Review any non-zero exception counts',
        'Exceptions are surfaced, not removed or repaired.'
    FROM receivables

    UNION ALL

    SELECT
        'Payables quality exceptions',
        CASE WHEN SUM(
            duplicate_count + payment_mismatch_count
            + payment_before_document_count
            + ledger_conflict_count + unmatched_count
        ) = 0 THEN 'PASS' ELSE 'WARN' END,
        'duplicates=' || SUM(duplicate_count)
        || '; payment mismatches=' || SUM(payment_mismatch_count)
        || '; payment-before-bill=' || SUM(payment_before_document_count)
        || '; ledger conflicts=' || SUM(ledger_conflict_count)
        || '; unmatched=' || SUM(unmatched_count),
        'Review any non-zero exception counts',
        'Exceptions are surfaced, not removed or repaired.'
    FROM payables
)

SELECT
    check_name,
    status,
    observed_value,
    expected_value,
    details
FROM checks
ORDER BY
    CASE status WHEN 'FAIL' THEN 1
                WHEN 'WARN' THEN 2
                ELSE 3 END,
    check_name;