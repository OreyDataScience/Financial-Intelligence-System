SELECT
    table_name,
    ordinal_position,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'analytics'
  AND table_name IN (
      'v_consolidated_cashflow_metrics',
      'v_consolidated_revenue',
      'v_consolidated_expenses',
      'v_consolidated_liquidity',
      'v_consolidated_payment_behavior',
      'v_consolidated_working_capital',
      'v_consolidated_profitability'
  )
ORDER BY
    table_name,
    ordinal_position;