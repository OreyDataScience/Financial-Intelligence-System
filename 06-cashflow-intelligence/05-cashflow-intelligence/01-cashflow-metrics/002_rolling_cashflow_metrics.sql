
-- ============================================================
-- Orey Analytics
-- Phase 06 — Cash Flow Intelligence
-- Rolling Cash Flow Metrics
--
-- Source:
--   analytics.v_monthly_cashflow_metrics
--
-- Purpose:
--   Measure short-term variability and persistence in monthly
--   net bank movement.
--
-- Notes:
--   Rolling windows use observed monthly rows.
--   Standard deviation requires at least two observations.
--   These are movement metrics, not closing cash balances.
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_rolling_cashflow_metrics AS
WITH rolling AS (
    SELECT
        business_id,
        business_name,
        industry,
        currency,
        month_start,
        net_bank_movement,
        negative_net_movement_flag,

        COUNT(*) OVER (
            PARTITION BY business_id, currency
            ORDER BY month_start
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ) AS observations_3m,

        AVG(net_bank_movement) OVER (
            PARTITION BY business_id, currency
            ORDER BY month_start
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ) AS avg_net_movement_3m,

        STDDEV_SAMP(net_bank_movement) OVER (
            PARTITION BY business_id, currency
            ORDER BY month_start
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ) AS sd_net_movement_3m,

        COUNT(*) OVER (
            PARTITION BY business_id, currency
            ORDER BY month_start
            ROWS BETWEEN 5 PRECEDING AND CURRENT ROW
        ) AS observations_6m,

        AVG(net_bank_movement) OVER (
            PARTITION BY business_id, currency
            ORDER BY month_start
            ROWS BETWEEN 5 PRECEDING AND CURRENT ROW
        ) AS avg_net_movement_6m,

        SUM(
            CASE WHEN negative_net_movement_flag THEN 1 ELSE 0 END
        ) OVER (
            PARTITION BY business_id, currency
            ORDER BY month_start
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ) AS negative_movement_months_3m

    FROM analytics.v_monthly_cashflow_metrics
)
SELECT
    *,
    (
        observations_3m = 3
    ) AS complete_3m_window_flag,
    (
        observations_6m = 6
    ) AS complete_6m_window_flag
FROM rolling;
