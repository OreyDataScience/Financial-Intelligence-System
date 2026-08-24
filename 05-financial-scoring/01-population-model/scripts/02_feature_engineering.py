"""
Orey Analytics
Financial Health Scoring — Population Model

Stage 02 — Feature Engineering

Purpose:
Create financially meaningful SME risk features from the audited population
dataset while ensuring that transaction-level information is temporally aligned
to each SME observation.

Important:
    - Source data is never modified.
    - Outcome variables are excluded from predictors.
    - Features use information available at the observation/snapshot date.
    - Transaction-level features only use transactions occurring on or before
      the relevant snapshot date.
    - Future transaction information is retained only for leakage auditing and
      is never used as a modelling predictor.
    - Model splits are assigned at business level to prevent entity leakage.
"""

# Imports

from pathlib import Path

import pandas as pd
import numpy as np


# Project paths

SCRIPT_DIR = Path(__file__).resolve().parent
MODEL_DIR = SCRIPT_DIR.parent

DATA_DIR = MODEL_DIR / "data"
OUTPUT_DIR = MODEL_DIR / "outputs"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PANEL_FILE = DATA_DIR / "sme financial health panel.csv"
TRANSACTION_FILE = DATA_DIR / "sme transactions sample.csv"


# Configuration

RANDOM_SEED = 42

TRAIN_SHARE = 0.70
VALIDATION_SHARE = 0.15
TEST_SHARE = 0.15


# Header

print("=" * 80)
print("OREY ANALYTICS — FINANCIAL HEALTH SCORING")
print("02 — FEATURE ENGINEERING")
print("=" * 80)


# Load data

print("\nLoading datasets...")

panel = pd.read_csv(PANEL_FILE)
transactions = pd.read_csv(TRANSACTION_FILE)

print(f"Panel observations: {len(panel):,}")
print(f"Transaction observations: {len(transactions):,}")


# Date standardisation

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


# Helper functions

def safe_divide(numerator, denominator):
    numerator = pd.to_numeric(
        numerator,
        errors="coerce"
    )

    denominator = pd.to_numeric(
        denominator,
        errors="coerce"
    )

    return numerator.div(
        denominator.replace(0, np.nan)
    )


# 1. Cash-flow stability features

print("\nCreating cash-flow stability features...")

panel["fe_credit_volatility"] = (
    panel["credit_volatility_90d"]
)

panel["fe_cash_flow_trend"] = (
    panel["cash_flow_trend_90d"]
)

panel["fe_min_to_avg_balance"] = safe_divide(
    panel["min_balance_90d"],
    panel["avg_balance_90d"]
)

panel["fe_weekly_credits_to_fixed_debits"] = safe_divide(
    panel["avg_weekly_credits_90d"] * 4.33,
    panel["fixed_monthly_debits"]
)

panel["fe_credit_growth_90_vs_180"] = (
    safe_divide(
        panel["total_credits_90d"] * 2,
        panel["total_credits_180d"]
    ) - 1
)

panel["fe_credit_growth_180_vs_365"] = (
    safe_divide(
        panel["total_credits_180d"] * 2,
        panel["total_credits_365d"]
    ) - 1
)


# 2. Cash buffer / liquidity features

print("Creating liquidity features...")

panel["fe_balance_to_monthly_expenses"] = safe_divide(
    panel["avg_balance_90d"],
    panel["monthly_expenses"]
)

panel["fe_min_balance_to_expenses"] = safe_divide(
    panel["min_balance_90d"],
    panel["monthly_expenses"]
)

panel["fe_negative_balance_frequency"] = (
    panel["negative_balance_frequency_90d"]
)

panel["fe_negative_balance_days"] = (
    panel["negative_balance_days_90d"]
)


# 3. Free cash / debt serviceability

print("Creating debt-serviceability features...")

panel["fe_free_cash_after_fixed_debits"] = (
    panel["free_cash_flow"]
    - panel["fixed_monthly_debits"]
)

