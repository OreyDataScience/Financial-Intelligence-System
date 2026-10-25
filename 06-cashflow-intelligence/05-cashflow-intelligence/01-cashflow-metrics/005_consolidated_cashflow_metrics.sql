
-- ============================================================
-- Orey Analytics
-- Phase 06 — Cash Flow Intelligence
-- File: 005_consolidated_cashflow_metrics.sql
--
-- Purpose:
-- Consolidate monthly, rolling, persistence, and volatility
-- metrics into one downstream analytics view.
--
-- Source views:
--   analytics.v_monthly_cashflow_metrics
--   analytics.v_rolling_cashflow_metrics
--   analytics.v_cashflow_trend_persistence
--   analytics.v_cashflow_volatility_metrics
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_consolidated_cashflow_metrics AS

SELECT
    -- Business and reporting period
    m.business_id,
    m.business_name,
    m.industry,
    m.currency,
    m.month_start,

    -- Monthly activity and movement
    m.transaction_count,
    m.total_credit_inflows,
    m.total_debit_outflows,
    m.net_bank_movement,

    -- Monthly ratios and flags
    m.net_movement_margin,
    m.outflow_to_inflow_ratio,
    m.zero_inflow_flag,
    m.zero_outflow_flag,
    m.negative_net_movement_flag,

    -- Month-on-month comparisons
    m.previous_period_month,
    m.previous_month_inflows,
    m.previous_month_outflows,
    m.previous_month_net_movement,
    m.inflow_change,
    m.outflow_change,
    m.net_movement_change,
    m.inflow_change_pct,
    m.outflow_change_pct,
    m.inflows_declined_flag,
    m.outflows_increased_flag,

    -- Data-quality indicators
    m.investigation_required_count,
    m.reversal_count,
    m.sign_inconsistency_count,
    m.data_quality_attention_flag,

    -- Three-month rolling metrics
    r.observations_3m,
    r.avg_net_movement_3m,
    r.sd_net_movement_3m,
    r.negative_movement_months_3m,
    r.complete_3m_window_flag,

    -- Six-month rolling metrics
    r.observations_6m,
    r.avg_net_movement_6m,
    r.complete_6m_window_flag,

    -- Trend persistence
    t.consecutive_negative_movement_months,
    t.consecutive_inflow_decline_months,
    t.consecutive_outflow_increase_months,
    t.persistent_negative_movement_3m_flag,
    t.persistent_inflow_decline_3m_flag,
    t.persistent_outflow_increase_3m_flag,

    -- Volatility
    v.relative_volatility_3m,
    v.sd_net_movement_6m,
    v.relative_volatility_6m

FROM analytics.v_monthly_cashflow_metrics AS m

INNER JOIN analytics.v_rolling_cashflow_metrics AS r
    ON  m.business_id = r.business_id
    AND m.currency = r.currency
    AND m.month_start = r.month_start

INNER JOIN analytics.v_cashflow_trend_persistence AS t
    ON  m.business_id = t.business_id
    AND m.currency = t.currency
    AND m.month_start = t.month_start

INNER JOIN analytics.v_cashflow_volatility_metrics AS v
    ON  m.business_id = v.business_id
    AND m.currency = v.currency
    AND m.month_start = v.month_start;
