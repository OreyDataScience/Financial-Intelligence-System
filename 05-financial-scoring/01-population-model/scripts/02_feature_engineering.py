"""
Orey Analytics
Financial Health Scoring — Population Model

Purpose: Create financially meaningful SME risk features from audited pop. dataset.

Important:
    - Source data is never modified.
    - Outcome variables are excluded from predictors.
    - Features calculated using info available at the observation/snapshot level.
    - Transaction-level features aonly used where the transaction
      date can be aligned to the relevant observation window.
"""

# IMPORTS
from pathlib import Path
import pandas as pd
import numpy as np

# PROJECT PATHS
SCRIPT_DIR = Path(__file__).resolve().parent
MODEL_DIR = SCRIPT_DIR.parent

DATA_DIR = MODEL_DIR / "data"
OUTPUT_DIR = MODEL_DIR / "outputs"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PANEL_FILE = DATA_DIR / "sme financial health panel.csv"
TRANSACTION_FILE = DATA_DIR / "sme transactions sample.csv"

# LOAD DATA
print("=" * 80)
print("OREY ANALYTICS — FINANCIAL HEALTH SCORING")
print("02 — FEATURE ENGINEERING")
print("=" * 80)

print("\nLoading datasets...")

panel = pd.read_csv(PANEL_FILE)
transactions = pd.read_csv(TRANSACTION_FILE)

print(f"Panel observations: {len(panel):,}")
print(f"Transaction observations: {len(transactions):,}")

# DATE STANDARDISATION
print("\nStandardising dates...")

panel["snapshot_date"] = pd.to_datetime(
    panel["snapshot_date"],
    errors="coerce"
)

panel["bureau_snapshot_date"] = pd.to_datetime(
    panel["bureau_snapshot_date"],
    errors="coerce"
)

transactions["transaction_date"] = pd.to_datetime(
    transactions["transaction_date"],
    errors="coerce"
)

# HELPER FUNCTIONS
def safe_divide(numerator, denominator):
    """
    Division that returns NaN when denominator is zero or missing.
    This avoids creating artificial infinite values.
    """
    numerator = pd.to_numeric(numerator, errors="coerce")
    denominator = pd.to_numeric(denominator, errors="coerce")

    return numerator.div(
        denominator.replace(0, np.nan)
    )

# 1. CASH-FLOW STABILITY FEATURES
print("\nCreating cash-flow stability features...")

# Credit volatility already supplied in the source data, retaining as raw model candidate

panel["fe_credit_volatility"] = panel["credit_volatility_90d"]

# Cash-flow trend.
panel["fe_cash_flow_trend"] = panel["cash_flow_trend_90d"]

# Minimum balance relative to average balance.
panel["fe_min_to_avg_balance"] = safe_divide(
    panel["min_balance_90d"],
    panel["avg_balance_90d"]
)

# Average weekly credits relative to fixed monthly debits.
panel["fe_weekly_credits_to_fixed_debits"] = safe_divide(
    panel["avg_weekly_credits_90d"] * 4.33,
    panel["fixed_monthly_debits"]
)

# Credit growth between 90-day and 180-day windows.
panel["fe_credit_growth_90_vs_180"] = (
    safe_divide(
        panel["total_credits_90d"] * 2,
        panel["total_credits_180d"]
    ) - 1
)

# Credit growth between 180-day and 365-day windows.
panel["fe_credit_growth_180_vs_365"] = (
    safe_divide(
        panel["total_credits_180d"] * 2,
        panel["total_credits_365d"]
    ) - 1
)

# 2. CASH BUFFER/LIQUIDITY FEATURES
print("Creating liquidity features...")

# Average balance relative to monthly expenses.
panel["fe_balance_to_monthly_expenses"] = safe_divide(
    panel["avg_balance_90d"],
    panel["monthly_expenses"]
)

# Minimum balance relative to monthly expenses.
panel["fe_min_balance_to_expenses"] = safe_divide(
    panel["min_balance_90d"],
    panel["monthly_expenses"]
)

# Negative balance frequency is already supplied.
panel["fe_negative_balance_frequency"] = (
    panel["negative_balance_frequency_90d"]
)

# Negative balance days.
panel["fe_negative_balance_days"] = (
    panel["negative_balance_days_90d"]
)

# 3. FREE CASH/DEBT SERVICEABILITY
print("Creating debt-serviceability features...")

# Free cash after fixed monthly debits.
panel["fe_free_cash_after_fixed_debits"] = (
    panel["free_cash_flow"]
    - panel["fixed_monthly_debits"]
)

