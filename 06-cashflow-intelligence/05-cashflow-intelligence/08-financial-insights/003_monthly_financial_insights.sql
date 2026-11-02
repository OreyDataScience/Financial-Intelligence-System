
-- ============================================================
-- Orey Analytics
-- Phase 06 — Cash Flow Intelligence
-- Module 08 — Financial Insights
--
-- Script 003: Financial Insight Evaluation
--
-- Purpose:
-- Evaluate the validated financial insight rules against
-- the unified financial evidence registry.
--
-- Design principles:
--   1. Preserve original evidence grains.
--   2. Preserve source evidence and traceability.
--   3. Distinguish triggered, not_triggered and
--      insufficient_evidence outcomes.
--   4. Do not replace missing evidence with zero.
--   5. Do not treat provisional evidence as verified.
--   6. Evaluate each rule independently.
--
-- Output:
--   analytics.v_financial_insights
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_financial_insights AS

WITH rule_evaluations AS (

    SELECT
        MD5(e.evidence_id || '|' || r.rule_id) AS insight_id,

        -- Rule metadata
        r.rule_id,
        r.rule_name,
        r.evidence_domain,
        r.indicator_name,
        r.rule_condition,
        r.insight_category,
        r.severity,
        r.confidence_requirement,
        r.persistence_requirement,
        r.evidence_limitation,
        r.management_attention_area,
        r.rule_description,

        -- Original evidence identifiers
        e.evidence_id,
        e.business_id,
        e.business_name,
        e.currency,
        e.source_view,
        e.evidence_grain,
        e.evidence_scope,

        -- Original observation dimensions
        e.observation_date,
        e.period_start,
        e.period_end,
        e.account_id,
        e.payment_direction,

        -- Original source metadata
        e.source_generated_at,
        e.registry_generated_at,

        -- Preserve original evidence
        e.evidence_payload,

        -- ====================================================
        -- Rule evaluation
        -- ====================================================

        CASE r.rule_id

            -- ------------------------------------------------
            -- CASHFLOW RULES
            -- ------------------------------------------------

            WHEN 'CF001' THEN
                CASE
                    WHEN e.evidence_payload ->> 'negative_net_movement_flag' IS NULL
                        THEN 'insufficient_evidence'
                    WHEN (e.evidence_payload ->> 'negative_net_movement_flag')::boolean
                        THEN 'triggered'
                    ELSE 'not_triggered'
                END

            WHEN 'CF002' THEN
                CASE
                    WHEN e.evidence_payload ->> 'persistent_negative_movement_3m_flag' IS NULL
                      OR e.evidence_payload ->> 'complete_3m_window_flag' IS NULL
                        THEN 'insufficient_evidence'
                    WHEN NOT (e.evidence_payload ->> 'complete_3m_window_flag')::boolean
                        THEN 'insufficient_evidence'
                    WHEN (e.evidence_payload ->> 'persistent_negative_movement_3m_flag')::boolean
                        THEN 'triggered'
                    ELSE 'not_triggered'
                END

            WHEN 'CF003' THEN
                CASE
                    WHEN e.evidence_payload ->> 'persistent_inflow_decline_3m_flag' IS NULL
                      OR e.evidence_payload ->> 'complete_3m_window_flag' IS NULL
                        THEN 'insufficient_evidence'
                    WHEN NOT (e.evidence_payload ->> 'complete_3m_window_flag')::boolean
                        THEN 'insufficient_evidence'
                    WHEN (e.evidence_payload ->> 'persistent_inflow_decline_3m_flag')::boolean
                        THEN 'triggered'
                    ELSE 'not_triggered'
                END

            WHEN 'CF004' THEN
                CASE
                    WHEN e.evidence_payload ->> 'persistent_outflow_increase_3m_flag' IS NULL
                      OR e.evidence_payload ->> 'complete_3m_window_flag' IS NULL
                        THEN 'insufficient_evidence'
                    WHEN NOT (e.evidence_payload ->> 'complete_3m_window_flag')::boolean
                        THEN 'insufficient_evidence'
                    WHEN (e.evidence_payload ->> 'persistent_outflow_increase_3m_flag')::boolean
                        THEN 'triggered'
                    ELSE 'not_triggered'
                END

            WHEN 'CF005' THEN
                CASE
                    WHEN e.evidence_payload ->> 'data_quality_attention_flag' IS NULL
                      OR e.evidence_payload ->> 'investigation_required_count' IS NULL
                      OR e.evidence_payload ->> 'reversal_count' IS NULL
                      OR e.evidence_payload ->> 'sign_inconsistency_count' IS NULL
                        THEN 'insufficient_evidence'
                    WHEN
                        (e.evidence_payload ->> 'data_quality_attention_flag')::boolean
                        OR (e.evidence_payload ->> 'investigation_required_count')::numeric > 0
                        OR (e.evidence_payload ->> 'reversal_count')::numeric > 0
                        OR (e.evidence_payload ->> 'sign_inconsistency_count')::numeric > 0
                        THEN 'triggered'
                    ELSE 'not_triggered'
                END

            WHEN 'CF006' THEN
                CASE
                    WHEN e.evidence_payload ->> 'complete_3m_window_flag' IS NULL
                      OR e.evidence_payload ->> 'complete_6m_window_flag' IS NULL
                        THEN 'insufficient_evidence'
                    WHEN
                        NOT (e.evidence_payload ->> 'complete_3m_window_flag')::boolean
                        OR NOT (e.evidence_payload ->> 'complete_6m_window_flag')::boolean
                        THEN 'triggered'
                    ELSE 'not_triggered'
                END

            -- ------------------------------------------------
            -- EXPENSE RULES
            -- ------------------------------------------------

            WHEN 'EXP001' THEN
                CASE
                    WHEN e.evidence_payload ->> 'supplier_concentration_band' IS NULL
                        THEN 'insufficient_evidence'
                    WHEN e.evidence_payload ->> 'supplier_concentration_band'
                         = 'Higher concentration'
                        THEN 'triggered'
                    ELSE 'not_triggered'
                END

            WHEN 'EXP002' THEN
                CASE
                    WHEN e.evidence_payload ->> 'accounting_expenses_verified' IS NULL
                      OR e.evidence_payload ->> 'bank_outflows_verified' IS NULL
                        THEN 'insufficient_evidence'
                    WHEN
                        NOT (e.evidence_payload ->> 'accounting_expenses_verified')::boolean
                        OR NOT (e.evidence_payload ->> 'bank_outflows_verified')::boolean
                        THEN 'triggered'
                    ELSE 'not_triggered'
                END

            WHEN 'EXP003' THEN
                CASE
                    WHEN e.evidence_payload ->> 'supplier_identity_incomplete' IS NULL
                        THEN 'insufficient_evidence'
                    WHEN (e.evidence_payload ->> 'supplier_identity_incomplete')::boolean
                        THEN 'triggered'
                    ELSE 'not_triggered'
                END

            WHEN 'EXP004' THEN
                CASE
                    WHEN e.evidence_payload ->> 'total_quality_flag_count' IS NULL
                        THEN 'insufficient_evidence'
                    WHEN (e.evidence_payload ->> 'total_quality_flag_count')::numeric > 0
                        THEN 'triggered'
                    ELSE 'not_triggered'
                END

            WHEN 'EXP005' THEN
                CASE
                    WHEN e.evidence_payload ->> 'month_over_month_comparison_unavailable' IS NULL
                        THEN 'insufficient_evidence'
                    WHEN (e.evidence_payload ->> 'month_over_month_comparison_unavailable')::boolean
                        THEN 'triggered'
                    ELSE 'not_triggered'
                END

            -- ------------------------------------------------
            -- LIQUIDITY RULES
            -- ------------------------------------------------

            WHEN 'LIQ001' THEN
                CASE
                    WHEN e.evidence_payload ->> 'balance_history_verified' IS NULL
                        THEN 'insufficient_evidence'
                    WHEN NOT (e.evidence_payload ->> 'balance_history_verified')::boolean
                        THEN 'triggered'
                    ELSE 'not_triggered'
                END

            WHEN 'LIQ002' THEN
                CASE
                    WHEN e.evidence_payload ->> 'ledger_conflict_count' IS NULL
                        THEN 'insufficient_evidence'
                    WHEN (e.evidence_payload ->> 'ledger_conflict_count')::numeric > 0
                        THEN 'triggered'
                    ELSE 'not_triggered'
                END

            WHEN 'LIQ003' THEN
                CASE
                    WHEN e.evidence_payload ->> 'latest_recorded_balance' IS NULL
                        THEN 'insufficient_evidence'
                    WHEN (e.evidence_payload ->> 'latest_recorded_balance')::numeric < 0
                        THEN 'triggered'
                    ELSE 'not_triggered'
                END

            WHEN 'LIQ004' THEN
                CASE
                    WHEN e.evidence_payload ->> 'outstanding_invoices_missing_due_date_count' IS NULL
                        THEN 'insufficient_evidence'
                    WHEN (e.evidence_payload ->> 'outstanding_invoices_missing_due_date_count')::numeric > 0
                        THEN 'triggered'
                    ELSE 'not_triggered'
                END

            WHEN 'LIQ005' THEN
                CASE
                    WHEN e.evidence_payload ->> 'unresolved_transaction_count' IS NULL
                        THEN 'insufficient_evidence'
                    WHEN (e.evidence_payload ->> 'unresolved_transaction_count')::numeric > 0
                        THEN 'triggered'
                    ELSE 'not_triggered'
                END

            -- ------------------------------------------------
            -- PAYMENT BEHAVIOUR RULES
            -- ------------------------------------------------

            WHEN 'PAY001' THEN
                CASE
                    WHEN e.evidence_payload ->> 'recorded_late_payment_count' IS NULL
                        THEN 'insufficient_evidence'
                    WHEN (e.evidence_payload ->> 'recorded_late_payment_count')::numeric > 0
                        THEN 'triggered'
                    ELSE 'not_triggered'
                END

            WHEN 'PAY002' THEN
                CASE
                    WHEN e.evidence_payload ->> 'metrics_pattern_record_count_difference' IS NULL
                      OR e.evidence_payload ->> 'metrics_pattern_document_amount_difference' IS NULL
                      OR e.evidence_payload ->> 'metrics_pattern_paid_amount_difference' IS NULL
                        THEN 'insufficient_evidence'
                    WHEN
                        (e.evidence_payload ->> 'metrics_pattern_record_count_difference')::numeric <> 0
                        OR (e.evidence_payload ->> 'metrics_pattern_document_amount_difference')::numeric <> 0
                        OR (e.evidence_payload ->> 'metrics_pattern_paid_amount_difference')::numeric <> 0
                        THEN 'triggered'
                    ELSE 'not_triggered'
                END

            WHEN 'PAY003' THEN
                CASE
                    WHEN e.evidence_payload ->> 'unmatched_investigation_count' IS NULL
                        THEN 'insufficient_evidence'
                    WHEN (e.evidence_payload ->> 'unmatched_investigation_count')::numeric > 0
                        THEN 'triggered'
                    ELSE 'not_triggered'
                END

            WHEN 'PAY004' THEN
                CASE
                    WHEN e.evidence_payload ->> 'payments_with_missing_due_date_count' IS NULL
                        THEN 'insufficient_evidence'
                    WHEN (e.evidence_payload ->> 'payments_with_missing_due_date_count')::numeric > 0
                        THEN 'triggered'
                    ELSE 'not_triggered'
                END

            -- ------------------------------------------------
            -- PROFITABILITY RULES
            -- ------------------------------------------------

            WHEN 'PROF001' THEN
                CASE
                    WHEN e.evidence_payload ->> 'consolidated_profitability_evidence_status' IS NULL
                        THEN 'insufficient_evidence'
                    WHEN e.evidence_payload ->> 'consolidated_profitability_evidence_status'
                         = 'provisional_comparison_accounting_expenses_unverified'
                        THEN 'triggered'
                    ELSE 'not_triggered'
                END

            WHEN 'PROF002' THEN
                CASE
                    WHEN e.evidence_payload ->> 'months_with_incomplete_source_coverage' IS NULL
                        THEN 'insufficient_evidence'
                    WHEN (e.evidence_payload ->> 'months_with_incomplete_source_coverage')::numeric > 0
                        THEN 'triggered'
                    ELSE 'not_triggered'
                END

            -- ------------------------------------------------
            -- REVENUE RULES
            -- ------------------------------------------------

            WHEN 'REV001' THEN
                CASE
                    WHEN e.evidence_payload ->> 'invoicing_declined_for_3_month_window' IS NULL
                      OR e.evidence_payload ->> 'has_3_month_row_window' IS NULL
                        THEN 'insufficient_evidence'
                    WHEN NOT (e.evidence_payload ->> 'has_3_month_row_window')::boolean
                        THEN 'insufficient_evidence'
                    WHEN (e.evidence_payload ->> 'invoicing_declined_for_3_month_window')::boolean
                        THEN 'triggered'
                    ELSE 'not_triggered'
                END

            WHEN 'REV002' THEN
                CASE
                    WHEN e.evidence_payload ->> 'overdue_invoice_count' IS NULL
                        THEN 'insufficient_evidence'
                    WHEN (e.evidence_payload ->> 'overdue_invoice_count')::numeric > 0
                        THEN 'triggered'
                    ELSE 'not_triggered'
                END

            WHEN 'REV003' THEN
                CASE
                    WHEN e.evidence_payload ->> 'revenue_quality_status' IS NULL
                        THEN 'insufficient_evidence'
                    WHEN e.evidence_payload ->> 'revenue_quality_status'
                         = 'revenue_data_quality_review_required'
                        THEN 'triggered'
                    ELSE 'not_triggered'
                END

            WHEN 'REV004' THEN
                CASE
                    WHEN e.evidence_payload ->> 'missing_customer_identity_count' IS NULL
                        THEN 'insufficient_evidence'
                    WHEN (e.evidence_payload ->> 'missing_customer_identity_count')::numeric > 0
                        THEN 'triggered'
                    ELSE 'not_triggered'
                END

            WHEN 'REV005' THEN
                CASE
                    WHEN e.evidence_payload ->> 'trend_comparison_status' IS NULL
                        THEN 'insufficient_evidence'
                    WHEN e.evidence_payload ->> 'trend_comparison_status'
                         IN ('gap_in_monthly_observations', 'no_previous_observation')
                        THEN 'triggered'
                    ELSE 'not_triggered'
                END

            -- ------------------------------------------------
            -- WORKING CAPITAL RULES
            -- ------------------------------------------------

            WHEN 'WC001' THEN
                CASE
                    WHEN e.evidence_payload ->> 'recorded_overdue_receivables' IS NULL
                        THEN 'insufficient_evidence'
                    WHEN (e.evidence_payload ->> 'recorded_overdue_receivables')::numeric > 0
                        THEN 'triggered'
                    ELSE 'not_triggered'
                END

            WHEN 'WC002' THEN
                CASE
                    WHEN e.evidence_payload ->> 'recorded_overdue_payables' IS NULL
                        THEN 'insufficient_evidence'
                    WHEN (e.evidence_payload ->> 'recorded_overdue_payables')::numeric > 0
                        THEN 'triggered'
                    ELSE 'not_triggered'
                END

            WHEN 'WC003' THEN
                CASE
                    WHEN e.evidence_payload ->> 'open_invoice_missing_due_date_count' IS NULL
                        THEN 'insufficient_evidence'
                    WHEN (e.evidence_payload ->> 'open_invoice_missing_due_date_count')::numeric > 0
                        THEN 'triggered'
                    ELSE 'not_triggered'
                END

            WHEN 'WC004' THEN
                CASE
                    WHEN e.evidence_payload ->> 'open_bill_missing_due_date_count' IS NULL
                        THEN 'insufficient_evidence'
                    WHEN (e.evidence_payload ->> 'open_bill_missing_due_date_count')::numeric > 0
                        THEN 'triggered'
                    ELSE 'not_triggered'
                END

            ELSE 'insufficient_evidence'

        END AS evaluation_status

    FROM analytics.v_financial_insight_evidence e

    INNER JOIN analytics.v_financial_insight_rules r
        ON e.evidence_domain = r.evidence_domain
)

SELECT
    insight_id,

    rule_id,
    rule_name,
    evidence_domain,
    indicator_name,
    rule_condition,
    insight_category,
    severity,
    confidence_requirement,
    persistence_requirement,
    evidence_limitation,
    management_attention_area,
    rule_description,

    evidence_id,
    business_id,
    business_name,
    currency,
    source_view,
    evidence_grain,
    evidence_scope,

    observation_date,
    period_start,
    period_end,
    account_id,
    payment_direction,

    evaluation_status,

    (evaluation_status = 'triggered') AS is_triggered,

    CASE
        WHEN evaluation_status = 'triggered'
            THEN 'The rule condition was satisfied by the available source evidence.'

        WHEN evaluation_status = 'not_triggered'
            THEN 'The rule condition was not satisfied by the available source evidence.'

        WHEN evaluation_status = 'insufficient_evidence'
            THEN 'The required evidence or comparison window is unavailable for reliable evaluation.'

    END AS evaluation_explanation,

    source_generated_at,
    registry_generated_at,
    evidence_payload

FROM rule_evaluations;
