
-- ============================================================
-- Orey Analytics
-- Phase 06 — Cash Flow Intelligence
-- Module 08 — Financial Insights
--
-- Script 001: Financial Insight Evidence
--
-- Purpose:
-- Establish a unified, traceable evidence registry from
-- the seven validated consolidated analytics sources.
--
-- Design principles:
--   1. Preserve original source records.
--   2. Preserve original evidence grain.
--   3. Do not recalculate financial metrics.
--   4. Do not convert snapshots into monthly observations.
--   5. Preserve provisional and unverified evidence.
--   6. Distinguish source observation dates from
--      source-generation timestamps.
--   7. Retain missing values rather than replacing them.
--
-- Output:
--   analytics.v_financial_insight_evidence
-- ============================================================


CREATE OR REPLACE VIEW
    analytics.v_financial_insight_evidence
AS

WITH source_evidence AS (

    -- --------------------------------------------------------
    -- 1. CASH FLOW: BUSINESS / CURRENCY / MONTH
    -- --------------------------------------------------------

    SELECT
        'cashflow'::text AS evidence_domain,
        'analytics.v_consolidated_cashflow_metrics'::text
            AS source_view,

        'business_month'::text AS evidence_grain,

        c.business_id,
        c.business_name,
        c.currency,

        c.month_start AS observation_date,
        c.month_start AS period_start,
        (
            c.month_start + INTERVAL '1 month'
            - INTERVAL '1 day'
        )::date AS period_end,

        NULL::text AS account_id,
        NULL::text AS payment_direction,

        NULL::timestamptz AS source_generated_at,

        'monthly_financial_observation'::text
            AS evidence_scope,

        to_jsonb(c) AS evidence_payload

    FROM analytics.v_consolidated_cashflow_metrics c


    UNION ALL


    -- --------------------------------------------------------
    -- 2. REVENUE: BUSINESS / CURRENCY / MONTH
    -- --------------------------------------------------------

    SELECT
        'revenue',
        'analytics.v_consolidated_revenue',

        'business_month',

        r.business_id,
        r.business_name,
        r.currency,

        r.month_start,
        r.month_start,
        (
            r.month_start + INTERVAL '1 month'
            - INTERVAL '1 day'
        )::date,

        NULL::text,
        NULL::text,

        r.view_generated_at,

        'monthly_revenue_and_collection_observation',

        to_jsonb(r)

    FROM analytics.v_consolidated_revenue r


    UNION ALL


    -- --------------------------------------------------------
    -- 3. EXPENSES: BUSINESS / CURRENCY / MONTH
    --
    -- Important:
    -- The payload also contains business/currency-level
    -- quality measures. These must not be interpreted as
    -- monthly counts by downstream insight rules.
    -- --------------------------------------------------------

    SELECT
        'expenses',
        'analytics.v_consolidated_expenses',

        'business_month_with_business_level_quality_fields',

        e.business_id,
        e.business_name,
        e.currency,

        e.month_start,
        e.month_start,
        (
            e.month_start + INTERVAL '1 month'
            - INTERVAL '1 day'
        )::date,

        NULL::text,
        NULL::text,

        e.view_generated_at,

        'monthly_expense_observation_with_business_currency_quality_scope',

        to_jsonb(e)

    FROM analytics.v_consolidated_expenses e


    UNION ALL


    -- --------------------------------------------------------
    -- 4. LIQUIDITY: BUSINESS / CURRENCY / BANK / ACCOUNT
    -- --------------------------------------------------------

    SELECT
        'liquidity',
        'analytics.v_consolidated_liquidity',

        'bank_account_snapshot',

        l.business_id,
        l.business_name,
        l.currency,

        GREATEST(
            l.latest_balance_transaction_date,
            l.latest_balance_posting_date
        ),

        NULL::date,
        NULL::date,

        l.account_id,
        NULL::text,

        l.view_generated_at,

        'account_level_liquidity_snapshot',

        to_jsonb(l)

    FROM analytics.v_consolidated_liquidity l


    UNION ALL


    -- --------------------------------------------------------
    -- 5. PAYMENT BEHAVIOUR:
    -- BUSINESS / CURRENCY / PAYMENT DIRECTION
    -- --------------------------------------------------------

    SELECT
        'payment_behavior',
        'analytics.v_consolidated_payment_behavior',

        'business_payment_direction',

        p.business_id,
        NULL::text,
        p.currency,

        NULL::date,
        NULL::date,
        NULL::date,

        NULL::text,
        p.payment_direction,

        p.view_generated_at,

        'business_level_payment_behavior_summary',

        to_jsonb(p)

    FROM analytics.v_consolidated_payment_behavior p


    UNION ALL


    -- --------------------------------------------------------
    -- 6. WORKING CAPITAL:
    -- BUSINESS / CURRENCY / AGEING SNAPSHOT
    -- --------------------------------------------------------

    SELECT
        'working_capital',
        'analytics.v_consolidated_working_capital',

        'business_working_capital_snapshot',

        w.business_id,
        w.business_name,
        w.currency,

        w.aging_as_of_date,
        NULL::date,
        NULL::date,

        NULL::text,
        NULL::text,

        w.view_generated_at,

        'invoice_and_supplier_bill_snapshot_not_verified_cash',

        to_jsonb(w)

    FROM analytics.v_consolidated_working_capital w


    UNION ALL


    -- --------------------------------------------------------
    -- 7. PROFITABILITY:
    -- BUSINESS / CURRENCY / HISTORICAL SUMMARY
    -- --------------------------------------------------------

    SELECT
        'profitability',
        'analytics.v_consolidated_profitability',

        'business_historical_summary',

        f.business_id,
        f.business_name,
        f.currency,

        f.last_observed_month,
        f.first_observed_month,
        f.last_observed_month,

        NULL::text,
        NULL::text,

        f.view_generated_at,

        'provisional_invoice_to_bill_comparison_not_profit',

        to_jsonb(f)

    FROM analytics.v_consolidated_profitability f

)

SELECT
    md5(
        jsonb_build_array(
            source_view,
            business_id,
            currency,
            evidence_grain,
            observation_date,
            period_start,
            period_end,
            account_id,
            payment_direction
        )::text
    ) AS evidence_id,

    business_id,
    business_name,
    currency,

    evidence_domain,
    source_view,
    evidence_grain,

    observation_date,
    period_start,
    period_end,

    account_id,
    payment_direction,

    evidence_scope,

    source_generated_at,

    evidence_payload,

    CURRENT_TIMESTAMP AS registry_generated_at

FROM source_evidence;