# Free cash as a percentage of monthly revenue.
panel["fe_free_cash_margin"] = safe_divide(
    panel["free_cash_flow"],
    panel["monthly_revenue"]
)

# Fixed debits as a percentage of monthly revenue.
panel["fe_fixed_debit_burden"] = safe_divide(
    panel["fixed_monthly_debits"],
    panel["monthly_revenue"]
)

# Fixed debits relative to average monthly credits.
panel["fe_fixed_debits_to_credits"] = safe_divide(
    panel["fixed_monthly_debits"],
    panel["total_credits_90d"] / 3
)

# Existing DSCR is retained.
panel["fe_dscr"] = panel["debt_service_coverage_ratio"]

# 4. PROFITABILITY FEATURES
print("Creating profitability features...")

# Operating margin.
panel["fe_operating_margin"] = safe_divide(
    panel["monthly_revenue"] - panel["monthly_expenses"],
    panel["monthly_revenue"]
)

# Expense-to-revenue ratio.
panel["fe_expense_to_revenue"] = safe_divide(
    panel["monthly_expenses"],
    panel["monthly_revenue"]
)

# Free cash flow to expenses.
panel["fe_free_cash_to_expenses"] = safe_divide(
    panel["free_cash_flow"],
    panel["monthly_expenses"]
)

# 5. BALANCE-SHEET / LEVERAGE FEATURES
print("Creating balance-sheet and leverage features...")

# Debt-to-assets.
panel["fe_debt_to_assets"] = safe_divide(
    panel["total_liabilities"],
    panel["total_assets"]
)

# Debt-to-equity.
panel["fe_debt_to_equity"] = safe_divide(
    panel["total_liabilities"],
    panel["total_equity"]
)

# Equity-to-assets.
panel["fe_equity_to_assets"] = safe_divide(
    panel["total_equity"],
    panel["total_assets"]
)

# Liabilities relative to annual revenue.
panel["fe_liabilities_to_annual_revenue"] = safe_divide(
    panel["total_liabilities"],
    panel["annual_revenue"]
)

# Existing debt exposure relative to annual revenue.
panel["fe_debt_exposure_to_revenue"] = safe_divide(
    panel["existing_debt_exposure"],
    panel["annual_revenue"]
)

# 6. OPERATIONAL DISTRESS FEATURES
print("Creating operational distress features...")

# Bounced payments.
panel["fe_bounced_payment_count"] = (
    panel["num_bounced_payments_90d"]
)

# Reversed transactions.
panel["fe_reversed_transaction_count"] = (
    panel["num_reversed_transactions_90d"]
)

# Debit orders.
panel["fe_debit_order_count"] = (
    panel["num_debit_orders_90d"]
)

# Combined operational distress events.
panel["fe_operational_distress_events"] = (
    panel["num_bounced_payments_90d"]
    + panel["num_reversed_transactions_90d"]
)

# Distress events relative to transaction activity.
panel["fe_distress_to_debit_orders"] = safe_divide(
    panel["fe_operational_distress_events"],
    panel["num_debit_orders_90d"]
)

# Fees relative to credits.
panel["fe_fees_to_credits"] = safe_divide(
    panel["total_fees_90d"],
    panel["total_credits_90d"]
)

# 7. BUREAU FEATURES
print("Creating business bureau features...")

panel["fe_business_credit_score"] = (
    panel["credit_score_business"]
)

panel["fe_business_credit_utilization"] = (
    panel["credit_utilization_business"]
)

panel["fe_business_arrears_days"] = (
    panel["arrears_days_bureau"]
)

panel["fe_business_judgments"] = (
    panel["judgments_count"]
)

panel["fe_business_credit_facilities"] = (
    panel["num_credit_facilities"]
)

panel["fe_bureau_debt_to_revenue"] = safe_divide(
    panel["existing_debt_exposure"],
    panel["annual_revenue"]
)

# 8. DIRECTOR RISK FEATURES
print("Creating director risk features...")

panel["fe_director_credit_score"] = (
    panel["director_credit_score"]
)

panel["fe_director_credit_utilization"] = (
    panel["director_credit_utilization"]
)

panel["fe_director_judgments"] = (
    panel["director_judgments_count"]
)

# Difference between business and director utilization.
panel["fe_business_vs_director_utilization"] = (
    panel["credit_utilization_business"]
    - panel["director_credit_utilization"]
)

