
-- ============================================================
-- Orey Analytics
-- Phase 06 — Cash Flow Intelligence
-- Module 08 — Financial Insights
--
-- Script 004:
-- Consolidated Financial Insights
--
-- Purpose:
-- Consolidate evaluated financial insights into a business-level
-- reporting view while preserving the original evidence grain.
--
-- Design principles:
--   1. Preserve individual insight records.
--   2. Do not combine different evidence grains.
--   3. Separate financial deterioration from evidence limitations
--      and operational investigation.
--   4. Preserve source evidence and evaluation explanations.
--   5. Avoid creating an uncalibrated business risk score.
--   6. Retain triggered, non-triggered and insufficient results.
--
-- Source:
--   analytics.v_financial_insights
--
-- Output:
--   analytics.v_consolidated_financial_insights
-- ============================================================


CREATE OR REPLACE VIEW analytics.v_consolidated_financial_insights AS

WITH classified_insights AS (

    SELECT
        i.*,

        CASE
            WHEN i.evaluation_status = 'insufficient_evidence'
                THEN 'insufficient_evidence'

            WHEN i.evaluation_status = 'not_triggered'
                THEN 'no_attention_required'

            WHEN i.evaluation_status = 'triggered'
                 AND i.evidence_domain IN (
                     'cashflow',
                     'revenue',
                     'expenses',
                     'liquidity',
                     'payment_behavior',
                     'working_capital'
                 )
                 AND i.rule_id NOT IN (
                     'CF005',
                     'CF006',
                     'EXP002',
                     'EXP003',
                     'EXP004',
                     'EXP005',
                     'LIQ001',
                     'LIQ002',
                     'LIQ004',
                     'LIQ005',
                     'PAY002',
                     'PAY003',
                     'PAY004',
                     'REV003',
                     'REV004',
                     'REV005',
                     'WC003',
                     'WC004'
                 )
                THEN 'financial_or_operational_condition'

            WHEN i.evaluation_status = 'triggered'
                 AND i.rule_id IN (
                     'CF005',
                     'LIQ002',
                     'LIQ005',
                     'PAY002',
                     'PAY003',
                     'EXP003',
                     'EXP004',
                     'REV003'
                 )
                THEN 'operational_investigation'

            WHEN i.evaluation_status = 'triggered'
                 AND i.rule_id IN (
                     'CF006',
                     'EXP002',
                     'EXP005',
                     'LIQ001',
                     'LIQ004',
                     'PAY004',
                     'PROF001',
                     'PROF002',
                     'REV004',
                     'REV005',
                     'WC003',
                     'WC004'
                 )
                THEN 'evidence_limitation'

            ELSE 'requires_classification_review'
        END AS insight_interpretation

    FROM analytics.v_financial_insights i
),

business_summary AS (

    SELECT
        business_id,
        business_name,
        currency,

        COUNT(*) AS total_evaluations,

        COUNT(*) FILTER (
            WHERE evaluation_status = 'triggered'
        ) AS triggered_insight_count,

        COUNT(*) FILTER (
            WHERE evaluation_status = 'not_triggered'
        ) AS not_triggered_count,

        COUNT(*) FILTER (
            WHERE evaluation_status = 'insufficient_evidence'
        ) AS insufficient_evidence_count,

        COUNT(*) FILTER (
            WHERE evaluation_status = 'triggered'
              AND insight_interpretation =
                  'financial_or_operational_condition'
        ) AS financial_or_operational_condition_count,

        COUNT(*) FILTER (
            WHERE evaluation_status = 'triggered'
              AND insight_interpretation =
                  'operational_investigation'
        ) AS operational_investigation_count,

        COUNT(*) FILTER (
            WHERE evaluation_status = 'triggered'
              AND insight_interpretation =
                  'evidence_limitation'
        ) AS evidence_limitation_count,

        COUNT(*) FILTER (
            WHERE evaluation_status = 'triggered'
              AND insight_interpretation =
                  'requires_classification_review'
        ) AS classification_review_count,

        COUNT(DISTINCT evidence_domain) AS evidence_domains_evaluated,

        COUNT(DISTINCT rule_id) AS rules_evaluated,

        COUNT(DISTINCT evidence_id) AS source_evidence_records,

        COUNT(DISTINCT observation_date) AS distinct_observation_dates,

        MIN(observation_date) AS earliest_observation_date,

        MAX(observation_date) AS latest_observation_date,

        MAX(registry_generated_at) AS latest_registry_generated_at

    FROM classified_insights

    GROUP BY
        business_id,
        business_name,
        currency
)

SELECT
    s.business_id,
    s.business_name,
    s.currency,

    s.total_evaluations,
    s.triggered_insight_count,
    s.not_triggered_count,
    s.insufficient_evidence_count,

    s.financial_or_operational_condition_count,
    s.operational_investigation_count,
    s.evidence_limitation_count,
    s.classification_review_count,

    s.evidence_domains_evaluated,
    s.rules_evaluated,
    s.source_evidence_records,

    s.distinct_observation_dates,
    s.earliest_observation_date,
    s.latest_observation_date,

    s.latest_registry_generated_at,

    CURRENT_TIMESTAMP AS view_generated_at

FROM business_summary s;


-- ============================================================
-- End of Script 004
-- ============================================================
