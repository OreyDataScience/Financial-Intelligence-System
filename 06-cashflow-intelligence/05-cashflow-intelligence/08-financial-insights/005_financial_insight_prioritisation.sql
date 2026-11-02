
-- ============================================================
-- Orey Analytics
-- Phase 06 - Cash Flow Intelligence
-- Module 08 - Financial Insights
--
-- Script 005: Financial Insight Prioritisation
--
-- Purpose:
-- Assign transparent attention priorities to evaluated
-- financial insights using the existing rule severity,
-- insight category and evaluation outcome.
--
-- Design principles:
-- 1. Preserve every evaluated insight.
-- 2. Do not recalculate source financial indicators.
-- 3. Do not invent severity levels or risk probabilities.
-- 4. Distinguish financial/operational conditions from
--    evidence limitations and reconciliation investigations.
-- 5. Retain source evidence and evaluation explanations.
--
-- Source:
-- analytics.v_financial_insights
--
-- Output:
-- analytics.v_prioritised_financial_insights
-- ============================================================


CREATE OR REPLACE VIEW
    analytics.v_prioritised_financial_insights
AS

SELECT
    i.*,

    -- --------------------------------------------------------
    -- Priority classification
    -- --------------------------------------------------------

    CASE
        WHEN i.evaluation_status = 'not_triggered'
            THEN 'not_prioritised'

        WHEN i.evaluation_status = 'insufficient_evidence'
            THEN 'review'

        WHEN i.evaluation_status = 'triggered'
             AND i.severity = 'high_attention'
            THEN 'high'

        WHEN i.evaluation_status = 'triggered'
             AND i.severity IN (
                 'elevated_attention',
                 'management_attention'
             )
            THEN 'elevated'

        WHEN i.evaluation_status = 'triggered'
             AND i.severity IN (
                 'evidence_review',
                 'insufficient_evidence'
             )
            THEN 'review'

        ELSE 'review'
    END AS priority_level,


    -- --------------------------------------------------------
    -- Numeric priority ordering
    -- Lower number = higher attention priority
    -- --------------------------------------------------------

    CASE
        WHEN i.evaluation_status = 'not_triggered'
            THEN 4

        WHEN i.evaluation_status = 'insufficient_evidence'
            THEN 3

        WHEN i.evaluation_status = 'triggered'
             AND i.severity = 'high_attention'
            THEN 1

        WHEN i.evaluation_status = 'triggered'
             AND i.severity IN (
                 'elevated_attention',
                 'management_attention'
             )
            THEN 2

        ELSE 3
    END AS priority_rank,


    -- --------------------------------------------------------
    -- Attention classification
    -- Identifies the nature of the item requiring attention
    -- --------------------------------------------------------

    CASE
        WHEN i.evaluation_status = 'not_triggered'
            THEN 'no_attention_required'

        WHEN i.evaluation_status = 'insufficient_evidence'
            THEN 'insufficient_evidence'

        WHEN i.insight_category = 'financial_condition'
            THEN 'financial_or_operational_condition'

        WHEN i.insight_category = 'deterioration'
            THEN 'financial_or_operational_condition'

        WHEN i.insight_category = 'reconciliation'
            THEN 'operational_investigation'

        WHEN i.insight_category = 'evidence_limitation'
            THEN 'evidence_limitation'

        ELSE 'requires_classification_review'
    END AS attention_classification,


    -- --------------------------------------------------------
    -- Explanation of the assigned priority
    -- --------------------------------------------------------

    CASE
        WHEN i.evaluation_status = 'not_triggered'
            THEN
                'The rule condition was not triggered. '
                || 'No attention priority has been assigned.'

        WHEN i.evaluation_status = 'insufficient_evidence'
            THEN
                'Available evidence was insufficient to '
                || 'evaluate the rule reliably. Further '
                || 'evidence or verification may be required.'

        WHEN i.evaluation_status = 'triggered'
             AND i.severity = 'high_attention'
            THEN
                'The triggered rule carries the highest '
                || 'severity currently defined in the '
                || 'financial insight rule catalogue.'

        WHEN i.evaluation_status = 'triggered'
             AND i.severity IN (
                 'elevated_attention',
                 'management_attention'
             )
            THEN
                'The triggered rule requires elevated '
                || 'financial or operational attention '
                || 'under the existing rule severity.'

        WHEN i.evaluation_status = 'triggered'
             AND i.severity IN (
                 'evidence_review',
                 'insufficient_evidence'
             )
            THEN
                'The triggered rule identifies an evidence '
                || 'limitation or verification requirement. '
                || 'It does not independently establish '
                || 'financial deterioration.'

        ELSE
            'The evaluation requires further classification '
            || 'review before a stronger priority conclusion '
            || 'can be assigned.'
    END AS prioritisation_explanation,


    -- --------------------------------------------------------
    -- Priority generation timestamp
    -- --------------------------------------------------------

    CURRENT_TIMESTAMP AS prioritisation_generated_at

FROM analytics.v_financial_insights i;


-- ============================================================
-- END OF SCRIPT 005
-- ============================================================
