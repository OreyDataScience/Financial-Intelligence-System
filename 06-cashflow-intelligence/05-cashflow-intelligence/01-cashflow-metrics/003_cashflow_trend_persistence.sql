
-- ============================================================
-- Orey Analytics
-- Phase 06 — Cash Flow Intelligence
-- Cash Flow Trend Persistence
--
-- Source:
--   analytics.v_monthly_cashflow_monitoring
--
-- Purpose:
--   Identify consecutive monthly patterns in:
--     1. Negative net bank movement
--     2. Declining inflows
--     3. Increasing outflows
--
-- Important:
--   These indicators describe observed patterns only.
--   They do not establish insolvency or closing cash balance.
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_cashflow_trend_persistence AS
WITH conditions AS (
    SELECT
        business_id,
        business_name,
        industry,
        currency,
        month_start,
        net_bank_movement,
        negative_net_movement_flag,
        inflows_declined_flag,
        outflows_increased_flag,
        previous_period_month,

        CASE
            WHEN negative_net_movement_flag THEN 1
            ELSE 0
        END AS negative_movement_indicator,

        CASE
            WHEN inflows_declined_flag THEN 1
            ELSE 0
        END AS inflow_decline_indicator,

        CASE
            WHEN outflows_increased_flag THEN 1
            ELSE 0
        END AS outflow_increase_indicator

    FROM analytics.v_monthly_cashflow_monitoring
),
streak_groups AS (
    SELECT
        *,
        SUM(
            CASE
                WHEN negative_movement_indicator = 0
                  OR previous_period_month IS DISTINCT FROM
                     (month_start - INTERVAL '1 month')::date
                THEN 1
                ELSE 0
            END
        ) OVER (
            PARTITION BY business_id, currency
            ORDER BY month_start
        ) AS negative_streak_group,

        SUM(
            CASE
                WHEN inflow_decline_indicator = 0
                  OR previous_period_month IS DISTINCT FROM
                     (month_start - INTERVAL '1 month')::date
                THEN 1
                ELSE 0
            END
        ) OVER (
            PARTITION BY business_id, currency
            ORDER BY month_start
        ) AS inflow_decline_streak_group,

        SUM(
            CASE
                WHEN outflow_increase_indicator = 0
                  OR previous_period_month IS DISTINCT FROM
                     (month_start - INTERVAL '1 month')::date
                THEN 1
                ELSE 0
            END
        ) OVER (
            PARTITION BY business_id, currency
            ORDER BY month_start
        ) AS outflow_increase_streak_group

    FROM conditions
),
streaks AS (
    SELECT
        *,
        CASE
            WHEN negative_movement_indicator = 1 THEN
                ROW_NUMBER() OVER (
                    PARTITION BY
                        business_id, currency, negative_streak_group
                    ORDER BY month_start
                )
            ELSE 0
        END AS consecutive_negative_movement_months,

        CASE
            WHEN inflow_decline_indicator = 1 THEN
                ROW_NUMBER() OVER (
                    PARTITION BY
                        business_id, currency, inflow_decline_streak_group
                    ORDER BY month_start
                )
            ELSE 0
        END AS consecutive_inflow_decline_months,

        CASE
            WHEN outflow_increase_indicator = 1 THEN
                ROW_NUMBER() OVER (
                    PARTITION BY
                        business_id, currency, outflow_increase_streak_group
                    ORDER BY month_start
                )
            ELSE 0
        END AS consecutive_outflow_increase_months

    FROM streak_groups
)
SELECT
    business_id,
    business_name,
    industry,
    currency,
    month_start,
    net_bank_movement,

    negative_movement_indicator = 1
        AS negative_net_movement_flag,
    inflow_decline_indicator = 1
        AS inflow_declined_flag,
    outflow_increase_indicator = 1
        AS outflows_increased_flag,

    consecutive_negative_movement_months,
    consecutive_inflow_decline_months,
    consecutive_outflow_increase_months,

    (
        consecutive_negative_movement_months >= 3
    ) AS persistent_negative_movement_3m_flag,

    (
        consecutive_inflow_decline_months >= 3
    ) AS persistent_inflow_decline_3m_flag,

    (
        consecutive_outflow_increase_months >= 3
    ) AS persistent_outflow_increase_3m_flag

FROM streaks;