panel["fe_free_cash_margin"] = safe_divide(
    panel["free_cash_flow"],
    panel["monthly_revenue"]
)

panel["fe_fixed_debit_burden"] = safe_divide(
    panel["fixed_monthly_debits"],
    panel["monthly_revenue"]
)

panel["fe_fixed_debits_to_credits"] = safe_divide(
    panel["fixed_monthly_debits"],
    panel["total_credits_90d"] / 3
)

panel["fe_dscr"] = (
    panel["debt_service_coverage_ratio"]
)


# 4. Profitability features

print("Creating profitability features...")

panel["fe_operating_margin"] = safe_divide(
    panel["monthly_revenue"] - panel["monthly_expenses"],
    panel["monthly_revenue"]
)

panel["fe_expense_to_revenue"] = safe_divide(
    panel["monthly_expenses"],
    panel["monthly_revenue"]
)

panel["fe_free_cash_to_expenses"] = safe_divide(
    panel["free_cash_flow"],
    panel["monthly_expenses"]
)


# 5. Balance-sheet / leverage features

print("Creating balance-sheet and leverage features...")

panel["fe_debt_to_assets"] = safe_divide(
    panel["total_liabilities"],
    panel["total_assets"]
)

panel["fe_debt_to_equity"] = safe_divide(
    panel["total_liabilities"],
    panel["total_equity"]
)

panel["fe_equity_to_assets"] = safe_divide(
    panel["total_equity"],
    panel["total_assets"]
)

panel["fe_liabilities_to_annual_revenue"] = safe_divide(
    panel["total_liabilities"],
    panel["annual_revenue"]
)

panel["fe_debt_exposure_to_revenue"] = safe_divide(
    panel["existing_debt_exposure"],
    panel["annual_revenue"]
)


# 6. Operational distress features

print("Creating operational distress features...")

panel["fe_bounced_payment_count"] = (
    panel["num_bounced_payments_90d"]
)

panel["fe_reversed_transaction_count"] = (
    panel["num_reversed_transactions_90d"]
)

panel["fe_debit_order_count"] = (
    panel["num_debit_orders_90d"]
)

panel["fe_operational_distress_events"] = (
    panel["num_bounced_payments_90d"]
    + panel["num_reversed_transactions_90d"]
)

panel["fe_distress_to_debit_orders"] = safe_divide(
    panel["fe_operational_distress_events"],
    panel["num_debit_orders_90d"]
)

panel["fe_fees_to_credits"] = safe_divide(
    panel["total_fees_90d"],
    panel["total_credits_90d"]
)


# 7. Business bureau features

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


# 8. Director risk features

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

panel["fe_business_vs_director_utilization"] = (
    panel["credit_utilization_business"]
    - panel["director_credit_utilization"]
)


# 9. Business structure features

print("Creating structural features...")

panel["fe_business_age"] = (
    panel["business_age_years"]
)

panel["fe_num_directors"] = (
    panel["num_directors"]
)

panel["fe_revenue_per_director"] = safe_divide(
    panel["monthly_revenue"],
    panel["num_directors"]
)


# 10. Transaction-level features

print("\nCreating temporally aligned transaction-level features...")

transactions = transactions[
    transactions["transaction_date"].notna()
].copy()

transactions = transactions.sort_values(
    ["transaction_date", "business_id"]
).reset_index(drop=True)

transactions["transaction_amount"] = pd.to_numeric(
    transactions["transaction_amount"],
    errors="coerce"
)

transactions["account_balance_after"] = pd.to_numeric(
    transactions["account_balance_after"],
    errors="coerce"
)

transactions["fe_transaction_count"] = (
    transactions
    .groupby("business_id")
    .cumcount()
    + 1
)

transactions["transaction_amount_sum"] = (
    transactions
    .groupby("business_id")["transaction_amount"]
    .cumsum()
)

transactions["transaction_amount_squared"] = (
    transactions["transaction_amount"] ** 2
)

