
-- ============================================================
-- Orey Analytics
-- Phase 06 - Cash Flow Intelligence
-- Module 08 - Financial Insights
--
-- Script 006: Financial Insight Validation
--
-- Purpose:
-- Independently validate the integrity and consistency
-- of the complete financial insight pipeline.
--
-- Validates:
-- 1. Evidence registry uniqueness.
-- 2. Rule catalogue uniqueness.
-- 3. Evaluated insight uniqueness.
-- 4. Evidence-to-rule evaluation coverage.
-- 5. Evidence referential integrity.
-- 6. Rule referential integrity.
-- 7. Prioritisation record preservation.
-- 8. Priority classification consistency.
-- 9. Attention classification consistency.
-- 10. Consolidated business-level reconciliation.
--
-- Output:
-- analytics.v_financial_insight_validation
--
-- Status:
-- PASS = validation condition satisfied.
-- FAIL = validation condition not satisfied.
--
-- ============================================================


CREATE OR REPLACE VIEW
    analytics.v_financial_insight_validation
AS

WITH

-- ------------------------------------------------------------
-- 1. Evidence registry checks
-- ------------------------------------------------------------

evidence_stats AS (
    SELECT
        COUNT(*) AS total_records,
        COUNT(DISTINCT evidence_id) AS unique_ids
    FROM analytics.v_financial_insight_evidence
),

-- ------------------------------------------------------------
-- 2. Rule catalogue checks
-- ------------------------------------------------------------

rule_stats AS (
    SELECT
        COUNT(*) AS total_records,
        COUNT(DISTINCT rule_id) AS unique_ids
    FROM analytics.v_financial_insight_rules
),

-- ------------------------------------------------------------
-- 3. Evaluated insight checks
-- ------------------------------------------------------------

insight_stats AS (
    SELECT
        COUNT(*) AS total_records,
        COUNT(DISTINCT insight_id) AS unique_ids
    FROM analytics.v_financial_insights
),

-- ------------------------------------------------------------
-- 4. Expected evaluation coverage
--
-- Every evidence record should be evaluated against
-- every rule belonging to its evidence domain.
-- ------------------------------------------------------------

expected_evaluations AS (
    SELECT
        SUM(
            evidence_counts.evidence_count
            * rule_counts.rule_count
        ) AS expected_records

    FROM (
        SELECT
            evidence_domain,
            COUNT(*) AS evidence_count
        FROM analytics.v_financial_insight_evidence
        GROUP BY evidence_domain
    ) evidence_counts

    INNER JOIN (
        SELECT
            evidence_domain,
            COUNT(*) AS rule_count
        FROM analytics.v_financial_insight_rules
        GROUP BY evidence_domain
    ) rule_counts
        ON evidence_counts.evidence_domain =
           rule_counts.evidence_domain
),

actual_evaluations AS (
    SELECT COUNT(*) AS actual_records
    FROM analytics.v_financial_insights
),

-- ------------------------------------------------------------
-- 5. Referential integrity
-- ------------------------------------------------------------

missing_evidence_references AS (
    SELECT COUNT(*) AS failure_count
    FROM analytics.v_financial_insights i
    LEFT JOIN analytics.v_financial_insight_evidence e
        ON e.evidence_id = i.evidence_id
    WHERE e.evidence_id IS NULL
),

missing_rule_references AS (
    SELECT COUNT(*) AS failure_count
    FROM analytics.v_financial_insights i
    LEFT JOIN analytics.v_financial_insight_rules r
        ON r.rule_id = i.rule_id
    WHERE r.rule_id IS NULL
),

-- ------------------------------------------------------------
-- 6. Prioritisation record preservation
-- ------------------------------------------------------------

priority_stats AS (
    SELECT
        COUNT(*) AS total_records,
        COUNT(DISTINCT insight_id) AS unique_ids
    FROM analytics.v_prioritised_financial_insights
),

missing_priority_records AS (
    SELECT COUNT(*) AS failure_count
    FROM analytics.v_financial_insights i
    LEFT JOIN analytics.v_prioritised_financial_insights p
        ON p.insight_id = i.insight_id
    WHERE p.insight_id IS NULL
),

-- ------------------------------------------------------------
-- 7. Priority classification integrity
-- ------------------------------------------------------------

priority_classification_failures AS (
    SELECT COUNT(*) AS failure_count
    FROM analytics.v_prioritised_financial_insights i
    WHERE
        i.priority_level IS DISTINCT FROM
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

            ELSE 'review'
        END

        OR

        i.priority_rank IS DISTINCT FROM
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
        END
),

-- ------------------------------------------------------------
-- 8. Attention classification integrity
-- ------------------------------------------------------------

attention_classification_failures AS (
    SELECT COUNT(*) AS failure_count
    FROM analytics.v_prioritised_financial_insights i
    WHERE
        i.attention_classification IS DISTINCT FROM
        CASE
            WHEN i.evaluation_status = 'not_triggered'
                THEN 'no_attention_required'

            WHEN i.evaluation_status = 'insufficient_evidence'
                THEN 'insufficient_evidence'

            WHEN i.insight_category IN (
                'financial_condition',
                'deterioration'
            )
                THEN 'financial_or_operational_condition'

            WHEN i.insight_category = 'reconciliation'
                THEN 'operational_investigation'

            WHEN i.insight_category = 'evidence_limitation'
                THEN 'evidence_limitation'

            ELSE 'requires_classification_review'
        END
),

-- ------------------------------------------------------------
-- 9. Business-level consolidated reconciliation
--
-- Compare the consolidated view with independently
-- aggregated prioritised insight records.
-- ------------------------------------------------------------