# 9. BUSINESS STRUCTURE FEATURES
print("Creating structural features...")

panel["fe_business_age"] = panel["business_age_years"]

panel["fe_num_directors"] = panel["num_directors"]

# Revenue per director.
panel["fe_revenue_per_director"] = safe_divide(
    panel["monthly_revenue"],
    panel["num_directors"]
)

# 10. TRANSACTION-LEVEL FEATURES
print("\nCreating transaction-level features...")

# These features are calculated for the transaction sample only.
# We will later merge them to panel observations only when the transaction
# history is available before the relevant snapshot date.

transaction_features = (
    transactions
    .groupby("business_id")
    .agg(
        fe_transaction_count=("transaction_amount", "count"),
        fe_transaction_amount_mean=("transaction_amount", "mean"),
        fe_transaction_amount_std=("transaction_amount", "std"),
        fe_transaction_amount_total=("transaction_amount", "sum"),
        fe_transaction_balance_mean=("account_balance_after", "mean"),
        fe_transaction_balance_min=("account_balance_after", "min")
    )
    .reset_index()
)

# Transaction status counts.
status_counts = pd.crosstab(
    transactions["business_id"],
    transactions["transaction_status"]
).reset_index()

status_counts.columns.name = None

status_counts = status_counts.rename(
    columns={
        "Unpaid": "fe_unpaid_transaction_count",
        "Bounced": "fe_bounced_transaction_count",
        "Reversed": "fe_reversed_transaction_count",
        "Paid": "fe_paid_transaction_count"
    }
)

transaction_features = transaction_features.merge(
    status_counts,
    on="business_id",
    how="left"
)

# Transaction type counts.
type_counts = pd.crosstab(
    transactions["business_id"],
    transactions["transaction_type"]
).reset_index()

type_counts.columns.name = None

transaction_features = transaction_features.merge(
    type_counts,
    on="business_id",
    how="left"
)

# TRANSACTION FEATURE RATIOS
if "fe_unpaid_transaction_count" in transaction_features.columns:

    transaction_features["fe_unpaid_transaction_rate"] = safe_divide(
        transaction_features["fe_unpaid_transaction_count"],
        transaction_features["fe_transaction_count"]
    )

if "fe_bounced_transaction_count" in transaction_features.columns:

    transaction_features["fe_bounced_transaction_rate"] = safe_divide(
        transaction_features["fe_bounced_transaction_count"],
        transaction_features["fe_transaction_count"]
    )

if "fe_reversed_transaction_count" in transaction_features.columns:

    transaction_features["fe_reversed_transaction_rate"] = safe_divide(
        transaction_features["fe_reversed_transaction_count"],
        transaction_features["fe_transaction_count"]
    )

# TRANSACTION DATE COVERAGE
transaction_date_summary = (
    transactions
    .groupby("business_id")
    .agg(
        transaction_first_date=("transaction_date", "min"),
        transaction_last_date=("transaction_date", "max")
    )
    .reset_index()
)

transaction_features = transaction_features.merge(
    transaction_date_summary,
    on="business_id",
    how="left"
)

# MERGING TRANSACTION FEATURES
panel = panel.merge(
    transaction_features,
    on="business_id",
    how="left"
)

# TRANSACTION TEMPORAL ALIGNMENT CHECK
print("\nChecking transaction temporal alignment...")

panel["fe_transaction_history_available"] = (
    panel["transaction_last_date"].notna()
    & (
        panel["transaction_last_date"]
        <= panel["snapshot_date"]
    )
)

# Number of panel obs. for which transaction info exists but extends beyond the scoring snapshot.

panel["fe_transaction_future_leakage_flag"] = (
    panel["transaction_last_date"].notna()
    & (
        panel["transaction_last_date"]
        > panel["snapshot_date"]
    )
)

future_transaction_count = (
    panel["fe_transaction_future_leakage_flag"]
    .sum()
)

print(
    f"Panel observations with transaction history: "
    f"{panel['fe_transaction_history_available'].sum():,}"
)

print(
    f"Potential future transaction leakage observations: "
    f"{future_transaction_count:,}"
)

# MODEL/OUTCOME VARIABLES
print("\nCreating modelling metadata...")

# These variables must NEVER become predictors.
OUTCOME_COLUMNS = [
    "default_event_12m",
    "default_type",
    "default_date",
    "outcome_observable",
    "outcome_window_end",
    "model_split"
]