transactions["transaction_amount_squared_sum"] = (
    transactions
    .groupby("business_id")["transaction_amount_squared"]
    .cumsum()
)

transactions["transaction_balance_sum"] = (
    transactions
    .groupby("business_id")["account_balance_after"]
    .cumsum()
)


# Cumulative transaction status counts

status_dummies = pd.get_dummies(
    transactions["transaction_status"],
    prefix="transaction_status"
)

status_dummies.index = transactions.index

transactions = pd.concat(
    [
        transactions,
        status_dummies
    ],
    axis=1
)

for column in status_dummies.columns:
    transactions[f"cum_{column}"] = (
        transactions
        .groupby("business_id")[column]
        .cumsum()
    )


# Cumulative transaction-type counts

type_dummies = pd.get_dummies(
    transactions["transaction_type"],
    prefix="transaction_type"
)

type_dummies.index = transactions.index

transactions = pd.concat(
    [
        transactions,
        type_dummies
    ],
    axis=1
)

for column in type_dummies.columns:
    transactions[f"cum_{column}"] = (
        transactions
        .groupby("business_id")[column]
        .cumsum()
    )


# Cumulative minimum balance

transactions["fe_transaction_balance_min"] = (
    transactions
    .groupby("business_id")["account_balance_after"]
    .cummin()
)


# Create cumulative transaction feature table

transaction_features = transactions[
    [
        "business_id",
        "transaction_date",
        "fe_transaction_count",
        "transaction_amount_sum",
        "transaction_amount_squared_sum",
        "transaction_balance_sum",
        "fe_transaction_balance_min"
    ]
].copy()


# Cumulative transaction amount statistics

n = transaction_features[
    "fe_transaction_count"
].astype(float)

sum_x = transaction_features[
    "transaction_amount_sum"
]

sum_x2 = transaction_features[
    "transaction_amount_squared_sum"
]

transaction_features[
    "fe_transaction_amount_total"
] = sum_x

transaction_features[
    "fe_transaction_amount_mean"
] = safe_divide(
    sum_x,
    n
)

variance_numerator = (
    sum_x2
    - safe_divide(
        sum_x ** 2,
        n
    )
)

variance_numerator = variance_numerator.clip(
    lower=0
)

transaction_features[
    "fe_transaction_amount_std"
] = np.sqrt(
    safe_divide(
        variance_numerator,
        n - 1
    )
)


# Average account balance

transaction_features[
    "fe_transaction_balance_mean"
] = safe_divide(
    transaction_features[
        "transaction_balance_sum"
    ],
    n
)


# Cumulative status counts

for status_name, output_name in [
    (
        "transaction_status_Unpaid",
        "fe_unpaid_transaction_count"
    ),
    (
        "transaction_status_Bounced",
        "fe_bounced_transaction_count"
    ),
    (
        "transaction_status_Reversed",
        "fe_reversed_transaction_count"
    ),
    (
        "transaction_status_Paid",
        "fe_paid_transaction_count"
    )
]:

    cumulative_column = f"cum_{status_name}"

    if cumulative_column in transactions.columns:
        transaction_features[output_name] = (
            transactions[cumulative_column].values
        )


# Transaction-type counts

for column in type_dummies.columns:

    cumulative_column = f"cum_{column}"

    output_column = (
        "fe_"
        + column.lower()
        + "_count"
    )

    transaction_features[output_column] = (
        transactions[cumulative_column].values
    )


# Transaction feature ratios

transaction_features[
    "fe_unpaid_transaction_rate"
] = safe_divide(
    transaction_features.get(
        "fe_unpaid_transaction_count",
        pd.Series(
            np.nan,
            index=transaction_features.index
        )
    ),
    transaction_features[
        "fe_transaction_count"
    ]
)

transaction_features[
    "fe_bounced_transaction_rate"
] = safe_divide(
    transaction_features.get(
        "fe_bounced_transaction_count",
        pd.Series(
            np.nan,
            index=transaction_features.index
        )
    ),
    transaction_features[
        "fe_transaction_count"
    ]
)