business_aggregates AS (
    SELECT
        business_id,
        business_name,

        COUNT(*) AS total_evaluations,

        COUNT(*) FILTER (
            WHERE evaluation_status = 'triggered'
        ) AS triggered_count,

        COUNT(*) FILTER (
            WHERE evaluation_status = 'not_triggered'
        ) AS not_triggered_count,

        COUNT(*) FILTER (
            WHERE evaluation_status = 'insufficient_evidence'
        ) AS insufficient_evidence_count,

        COUNT(DISTINCT evidence_domain) AS evidence_domains,

        COUNT(DISTINCT rule_id) AS rules_evaluated,

        COUNT(DISTINCT evidence_id) AS evidence_records

    FROM analytics.v_prioritised_financial_insights

    GROUP BY business_id, business_name
),

consolidated_comparisons AS (
    SELECT
        COUNT(*) FILTER (
            WHERE
                a.total_evaluations
                    IS DISTINCT FROM c.total_evaluations

                OR a.triggered_count
                    IS DISTINCT FROM c.triggered_insight_count

                OR a.not_triggered_count
                    IS DISTINCT FROM c.not_triggered_count

                OR a.insufficient_evidence_count
                    IS DISTINCT FROM c.insufficient_evidence_count

                OR a.evidence_domains
                    IS DISTINCT FROM c.evidence_domains_evaluated

                OR a.rules_evaluated
                    IS DISTINCT FROM c.rules_evaluated

                OR a.evidence_records
                    IS DISTINCT FROM c.source_evidence_records
        ) AS mismatched_businesses,

        COUNT(*) AS matched_businesses

    FROM business_aggregates a

    FULL OUTER JOIN
        analytics.v_consolidated_financial_insights c
        ON a.business_id = c.business_id
)

-- ============================================================
-- VALIDATION RESULTS
-- ============================================================

SELECT
    'VAL001'::text AS validation_id,
    'Evidence registry uniqueness'::text AS validation_name,
    '0 duplicate evidence IDs'::text AS expected_result,
    (
        total_records - unique_ids
    )::text AS actual_result,
    (
        total_records - unique_ids
    ) AS failure_count,
    CASE
        WHEN total_records = unique_ids THEN 'PASS'
        ELSE 'FAIL'
    END::text AS validation_status
FROM evidence_stats

UNION ALL

SELECT
    'VAL002',
    'Rule catalogue uniqueness',
    '0 duplicate rule IDs',
    (total_records - unique_ids)::text,
    (total_records - unique_ids),
    CASE
        WHEN total_records = unique_ids THEN 'PASS'
        ELSE 'FAIL'
    END
FROM rule_stats

UNION ALL

SELECT
    'VAL003',
    'Evaluated insight uniqueness',
    '0 duplicate insight IDs',
    (total_records - unique_ids)::text,
    (total_records - unique_ids),
    CASE
        WHEN total_records = unique_ids THEN 'PASS'
        ELSE 'FAIL'
    END
FROM insight_stats

UNION ALL

SELECT
    'VAL004',
    'Evidence-to-rule evaluation coverage',
    e.expected_records::text,
    a.actual_records::text,
    ABS(
        e.expected_records - a.actual_records
    ),
    CASE
        WHEN e.expected_records = a.actual_records
            THEN 'PASS'
        ELSE 'FAIL'
    END
FROM expected_evaluations e
CROSS JOIN actual_evaluations a

UNION ALL

SELECT
    'VAL005',
    'Evidence referential integrity',
    '0 missing evidence references',
    failure_count::text,
    failure_count,
    CASE
        WHEN failure_count = 0 THEN 'PASS'
        ELSE 'FAIL'
    END
FROM missing_evidence_references

UNION ALL

SELECT
    'VAL006',
    'Rule referential integrity',
    '0 missing rule references',
    failure_count::text,
    failure_count,
    CASE
        WHEN failure_count = 0 THEN 'PASS'
        ELSE 'FAIL'
    END
FROM missing_rule_references

UNION ALL

SELECT
    'VAL007',
    'Prioritisation record preservation',
    i.total_records::text,
    p.total_records::text,
    ABS(i.total_records - p.total_records),
    CASE
        WHEN i.total_records = p.total_records
         AND p.total_records = p.unique_ids
            THEN 'PASS'
        ELSE 'FAIL'
    END
FROM insight_stats i
CROSS JOIN priority_stats p

UNION ALL

SELECT
    'VAL008',
    'Prioritisation evidence record preservation',
    '0 missing prioritisation records',
    failure_count::text,
    failure_count,
    CASE
        WHEN failure_count = 0 THEN 'PASS'
        ELSE 'FAIL'
    END
FROM missing_priority_records

UNION ALL

SELECT
    'VAL009',
    'Priority classification consistency',
    '0 priority classification mismatches',
    failure_count::text,
    failure_count,
    CASE
        WHEN failure_count = 0 THEN 'PASS'
        ELSE 'FAIL'
    END
FROM priority_classification_failures

UNION ALL

SELECT
    'VAL010',
    'Attention classification consistency',
    '0 attention classification mismatches',
    failure_count::text,
    failure_count,
    CASE
        WHEN failure_count = 0 THEN 'PASS'
        ELSE 'FAIL'
    END
FROM attention_classification_failures

UNION ALL

SELECT
    'VAL011',
    'Business-level consolidated reconciliation',
    '0 mismatched businesses',
    mismatched_businesses::text,
    mismatched_businesses,
    CASE
        WHEN mismatched_businesses = 0
            AND matched_businesses = (
                SELECT COUNT(*)
                FROM analytics.v_consolidated_financial_insights
            )
            THEN 'PASS'
        ELSE 'FAIL'
    END
FROM consolidated_comparisons;


-- ============================================================
-- END OF SCRIPT 006
-- ============================================================