# Administrative identifiers.
IDENTIFIER_COLUMNS = [
    "business_id",
    "snapshot_date",
    "bureau_snapshot_date"
]

# ENGINEERED FEATURE LIST
engineered_features = [
    column
    for column in panel.columns
    if column.startswith("fe_")
]

print(
    f"\nEngineered features created: "
    f"{len(engineered_features):,}"
)

for feature in engineered_features:
    print(f"  - {feature}")

# FEATURE DATASET
print("\nCreating modelling feature dataset...")

# Keep all orig. variables for traceability, but identify the variables eligible for modelling separately.

model_features = (
    panel
    .loc[
        panel["outcome_observable"] == True
    ]
    .copy()
)

print(
    f"Observations with observable outcomes: "
    f"{len(model_features):,}"
)

# FEATURE METADATA
feature_metadata = pd.DataFrame({
    "feature": engineered_features,
    "source_type": "engineered",
    "description": "",
    "risk_direction_expected": ""
})

# Add descriptions for key engineered variables.

descriptions = {
    "fe_credit_volatility": "90-day credit volatility measure.",

    "fe_cash_flow_trend": "90-day cash-flow trend.",

    "fe_min_to_avg_balance": "Minimum 90-day balance divided by average 90-day balance.",

    "fe_weekly_credits_to_fixed_debits": "Estimated monthly credit inflow relative to fixed monthly debits.",

    "fe_free_cash_after_fixed_debits": "Free cash flow after fixed monthly debits.",

    "fe_free_cash_margin": "Free cash flow divided by monthly revenue.",

    "fe_fixed_debit_burden": "Fixed monthly debits divided by monthly revenue.",

    "fe_fixed_debits_to_credits": "Fixed monthly debits relative to average monthly credits.",

    "fe_operating_margin": "Monthly operating surplus divided by monthly revenue.",

    "fe_expense_to_revenue": "Monthly expenses divided by monthly revenue.",

    "fe_debt_to_assets": "Total liabilities divided by total assets.",

    "fe_debt_to_equity": "Total liabilities divided by total equity.",

    "fe_equity_to_assets": "Total equity divided by total assets.",

    "fe_debt_exposure_to_revenue": "Existing debt exposure divided by annual revenue.",

    "fe_operational_distress_events": "Combined bounced payment and reversed transaction count.",

    "fe_distress_to_debit_orders": "Operational distress events relative to debit orders.",

    "fe_business_credit_utilization": "Business bureau credit utilization.",

    "fe_business_judgments": "Number of business bureau judgments.",

    "fe_director_credit_utilization": "Director bureau credit utilization.",

    "fe_director_judgments": "Number of director judgments.",

    "fe_business_vs_director_utilization": "Difference between business and director credit utilization.",

    "fe_revenue_per_director": "Monthly revenue divided by number of directors."
}

feature_metadata["description"] = (
    feature_metadata["feature"]
    .map(descriptions)
    .fillna("")
)

# SAVE OUTPUTS
print("\nSaving engineered datasets...")

# Full engineered panel.
panel.to_csv(
    OUTPUT_DIR / "financial_health_panel_engineered.csv",
    index=False
)

# Transaction feature table.
transaction_features.to_csv(
    OUTPUT_DIR / "transaction_features.csv",
    index=False
)

# Feature metadata.
feature_metadata.to_csv(
    OUTPUT_DIR / "feature_metadata.csv",
    index=False
)

# FEATURE SUMMARY
feature_summary = pd.DataFrame({
    "feature": engineered_features,
    "dtype": [
        str(panel[feature].dtype)
        for feature in engineered_features
    ],
    "missing_count": [
        panel[feature].isna().sum()
        for feature in engineered_features
    ],
    "missing_pct": [
        panel[feature].isna().mean() * 100
        for feature in engineered_features
    ],
    "unique_values": [
        panel[feature].nunique(dropna=True)
        for feature in engineered_features
    ]
})

feature_summary = feature_summary.sort_values(
    "missing_pct",
    ascending=False
)

feature_summary.to_csv(
    OUTPUT_DIR / "engineered_feature_summary.csv",
    index=False
)

# COMPLETION
print("\n" + "=" * 80)
print("FEATURE ENGINEERING COMPLETE")
print("=" * 80)

print(
    f"\nEngineered features: {len(engineered_features):,}"
)

print(
    "\nOutputs saved to:"
)

print(OUTPUT_DIR)

print("\nSource datasets were not modified.")

print("\nNext stage:")
print("03 — preprocessing, missingness treatment and leakage controls")