transaction_features[
    "fe_reversed_transaction_rate"
] = safe_divide(
    transaction_features.get(
        "fe_reversed_transaction_count",
        pd.Series(
            np.nan,
            index=transaction_features.index
        )
    ),
    transaction_features[
        "fe_transaction_count"
    ]
)


# Merge transaction features using temporal as-of join

print("\nAligning transactions to panel snapshots...")

panel_for_merge = panel[
    [
        "business_id",
        "snapshot_date"
    ]
].copy()

panel_for_merge["_panel_row_id"] = np.arange(
    len(panel_for_merge)
)

panel_for_merge = panel_for_merge.sort_values(
    [
        "snapshot_date",
        "business_id"
    ]
).reset_index(drop=True)

transaction_features_for_merge = (
    transaction_features
    .drop(
        columns=[
            "transaction_amount_sum",
            "transaction_amount_squared_sum",
            "transaction_balance_sum"
        ],
        errors="ignore"
    )
    .copy()
)

transaction_features_for_merge = (
    transaction_features_for_merge
    .sort_values(
        [
            "transaction_date",
            "business_id"
        ]
    )
    .reset_index(drop=True)
)

panel_aligned = pd.merge_asof(
    panel_for_merge,
    transaction_features_for_merge,
    left_on="snapshot_date",
    right_on="transaction_date",
    by="business_id",
    direction="backward",
    allow_exact_matches=True
)

panel_aligned = panel_aligned.sort_values(
    "_panel_row_id"
).reset_index(drop=True)

panel_aligned = panel_aligned.drop(
    columns=[
        "_panel_row_id",
        "snapshot_date",
        "business_id"
    ],
    errors="ignore"
)

panel = panel.reset_index(drop=True)

panel = pd.concat(
    [
        panel,
        panel_aligned
    ],
    axis=1
)


# Transaction temporal alignment audit

print("\nChecking transaction temporal alignment...")

panel["fe_transaction_history_available"] = (
    panel["transaction_date"].notna()
)

business_transaction_last_date = (
    transactions
    .groupby("business_id")[
        "transaction_date"
    ]
    .max()
    .rename(
        "all_transaction_last_date"
    )
    .reset_index()
)

panel = panel.merge(
    business_transaction_last_date,
    on="business_id",
    how="left"
)

panel[
    "fe_transaction_future_leakage_flag"
] = (
    panel["all_transaction_last_date"].notna()
    &
    (
        panel["all_transaction_last_date"]
        > panel["snapshot_date"]
    )
)

future_transaction_count = int(
    panel[
        "fe_transaction_future_leakage_flag"
    ].sum()
)

print(
    f"Panel observations with transaction history available "
    f"at snapshot: "
    f"{panel['fe_transaction_history_available'].sum():,}"
)

print(
    f"Observations where future transactions exist "
    f"after snapshot: "
    f"{future_transaction_count:,}"
)


# Temporal validation

print("\nRunning temporal leakage validation...")

aligned_transaction_dates = (
    panel["transaction_date"]
)

temporal_violations = (
    aligned_transaction_dates.notna()
    &
    (
        aligned_transaction_dates
        > panel["snapshot_date"]
    )
).sum()

print(
    f"Transaction dates after snapshot date: "
    f"{temporal_violations:,}"
)

if temporal_violations > 0:
    raise ValueError(
        "TEMPORAL LEAKAGE DETECTED: "
        "one or more aligned transaction records occur "
        "after the panel snapshot date."
    )

print("Temporal alignment check: PASS")


# Business-level model split

print("\n" + "=" * 80)
print("BUSINESS-LEVEL MODEL SPLIT")
print("=" * 80)

if not np.isclose(
    TRAIN_SHARE + VALIDATION_SHARE + TEST_SHARE,
    1.0
):
    raise ValueError(
        "Model split proportions must sum to 1."
    )

