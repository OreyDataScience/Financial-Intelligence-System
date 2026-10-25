
-- ============================================================
-- Orey Analytics
-- Phase 06 — Cash Flow Intelligence
-- File: 004_cashflow_volatility_metrics.sql
--
-- Purpose:
-- Measure rolling variability in monthly net bank movements.
--
-- Notes:
-- These metrics describe bank movement variability, not
-- closing cash balances or profitability.
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_cashflow_volatility_metrics AS

SELECT
    r.business_id,
    r.business_name,
    r.currency,
    r.month_start,
    r.net_bank_movement,

    -- Three-month variability
    r.observations_3m,
    r.sd_net_movement_3m,

    CASE
        WHEN r.observations_3m >= 2
         AND r.avg_net_movement_3m IS NOT NULL
         AND r.avg_net_movement_3m <> 0
        THEN r.sd_net_movement_3m
             / ABS(r.avg_net_movement_3m)
        ELSE NULL
    END AS relative_volatility_3m,

    -- Six-month variability
    r.observations_6m,
    r.avg_net_movement_6m,

    -- The six-month standard deviation is calculated from
    -- the underlying monthly records, not inferred from
    -- the three-month standard deviation.
    CASE
        WHEN COUNT(r.net_bank_movement) OVER (
            PARTITION BY r.business_id, r.currency
            ORDER BY r.month_start
            ROWS BETWEEN 5 PRECEDING AND CURRENT ROW
        ) >= 2
        THEN STDDEV_SAMP(r.net_bank_movement) OVER (
            PARTITION BY r.business_id, r.currency
            ORDER BY r.month_start
            ROWS BETWEEN 5 PRECEDING AND CURRENT ROW
        )
        ELSE NULL
    END AS sd_net_movement_6m,

    CASE
        WHEN COUNT(r.net_bank_movement) OVER (
            PARTITION BY r.business_id, r.currency
            ORDER BY r.month_start
            ROWS BETWEEN 5 PRECEDING AND CURRENT ROW
        ) >= 2
         AND AVG(r.net_bank_movement) OVER (
            PARTITION BY r.business_id, r.currency
            ORDER BY r.month_start
            ROWS BETWEEN 5 PRECEDING AND CURRENT ROW
        ) <> 0
        THEN
            STDDEV_SAMP(r.net_bank_movement) OVER (
                PARTITION BY r.business_id, r.currency
                ORDER BY r.month_start
                ROWS BETWEEN 5 PRECEDING AND CURRENT ROW
            )
            / ABS(
                AVG(r.net_bank_movement) OVER (
                    PARTITION BY r.business_id, r.currency
                    ORDER BY r.month_start
                    ROWS BETWEEN 5 PRECEDING AND CURRENT ROW
                )
            )
        ELSE NULL
    END AS relative_volatility_6m,

    r.complete_3m_window_flag,
    r.complete_6m_window_flag

FROM analytics.v_rolling_cashflow_metrics AS r;
