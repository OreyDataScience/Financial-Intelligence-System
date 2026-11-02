
-- ============================================================
-- Orey Analytics
-- Phase 06 — Cash Flow Intelligence
-- Module 08 — Financial Insights
--
-- Script 002: Financial Insight Rules
--
-- Purpose:
-- Establish a central, explainable financial insight
-- rule catalogue for the seven evidence domains.
--
-- Design principles:
--   1. Use existing source indicators where available.
--   2. Avoid arbitrary financial thresholds.
--   3. Separate severity from evidence confidence.
--   4. Separate isolated conditions from persistence.
--   5. Preserve provisional and unverified evidence.
--   6. Distinguish financial conditions from data quality.
--   7. Do not interpret receivables as available cash.
--   8. Do not interpret invoice-to-bill differences as profit.
--
-- Output:
--   analytics.v_financial_insight_rules
--
-- This script defines rule metadata only.
-- It does not yet evaluate individual business records.
-- ============================================================


CREATE OR REPLACE VIEW
    analytics.v_financial_insight_rules
AS

SELECT *
FROM (
    VALUES

    -- ========================================================
    -- CASH FLOW INTELLIGENCE
    -- ========================================================

    (
        'CF001',
        'Negative Monthly Net Movement',
        'cashflow',
        'negative_net_movement_flag',
        'negative_net_movement_flag = true',
        'financial_condition',
        'elevated_attention',
        'monthly_source_observation',
        'single_month; assess persistence separately',
        'Bank movement is not equivalent to verified accounting profit or loss.',
        'Cash flow monitoring',
        'Identify months in which recorded bank outflows exceed recorded inflows.'
    ),

    (
        'CF002',
        'Persistent Negative Net Movement',
        'cashflow',
        'persistent_negative_movement_3m_flag',
        'persistent_negative_movement_3m_flag = true AND complete_3m_window_flag = true',
        'deterioration',
        'high_attention',
        'complete_three_month_window',
        'persistent_three_month_condition',
        'Based on recorded bank movements; does not establish future cash exhaustion.',
        'Cash flow deterioration',
        'Identify persistent negative bank movement across a complete three-month window.'
    ),

    (
        'CF003',
        'Persistent Inflow Decline',
        'cashflow',
        'persistent_inflow_decline_3m_flag',
        'persistent_inflow_decline_3m_flag = true AND complete_3m_window_flag = true',
        'deterioration',
        'elevated_attention',
        'complete_three_month_window',
        'persistent_three_month_condition',
        'Declining recorded inflows do not necessarily establish declining accounting revenue.',
        'Revenue and cash inflow monitoring',
        'Identify sustained declines in recorded bank inflows.'
    ),

    (
        'CF004',
        'Persistent Outflow Increase',
        'cashflow',
        'persistent_outflow_increase_3m_flag',
        'persistent_outflow_increase_3m_flag = true AND complete_3m_window_flag = true',
        'deterioration',
        'elevated_attention',
        'complete_three_month_window',
        'persistent_three_month_condition',
        'Increasing bank outflows do not independently establish increasing accounting expenses.',
        'Cash expenditure monitoring',
        'Identify sustained increases in recorded bank outflows.'
    ),

    (
        'CF005',
        'Cash Flow Data Quality Investigation',
        'cashflow',
        'data_quality_attention_flag',
        'data_quality_attention_flag = true OR investigation_required_count > 0 OR reversal_count > 0 OR sign_inconsistency_count > 0',
        'evidence_limitation',
        'evidence_review',
        'source_quality_indicators_available',
        'assess each observation independently',
        'Underlying transaction and reconciliation evidence may require investigation.',
        'Financial data integrity',
        'Identify cash flow observations requiring transaction or reconciliation review.'
    ),

    (
        'CF006',
        'Incomplete Cash Flow Rolling Window',
        'cashflow',
        'complete_3m_window_flag',
        'complete_3m_window_flag = false OR complete_6m_window_flag = false',
        'evidence_limitation',
        'insufficient_evidence',
        'rolling_window_completeness',
        'reassess when additional observations become available',
        'Incomplete rolling windows must not be interpreted as complete historical trends.',
        'Historical evidence coverage',
        'Identify incomplete three-month or six-month rolling observation windows.'
    ),


    -- ========================================================
    -- REVENUE INTELLIGENCE
    -- ========================================================

    (
        'REV001',
        'Persistent Invoice Activity Decline',
        'revenue',
        'invoicing_declined_for_3_month_window',
        'invoicing_declined_for_3_month_window = true AND has_3_month_row_window = true',
        'deterioration',
        'elevated_attention',
        'three_month_row_window_required',
        'persistent_three_month_observation',
        'Invoice activity is not necessarily equivalent to collected cash or recognised revenue.',
        'Revenue performance',
        'Identify sustained declines in recorded invoice activity.'
    ),

    (
        'REV002',
        'Overdue Customer Invoices',
        'revenue',
        'overdue_invoice_count',
        'overdue_invoice_count > 0',
        'financial_condition',
        'management_attention',
        'overdue_invoice_evidence_available',
        'assess the latest monthly observation',
        'Overdue invoices represent recorded collection exposure, not guaranteed collectible cash.',
        'Receivables and collections',
        'Identify monthly observations containing overdue customer invoices.'
    ),

    (
        'REV003',
        'Revenue Data Quality Review',
        'revenue',
        'revenue_quality_status',
        'revenue_quality_status = revenue_data_quality_review_required',
        'evidence_limitation',
        'evidence_review',
        'revenue_quality_classification_available',
        'reassess as source quality changes',
        'Monthly quality counts exclude records without standardized invoice dates.',
        'Revenue data integrity',
        'Identify revenue observations requiring source-data quality review.'
    ),

    (
        'REV004',
        'Incomplete Customer Identity',
        'revenue',
        'missing_customer_identity_count',
        'missing_customer_identity_count > 0',
        'evidence_limitation',
        'evidence_review',
        'customer_identity_quality_available',
        'assess each monthly observation',
        'Unidentified customers limit customer concentration and counterparty analysis.',
        'Customer identity and concentration',
        'Identify revenue observations containing invoices without customer identity.'
    ),

    (
        'REV005',
        'Revenue Trend Comparison Unavailable',
        'revenue',
        'trend_comparison_status',
        'trend_comparison_status IN (gap_in_monthly_observations, no_previous_observation)',
        'evidence_limitation',
        'insufficient_evidence',
        'historical_comparison_required',
        'reassess when comparable observations become available',
        'A missing comparison must not be interpreted as revenue deterioration.',
        'Revenue trend reliability',
        'Identify observations where historical monthly comparison is unavailable.'
    ),


    -- ========================================================
    -- EXPENSE INTELLIGENCE
    -- ========================================================

    (
        'EXP001',
        'High Supplier Concentration',
        'expenses',
        'supplier_concentration_band',
        'supplier_concentration_band = Higher concentration',
        'financial_condition',
        'management_attention',
        'supplier_concentration_measure_available',
        'assess monthly observations',
        'Supplier concentration does not independently establish financial distress.',
        'Supplier dependency',
        'Identify expense observations classified as having higher supplier concentration.'
    ),

    (
        'EXP002',
        'Expense Evidence Not Verified',
        'expenses',
        'accounting_expenses_verified',
        'accounting_expenses_verified = false OR bank_outflows_verified = false',
        'evidence_limitation',
        'evidence_review',
        'accounting_and_bank_evidence_verification',
        'reassess when independent verification becomes available',
        'Supplier bill records must not be represented as verified accounting expenses or bank outflows.',
        'Expense evidence reliability',
        'Identify expense records whose accounting expense or bank outflow evidence is unverified.'
    ),

    (
        'EXP003',
        'Supplier Identity Incomplete',
        'expenses',
        'supplier_identity_incomplete',
        'supplier_identity_incomplete = true',
        'evidence_limitation',
        'evidence_review',
        'supplier_identity_quality_available',
        'assess monthly observations',
        'Incomplete supplier identity can distort supplier concentration and dependency analysis.',
        'Supplier identity and reconciliation',
        'Identify expense observations with incomplete supplier identity.'
    ),

    (
        'EXP004',
        'Expense Data Quality Review',
        'expenses',
        'total_quality_flag_count',
        'total_quality_flag_count > 0',
        'evidence_limitation',
        'evidence_review',
        'monthly_quality_indicators_available',
        'assess monthly observations',
        'Business/currency-level quality totals must not be mistaken for monthly counts.',
        'Expense data integrity',
        'Identify monthly expense observations containing recorded quality flags.'
    ),

    (
        'EXP005',
        'Expense Trend Comparison Unavailable',
        'expenses',
        'month_over_month_comparison_unavailable',
        'month_over_month_comparison_unavailable = true',
        'evidence_limitation',
        'insufficient_evidence',
        'previous_calendar_month_required',
        'reassess when comparable monthly observations become available',
        'Rolling observed-month windows may not represent consecutive calendar months.',
        'Expense trend reliability',
        'Identify expense observations where calendar-month comparison is unavailable.'
    ),


    -- ========================================================
    -- LIQUIDITY INTELLIGENCE
    -- ========================================================

    (
        'LIQ001',
        'Cash Balance Not Independently Verified',
        'liquidity',
        'balance_history_verified',
        'balance_history_verified = false',
        'evidence_limitation',
        'evidence_review',
        'balance_verification_status_available',
        'reassess when balance verification improves',
        'Recorded account balances must not automatically be presented as verified available cash.',
        'Cash position verification',
        'Identify bank accounts whose recorded balance history is not verified.'
    ),

    (
        'LIQ002',
        'Bank Ledger Reconciliation Conflicts',
        'liquidity',
        'ledger_conflict_count',
        'ledger_conflict_count > 0',
        'reconciliation',
        'elevated_attention',
        'ledger_conflict_evidence_available',
        'assess account-level observations',
        'A reconciliation conflict requires investigation before relying on affected balances.',
        'Bank reconciliation',
        'Identify bank accounts with recorded ledger conflicts.'
    ),

    (
        'LIQ003',
        'Negative Recorded Bank Balance',
        'liquidity',
        'latest_recorded_balance',
        'latest_recorded_balance < 0',
        'financial_condition',
        'elevated_attention',
        'recorded_balance_available',
        'assess latest account observation',
        'The recorded balance is unverified and must not be represented as a confirmed overdraft or verified cash position.',
        'Recorded bank balance review',
        'Identify accounts with negative recorded balances requiring verification.'
    ),

    (
        'LIQ004',
        'Receivables Due Date Evidence Incomplete',
        'liquidity',
        'outstanding_invoices_missing_due_date_count',
        'outstanding_invoices_missing_due_date_count > 0',
        'evidence_limitation',
        'evidence_review',
        'outstanding_invoice_due_date_quality_available',
        'assess account-level snapshot',
        'Missing due dates prevent reliable overdue classification for affected invoices.',
        'Receivables timing evidence',
        'Identify outstanding receivables containing invoices without due dates.'
    ),

    (
        'LIQ005',
        'Unresolved Bank Transaction Evidence',
        'liquidity',
        'unresolved_transaction_count',
        'unresolved_transaction_count > 0',
        'reconciliation',
        'elevated_attention',
        'transaction_reconciliation_evidence_available',
        'assess account-level snapshot',
        'Unresolved transactions can affect confidence in recorded account balances.',
        'Bank transaction reconciliation',
        'Identify accounts with unresolved transaction evidence.'
    ),


    -- ========================================================
    -- PAYMENT BEHAVIOUR INTELLIGENCE
    -- ========================================================

    (
        'PAY001',
        'Recorded Late Payment Behaviour',
        'payment_behavior',
        'recorded_late_payment_count',
        'recorded_late_payment_count > 0',
        'financial_condition',
        'management_attention',
        'recorded_payment_timing_evidence_available',
        'assess separately by payment direction',
        'Payment timing is based on recorded invoice and supplier-bill fields, not independently verified cash.',
        'Customer and supplier payment behaviour',
        'Identify customer or supplier payment-direction summaries containing recorded late payments.'
    ),

    (
        'PAY002',
        'Payment Reconciliation Differences',
        'payment_behavior',
        'metrics_pattern_record_count_difference',
        'metrics_pattern_record_count_difference <> 0 OR metrics_pattern_document_amount_difference <> 0 OR metrics_pattern_paid_amount_difference <> 0',
        'reconciliation',
        'evidence_review',
        'metrics_and_counterparty_pattern_comparison_available',
        'assess business and payment direction separately',
        'Differences between payment metrics and counterparty patterns require reconciliation.',
        'Payment evidence integrity',
        'Identify inconsistencies between payment metrics and counterparty pattern aggregates.'
    ),

    (
        'PAY003',
        'Unmatched Payment Investigation',
        'payment_behavior',
        'unmatched_investigation_count',
        'unmatched_investigation_count > 0',
        'reconciliation',
        'evidence_review',
        'payment_matching_quality_available',
        'assess business and payment direction separately',
        'Unmatched payment records require investigation before relying on payment behaviour conclusions.',
        'Payment reconciliation',
        'Identify payment summaries containing unmatched investigation records.'
    ),

    (
        'PAY004',
        'Payment Due Date Evidence Incomplete',
        'payment_behavior',
        'payments_with_missing_due_date_count',
        'payments_with_missing_due_date_count > 0',
        'evidence_limitation',
        'insufficient_evidence',
        'payment_due_date_quality_available',
        'assess business and payment direction separately',
        'Missing due dates limit reliable early, on-time and late payment classification.',
        'Payment timing reliability',
        'Identify payment summaries containing documents without due dates.'
    ),


    -- ========================================================
    -- WORKING CAPITAL INTELLIGENCE
    -- ========================================================

    (
        'WC001',
        'Overdue Receivables Exposure',
        'working_capital',
        'recorded_overdue_receivables',
        'recorded_overdue_receivables > 0',
        'financial_condition',
        'elevated_attention',
        'working_capital_snapshot_available',
        'assess snapshot as of aging_as_of_date',
        'Overdue receivables represent recorded exposure, not verified collectible cash.',
        'Receivables ageing and collections',
        'Identify businesses with recorded overdue customer receivables.'
    ),

    (
        'WC002',
        'Overdue Payables Exposure',
        'working_capital',
        'recorded_overdue_payables',
        'recorded_overdue_payables > 0',
        'financial_condition',
        'elevated_attention',
        'working_capital_snapshot_available',
        'assess snapshot as of aging_as_of_date',
        'Overdue supplier bills represent recorded obligations, not independently verified cash outflows.',
        'Payables ageing and supplier obligations',
        'Identify businesses with recorded overdue supplier payables.'
    ),

    (
        'WC003',
        'Receivables Missing Due Dates',
        'working_capital',
        'open_invoice_missing_due_date_count',
        'open_invoice_missing_due_date_count > 0',
        'evidence_limitation',
        'evidence_review',
        'working_capital_snapshot_available',
        'assess snapshot as of aging_as_of_date',
        'Invoices without due dates cannot be reliably classified by overdue status.',
        'Receivables ageing reliability',
        'Identify open receivables with missing due dates.'
    ),

    (
        'WC004',
        'Payables Missing Due Dates',
        'working_capital',
        'open_bill_missing_due_date_count',
        'open_bill_missing_due_date_count > 0',
        'evidence_limitation',
        'evidence_review',
        'working_capital_snapshot_available',
        'assess snapshot as of aging_as_of_date',
        'Bills without due dates cannot be reliably classified by overdue status.',
        'Payables ageing reliability',
        'Identify open supplier bills with missing due dates.'
    ),


    -- ========================================================
    -- PROFITABILITY INTELLIGENCE
    -- ========================================================

    (
        'PROF001',
        'Profitability Evidence Not Verified',
        'profitability',
        'consolidated_profitability_evidence_status',
        'consolidated_profitability_evidence_status = provisional_comparison_accounting_expenses_unverified',
        'evidence_limitation',
        'evidence_review',
        'historical_revenue_and_expense_comparison_available',
        'reassess when verified accounting expense evidence becomes available',
        'Invoice-to-bill differences are provisional comparisons and must not be represented as accounting profit or loss.',
        'Profitability evidence reliability',
        'Identify businesses whose historical profitability comparison remains provisional.'
    ),

    (
        'PROF002',
        'Incomplete Profitability Source Coverage',
        'profitability',
        'months_with_incomplete_source_coverage',
        'months_with_incomplete_source_coverage > 0',
        'evidence_limitation',
        'insufficient_evidence',
        'historical_source_coverage_available',
        'reassess when comparable source records become available',
        'Incomplete revenue or expense coverage limits historical comparison.',
        'Profitability evidence coverage',
        'Identify businesses with historical months lacking comparable revenue and expense records.'
    )

) AS rules (

    rule_id,
    rule_name,
    evidence_domain,
    indicator_name,
    rule_condition,
    insight_category,
    severity,
    confidence_requirement,
    persistence_requirement,
    evidence_limitation,
    management_attention_area,
    rule_description

);