print("\nCreating business-level split assignment...")

split_source = panel[
    [
        "business_id",
        "default_event_12m"
    ]
].copy()

observable_split_source = split_source.loc[
    split_source["default_event_12m"].notna()
].copy()

business_default_profile = (
    observable_split_source
    .groupby("business_id")["default_event_12m"]
    .max()
    .rename("business_default_profile")
)

all_businesses = (
    panel["business_id"]
    .drop_duplicates()
    .to_frame()
)

all_businesses = all_businesses.merge(
    business_default_profile,
    on="business_id",
    how="left"
)

all_businesses["business_default_profile"] = (
    all_businesses["business_default_profile"]
    .fillna(0)
    .astype(int)
)

default_businesses = all_businesses.loc[
    all_businesses["business_default_profile"] == 1
].copy()

non_default_businesses = all_businesses.loc[
    all_businesses["business_default_profile"] == 0
].copy()

default_businesses = default_businesses.sample(
    frac=1,
    random_state=RANDOM_SEED
).reset_index(drop=True)

non_default_businesses = non_default_businesses.sample(
    frac=1,
    random_state=RANDOM_SEED
).reset_index(drop=True)


def assign_group_splits(group):

    n = len(group)

    train_end = int(
        n * TRAIN_SHARE
    )

    validation_end = train_end + int(
        n * VALIDATION_SHARE
    )

    group = group.copy()

    group["model_split"] = "test"

    group.loc[
        :train_end - 1,
        "model_split"
    ] = "train"

    group.loc[
        train_end:validation_end - 1,
        "model_split"
    ] = "validation"

    return group


default_businesses = assign_group_splits(
    default_businesses
)

non_default_businesses = assign_group_splits(
    non_default_businesses
)

business_split_assignment = pd.concat(
    [
        default_businesses,
        non_default_businesses
    ],
    ignore_index=True
)

business_split_assignment = (
    business_split_assignment[
        [
            "business_id",
            "model_split"
        ]
    ]
)

panel = panel.drop(
    columns=["model_split"],
    errors="ignore"
)

panel = panel.merge(
    business_split_assignment,
    on="business_id",
    how="left",
    validate="many_to_one"
)

if panel["model_split"].isna().any():

    missing_split_count = int(
        panel["model_split"].isna().sum()
    )

    raise ValueError(
        f"{missing_split_count:,} panel observations "
        "could not be assigned to a model split."
    )

business_split_counts = (
    business_split_assignment
    .groupby("model_split")["business_id"]
    .nunique()
)

print("\nBusinesses assigned to each split:")

for split in [
    "train",
    "validation",
    "test"
]:

    print(
        f"  {split}: "
        f"{business_split_counts.get(split, 0):,}"
    )

business_split_check = (
    business_split_assignment
    .groupby("business_id")["model_split"]
    .nunique()
)

businesses_in_multiple_splits = int(
    (
        business_split_check > 1
    ).sum()
)

print(
    "\nBusinesses appearing in multiple splits: "
    f"{businesses_in_multiple_splits:,}"
)

if businesses_in_multiple_splits > 0:
    raise ValueError(
        "BUSINESS-LEVEL LEAKAGE DETECTED: "
        "one or more businesses were assigned "
        "to multiple model splits."
    )

print("Business-level split integrity: PASS")


# Model / outcome variables

print("\nCreating modelling metadata...")

OUTCOME_COLUMNS = [
    "default_event_12m",
    "default_type",
    "default_date",
    "outcome_observable",
    "outcome_window_end",
    "model_split"
]

IDENTIFIER_COLUMNS = [
    "business_id",
    "snapshot_date",
    "bureau_snapshot_date"
]


# Engineered feature list

AUDIT_COLUMNS = [
    "fe_transaction_history_available",
    "fe_transaction_future_leakage_flag"
]

engineered_features = [
    column
    for column in panel.columns
    if column.startswith("fe_")
    and column not in AUDIT_COLUMNS
]

