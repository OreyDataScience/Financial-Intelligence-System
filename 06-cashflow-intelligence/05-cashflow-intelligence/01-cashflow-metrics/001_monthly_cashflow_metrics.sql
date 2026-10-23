
-- ============================================================
-- Orey Analytics
-- Phase 06 — Cash Flow Intelligence
-- Monthly Cash Flow Metrics
--
-- Source:
--   analytics.v_monthly_cashflow_monitoring
--
-- Purpose:
--   Add derived monthly cash-flow indicators while retaining
--   source metrics and data-quality context.
--
-- Important:
--   Net bank movement is not closing cash balance.
--   Ratios are NULL when inflows are zero.
--   Zero recorded activity does not prove no activity occurred.
-- ============================================================

CREATE SCHEMA IF NOT EXISTS analytics;

CREATE OR REPLACE VIEW analytics.v_monthly_cashflow_metrics AS
SELECT
    business_id,
    business_name,
    industry,
    currency,
    month_start,

    -- Source monthly measures
    transaction_count,
    total_credit_inflows,
    total_debit_outflows,
    net_bank_movement,

    -- Derived ratios; undefined when inflows are zero
    CASE
        WHEN total_credit_inflows > 0
        THEN net_bank_movement / total_credit_inflows
        ELSE NULL
    END AS net_movement_margin,

    CASE
        WHEN total_credit_inflows > 0
        THEN total_debit_outflows / total_credit_inflows
        ELSE NULL
    END AS outflow_to_inflow_ratio,

    -- Explicit activity indicators
    (total_credit_inflows = 0) AS zero_inflow_flag,
    (total_debit_outflows = 0) AS zero_outflow_flag,
    (net_bank_movement < 0) AS negative_net_movement_flag,

    -- Existing month-over-month monitoring
    previous_period_month,
    previous_month_inflows,
    previous_month_outflows,
    previous_month_net_movement,
    inflow_change,
    outflow_change,
    net_movement_change,
    inflow_change_pct,
    outflow_change_pct,
    inflows_declined_flag,
    outflows_increased_flag,

    -- Preserve data-quality context
    investigation_required_count,
    reversal_count,
    sign_inconsistency_count,

    (
        COALESCE(investigation_required_count, 0) > 0
        OR COALESCE(reversal_count, 0) > 0
        OR COALESCE(sign_inconsistency_count, 0) > 0
    ) AS data_quality_attention_flag

FROM analytics.v_monthly_cashflow_monitoring;
