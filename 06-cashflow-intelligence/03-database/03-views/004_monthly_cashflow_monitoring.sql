
BEGIN;

CREATE SCHEMA IF NOT EXISTS analytics;

CREATE OR REPLACE VIEW analytics.v_monthly_cashflow_monitoring AS
WITH monthly AS (
    SELECT
        business_id,
        business_name,
        industry,
        currency,
        month_start,
        transaction_count,
        total_credit_inflows,
        total_debit_outflows,
        net_bank_movement,
        investigation_required_count,
        reversal_count,
        sign_inconsistency_count
    FROM analytics.v_monthly_cash_movements
),
with_previous_month AS (
    SELECT
        m.*,

        LAG(month_start) OVER (
            PARTITION BY business_id, currency
            ORDER BY month_start
        ) AS previous_period_month,

        LAG(total_credit_inflows) OVER (
            PARTITION BY business_id, currency
            ORDER BY month_start
        ) AS previous_month_inflows,

        LAG(total_debit_outflows) OVER (
            PARTITION BY business_id, currency
            ORDER BY month_start
        ) AS previous_month_outflows,

        LAG(net_bank_movement) OVER (
            PARTITION BY business_id, currency
            ORDER BY month_start
        ) AS previous_month_net_movement

    FROM monthly AS m
)
SELECT
    business_id,
    business_name,
    industry,
    currency,
    month_start,

    transaction_count,
    total_credit_inflows,
    total_debit_outflows,
    net_bank_movement,

    previous_period_month,
    previous_month_inflows,
    previous_month_outflows,
    previous_month_net_movement,

    -- Month-over-month absolute changes
    CASE
        WHEN previous_period_month = (month_start - INTERVAL '1 month')::date
        THEN total_credit_inflows - previous_month_inflows
        ELSE NULL
    END AS inflow_change,

    CASE
        WHEN previous_period_month = (month_start - INTERVAL '1 month')::date
        THEN total_debit_outflows - previous_month_outflows
        ELSE NULL
    END AS outflow_change,

    CASE
        WHEN previous_period_month = (month_start - INTERVAL '1 month')::date
        THEN net_bank_movement - previous_month_net_movement
        ELSE NULL
    END AS net_movement_change,

    -- Percentage changes are undefined when prior value is zero
    CASE
        WHEN previous_period_month = (month_start - INTERVAL '1 month')::date
         AND previous_month_inflows <> 0
        THEN
            100.0 * (
                total_credit_inflows - previous_month_inflows
            ) / ABS(previous_month_inflows)
        ELSE NULL
    END AS inflow_change_pct,

    CASE
        WHEN previous_period_month = (month_start - INTERVAL '1 month')::date
         AND previous_month_outflows <> 0
        THEN
            100.0 * (
                total_debit_outflows - previous_month_outflows
            ) / ABS(previous_month_outflows)
        ELSE NULL
    END AS outflow_change_pct,

    -- Monitoring indicators
    CASE
        WHEN net_bank_movement < 0 THEN TRUE
        ELSE FALSE
    END AS negative_net_movement_flag,

    CASE
        WHEN previous_period_month = (month_start - INTERVAL '1 month')::date
         AND total_credit_inflows < previous_month_inflows
        THEN TRUE
        ELSE FALSE
    END AS inflows_declined_flag,

    CASE
        WHEN previous_period_month = (month_start - INTERVAL '1 month')::date
         AND total_debit_outflows > previous_month_outflows
        THEN TRUE
        ELSE FALSE
    END AS outflows_increased_flag,

    investigation_required_count,
    reversal_count,
    sign_inconsistency_count

FROM with_previous_month;

COMMENT ON VIEW analytics.v_monthly_cashflow_monitoring IS
'Monthly SME cashflow monitoring indicators based on recorded bank movements. Month-over-month comparisons require a consecutive prior calendar month. Negative net movement does not by itself establish insolvency, cash shortfall or closing cash balance.';

COMMIT;