print(
    f"\nEngineered modelling features created: "
    f"{len(engineered_features):,}"
)

for feature in engineered_features:
    print(f"  - {feature}")


# Feature dataset

print("\nCreating modelling feature dataset...")

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


# Feature metadata

feature_metadata = pd.DataFrame(
    {
        "feature": engineered_features,
        "source_type": "engineered",
        "description": "",
        "risk_direction_expected": ""
    }
)

descriptions = {
    "fe_credit_volatility":
        "90-day credit volatility measure.",
    "fe_cash_flow_trend":
        "90-day cash-flow trend.",
    "fe_min_to_avg_balance":
        "Minimum 90-day balance divided by average 90-day balance.",
    "fe_weekly_credits_to_fixed_debits":
        "Estimated monthly credit inflow relative to fixed monthly debits.",
    "fe_credit_growth_90_vs_180":
        "Credit growth between the 90-day and 180-day windows.",
    "fe_credit_growth_180_vs_365":
        "Credit growth between the 180-day and 365-day windows.",
    "fe_balance_to_monthly_expenses":
        "Average 90-day balance divided by monthly expenses.",
    "fe_min_balance_to_expenses":
        "Minimum 90-day balance divided by monthly expenses.",
    "fe_negative_balance_frequency":
        "Frequency of negative account balances.",
    "fe_negative_balance_days":
        "Number of days with negative balances.",
    "fe_free_cash_after_fixed_debits":
        "Free cash flow after fixed monthly debits.",
    "fe_free_cash_margin":
        "Free cash flow divided by monthly revenue.",
    "fe_fixed_debit_burden":
        "Fixed monthly debits divided by monthly revenue.",
    "fe_fixed_debits_to_credits":
        "Fixed monthly debits relative to average monthly credits.",
    "fe_dscr":
        "Debt service coverage ratio.",
    "fe_operating_margin":
        "Monthly operating surplus divided by monthly revenue.",
    "fe_expense_to_revenue":
        "Monthly expenses divided by monthly revenue.",
    "fe_free_cash_to_expenses":
        "Free cash flow divided by monthly expenses.",
    "fe_debt_to_assets":
        "Total liabilities divided by total assets.",
    "fe_debt_to_equity":
        "Total liabilities divided by total equity.",
    "fe_equity_to_assets":
        "Total equity divided by total assets.",
    "fe_liabilities_to_annual_revenue":
        "Total liabilities divided by annual revenue.",
    "fe_debt_exposure_to_revenue":
        "Existing debt exposure divided by annual revenue.",
    "fe_operational_distress_events":
        "Combined bounced payment and reversed transaction count.",
    "fe_distress_to_debit_orders":
        "Operational distress events relative to debit orders.",
    "fe_fees_to_credits":
        "Fees relative to total credits.",
    "fe_business_credit_score":
        "Business bureau credit score.",
    "fe_business_credit_utilization":
        "Business bureau credit utilization.",
    "fe_business_arrears_days":
        "Business bureau arrears days.",
    "fe_business_judgments":
        "Number of business bureau judgments.",
    "fe_business_credit_facilities":
        "Number of business credit facilities.",
    "fe_bureau_debt_to_revenue":
        "Existing debt exposure relative to annual revenue.",
    "fe_director_credit_score":
        "Director bureau credit score.",
    "fe_director_credit_utilization":
        "Director bureau credit utilization.",
    "fe_director_judgments":
        "Number of director judgments.",
    "fe_business_vs_director_utilization":
        "Difference between business and director credit utilization.",
    "fe_business_age":
        "Business age in years.",
    "fe_num_directors":
        "Number of directors.",
    "fe_revenue_per_director":
        "Monthly revenue divided by number of directors.",
    "fe_transaction_count":
        "Number of transactions available up to the snapshot date.",
    "fe_transaction_amount_mean":
        "Mean transaction amount available up to the snapshot date.",
    "fe_transaction_amount_std":
        "Sample standard deviation of transaction amounts available up to the snapshot date.",
    "fe_transaction_amount_total":
        "Total transaction amount available up to the snapshot date.",
    "fe_transaction_balance_mean":
        "Mean account balance after transactions available up to the snapshot date.",
    "fe_transaction_balance_min":
        "Minimum account balance observed up to the snapshot date.",
    "fe_unpaid_transaction_count":
        "Cumulative unpaid transaction count up to the snapshot date.",
    "fe_bounced_transaction_count":
        "Cumulative bounced transaction count up to the snapshot date.",
    "fe_reversed_transaction_count":
        "Cumulative reversed transaction count up to the snapshot date.",
    "fe_paid_transaction_count":
        "Cumulative paid transaction count up to the snapshot date.",
    "fe_unpaid_transaction_rate":
        "Unpaid transactions divided by total transactions available up to the snapshot date.",
    "fe_bounced_transaction_rate":
        "Bounced transactions divided by total transactions available up to the snapshot date.",
    "fe_reversed_transaction_rate":
        "Reversed transactions divided by total transactions available up to the snapshot date."
}

feature_metadata["description"] = (
    feature_metadata["feature"]
    .map(descriptions)
    .fillna("")
)


# Save outputs

print("\nSaving engineered datasets...")

panel.to_csv(
    OUTPUT_DIR /
    "financial_health_panel_engineered.csv",
    index=False
)

transaction_features.to_csv(
    OUTPUT_DIR /
    "transaction_features.csv",
    index=False
)

feature_metadata.to_csv(
    OUTPUT_DIR /
    "feature_metadata.csv",
    index=False
)


# Feature summary

print("\nCreating engineered feature summary...")

duplicate_columns = (
    panel.columns[
        panel.columns.duplicated()
    ]
    .tolist()
)

if duplicate_columns:

    print(
        "\nWarning: duplicate column names detected:"
    )

    for column in sorted(set(duplicate_columns)):
        print(f"  - {column}")

    panel = panel.loc[
        :,
        ~panel.columns.duplicated(
            keep="first"
        )
    ].copy()

    engineered_features = [
        column
        for column in panel.columns
        if column.startswith("fe_")
        and column not in AUDIT_COLUMNS
    ]

    print("\nDuplicate columns removed.")

    print(
        f"Final engineered modelling features: "
        f"{len(engineered_features):,}"
    )


feature_summary_rows = []

for feature in engineered_features:

    feature_data = panel.loc[:, feature]

    if isinstance(
        feature_data,
        pd.DataFrame
    ):
        feature_data = feature_data.iloc[:, 0]

    feature_summary_rows.append(
        {
            "feature": feature,
            "dtype": str(
                feature_data.dtype
            ),
            "missing_count": int(
                feature_data.isna().sum()
            ),
            "missing_pct": float(
                feature_data.isna().mean()
                * 100
            ),
            "unique_values": int(
                feature_data.nunique(
                    dropna=True
                )
            )
        }
    )

feature_summary = pd.DataFrame(
    feature_summary_rows
)

feature_summary = feature_summary.sort_values(
    "missing_pct",
    ascending=False
)

feature_summary.to_csv(
    OUTPUT_DIR /
    "engineered_feature_summary.csv",
    index=False
)

print(
    f"\nFeature summary created for "
    f"{len(feature_summary):,} engineered features."
)


# Completion

print("\n" + "=" * 80)
print("FEATURE ENGINEERING COMPLETE")
print("=" * 80)

print(
    f"\nEngineered modelling features: "
    f"{len(engineered_features):,}"
)

print("\nTemporal leakage validation: PASS")

print("Business-level split validation: PASS")

print("\nOutputs saved to:")
print(OUTPUT_DIR)

print("\nSource datasets were not modified.")

print("\nNext stage:")
print(
    "03 — preprocessing, missingness treatment and leakage controls"
)