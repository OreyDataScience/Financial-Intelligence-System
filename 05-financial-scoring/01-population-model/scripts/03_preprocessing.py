"""
Orey Analytics
Financial Health Scoring - Preprocessing & Leakage control

Purpose: Prepare engineered SME population dataset for credit-risk modelling.

Key principles:
    1. The 12-month default event is the modelling target.
    2. Preprocessing parameters are learned from TRAINING data only.
    3. Validation and test data are transformed using training-derived values.
    4. Structural transaction-data missingness is not blindly imputed.
    5. Missingness indicators preserve information about unavailable data.
    6. Categorical variables are numerically encoded.
    7. Near-zero-variance predictors are removed.
    8. Outcome and administrative variables are excluded from predictors.
"""

# IMPORTS
from pathlib import Path
import json
import warnings

import numpy as np
import pandas as pd

from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.feature_selection import VarianceThreshold

warnings.filterwarnings("ignore")

# PROJECT PATHS
SCRIPT_DIR = Path(__file__).resolve().parent
MODEL_DIR = SCRIPT_DIR.parent

DATA_DIR = MODEL_DIR / "data"
OUTPUT_DIR = MODEL_DIR / "outputs"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

INPUT_FILE = OUTPUT_DIR / "financial_health_panel_engineered.csv"

# CONFIGURATION
TARGET = "default_event_12m"

# Transaction aggregates are based on only 300 of the 11,500 businesses therefore have 
# approx. 97.4% structural missingness and excluded from the primary pop. model at this stage.

TRANSACTION_FEATURES = [
    "fe_transaction_count",
    "fe_transaction_amount_mean",
    "fe_transaction_amount_std",
    "fe_transaction_amount_total",
    "fe_transaction_balance_mean",
    "fe_transaction_balance_min",
    "fe_bounced_transaction_count",
    "fe_paid_transaction_count",
    "fe_reversed_transaction_count_y",
    "fe_unpaid_transaction_count",
    "fe_unpaid_transaction_rate",
    "fe_bounced_transaction_rate",
    "fe_reversed_transaction_rate",
]

# Metadata/administrative variables that should never be predictors.
ADMIN_COLUMNS = [
    "business_id",
    "snapshot_date",
    "bureau_snapshot_date",
    "observation_seq",
    "outcome_observable",
    "outcome_window_end",
    "model_split",
    "default_type",
    "default_date",
]

# Target / outcome variable.
OUTCOME_COLUMNS = [
    "default_event_12m",
]

# Historical bureau variables that are potentially legitimate predictors NOT automatically 
# removed because they are correlated with default. They represent historical credit info 
# available around scoring obs. and will be evaluated later for predictive power & leakage.

BUREAU_HISTORY_FEATURES = [
    "judgments_count",
    "default_flag_bureau_history",
    "director_judgments_count",
]

# Categorical structural variables.
CATEGORICAL_COLUMNS = [
    "province",
    "industry_sector",
    "legal_entity_type",
]

# Important variables where missingness itself can carry information.
MISSINGNESS_INDICATOR_COLUMNS = [
    "annual_revenue",
    "total_assets",
    "total_liabilities",
    "total_equity",
    "existing_debt_exposure",
    "credit_score_business",
    "credit_utilization_business",
    "arrears_days_bureau",
    "director_credit_score",
    "director_credit_utilization",
    "business_age_years",
    "cash_flow_trend_90d",
    "fe_equity_to_assets",
    "fe_debt_to_equity",
    "fe_debt_to_assets",
    "fe_business_vs_director_utilization",
    "fe_liabilities_to_annual_revenue",
    "fe_bureau_debt_to_revenue",
    "fe_debt_exposure_to_revenue",
    "fe_director_credit_utilization",
    "fe_director_credit_score",
]

# HEADER
print("=" * 80)
print("OREY ANALYTICS — FINANCIAL HEALTH SCORING")
print("03 — PREPROCESSING & LEAKAGE CONTROL")
print("=" * 80)

# LOAD ENGINEERED DATA
print("\nLoading engineered population dataset...")

df = pd.read_csv(INPUT_FILE)

print(f"Rows loaded: {len(df):,}")
print(f"Columns loaded: {len(df.columns):,}")

# BASIC VALIDATION
required_columns = [
    TARGET,
    "model_split",
    "outcome_observable",
    "business_id",
    "snapshot_date",
]

missing_required = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_required:
    raise ValueError(
        f"Required columns are missing: {missing_required}"
    )

# TARGET VALIDATION
print("\n" + "=" * 80)
print("TARGET VALIDATION")
print("=" * 80)

print("\nTarget distribution before filtering:")

print(
    df[TARGET]
    .value_counts(dropna=False)
    .sort_index()
)

# OUTCOME OBSERVABILITY FILTER
print("\nFiltering to observations with observable outcomes...")

df = df.loc[
    df["outcome_observable"] == True
].copy()

print(
    f"Observable outcome observations: {len(df):,}"
)

if df[TARGET].isna().any():
    raise ValueError(
        "Observable observations contain missing target values."
    )

# TARGET STANDARDISATION
df[TARGET] = pd.to_numeric(
    df[TARGET],
    errors="coerce"
)

df = df.loc[
    df[TARGET].isin([0, 1])
].copy()

df[TARGET] = df[TARGET].astype(int)

print("\nFinal target distribution:")

target_counts = df[TARGET].value_counts().sort_index()

print(target_counts)

target_rate = df[TARGET].mean()

print(
    f"\nObserved 12-month default rate: "
    f"{target_rate:.2%}"
)

# MODEL SPLIT VALIDATION
print("\n" + "=" * 80)
print("MODEL SPLIT VALIDATION")
print("=" * 80)

print(
    df["model_split"]
    .value_counts(dropna=False)
)

VALID_SPLITS = {"train", "validation", "test"}

invalid_splits = set(
    df["model_split"].unique()
) - VALID_SPLITS

if invalid_splits:
    raise ValueError(
        f"Unexpected model splits found: {invalid_splits}"
    )

if df["model_split"].isna().any():
    raise ValueError(
        "Missing model_split values detected."
    )

# BUSINESS-LEVEL SPLIT CHECK
print("\nChecking business-level split integrity...")

business_split_counts = (
    df.groupby("business_id")["model_split"]
    .nunique()
)

businesses_in_multiple_splits = (
    business_split_counts > 1
).sum()

print(
    f"Businesses appearing in multiple model splits: "
    f"{businesses_in_multiple_splits:,}"
)

if businesses_in_multiple_splits > 0:
    print(
        "\nWARNING:"
        "\nSome businesses appear in more than one model split."
        "\nThis can create entity-level leakage."
    )

# REMOVE TRANSACTION FEATURES
print("\n" + "=" * 80)
print("TRANSACTION FEATURE CONTROL")
print("=" * 80)

transaction_columns_present = [
    column
    for column in TRANSACTION_FEATURES
    if column in df.columns
]

print(
    f"Transaction-derived features excluded: "
    f"{len(transaction_columns_present)}"
)

for column in transaction_columns_present:
    print(f"  - {column}")

df = df.drop(
    columns=transaction_columns_present,
    errors="ignore"
)

# REMOVE ADMINISTRATIVE/OUTCOME COLUMNS
print("\nRemoving administrative and outcome variables...")

columns_to_exclude = (
    ADMIN_COLUMNS
    + OUTCOME_COLUMNS
)

columns_to_exclude = list(
    dict.fromkeys(columns_to_exclude)
)

columns_present = [
    column
    for column in columns_to_exclude
    if column in df.columns
]

df_model = df.drop(
    columns=columns_present,
    errors="ignore"
).copy()

print(
    f"Administrative/outcome columns removed: "
    f"{len(columns_present)}"
)

# CHECK FOR INF/-INF
print("\nChecking for infinite values...")

numeric_columns = df_model.select_dtypes(
    include=np.number
).columns

infinity_counts = {}

for column in numeric_columns:

    count = np.isinf(
        df_model[column].to_numpy(
            dtype=float
        )
    ).sum()

    if count > 0:
        infinity_counts[column] = int(count)

print(
    f"Columns containing infinite values: "
    f"{len(infinity_counts)}"
)

for column, count in infinity_counts.items():

    print(
        f"  - {column}: {count:,}"
    )

# Convert infinity to missing.
if infinity_counts:

    df_model[numeric_columns] = (
        df_model[numeric_columns]
        .replace(
            [np.inf, -np.inf],
            np.nan
        )
    )

# CREATE MISSINGNESS INDICATORS
print("\n" + "=" * 80)
print("MISSINGNESS INDICATORS")
print("=" * 80)

created_indicators = []

for column in MISSINGNESS_INDICATOR_COLUMNS:

    if column not in df_model.columns:
        continue

    indicator_name = (
        f"{column}_missing"
    )

    df_model[indicator_name] = (
        df_model[column]
        .isna()
        .astype(int)
    )

    created_indicators.append(
        indicator_name
    )

print(
    f"Missingness indicators created: "
    f"{len(created_indicators)}"
)

for indicator in created_indicators:
    print(f"  - {indicator}")

# IDENTIFY CATEGORICAL VARIABLES
categorical_columns = [
    column
    for column in CATEGORICAL_COLUMNS
    if column in df_model.columns
]

print("\nCategorical variables:")

for column in categorical_columns:

    print(
        f"  - {column}: "
        f"{df_model[column].nunique(dropna=True)} "
        f"categories"
    )

# IDENTIFY NUMERICAL VARIABLES
numeric_columns = [
    column
    for column in df_model.columns
    if pd.api.types.is_numeric_dtype(
        df_model[column]
    )
]

non_numeric_columns = [
    column
    for column in df_model.columns
    if column not in numeric_columns
    and column not in categorical_columns
]

if non_numeric_columns:

    print("\nNon-numeric non-categorical columns excluded:")

    for column in non_numeric_columns:
        print(f"  - {column}: {df_model[column].dtype}")

    df_model = df_model.drop(
        columns=non_numeric_columns,
        errors="ignore"
    )

print(
    f"\nNumerical variables before preprocessing: "
    f"{len(numeric_columns)}"
)

# SPLIT DATA
print("\n" + "=" * 80)
print("TRAIN / VALIDATION / TEST SPLIT")
print("=" * 80)

train = df_model.loc[
    df["model_split"] == "train"
].copy()

validation = df_model.loc[
    df["model_split"] == "validation"
].copy()

test = df_model.loc[
    df["model_split"] == "test"
].copy()

print(f"Training observations:   {len(train):,}")
print(f"Validation observations: {len(validation):,}")
print(f"Test observations:       {len(test):,}")

# SEPARATE TARGET
y_train = df.loc[
    df["model_split"] == "train",
    TARGET
].astype(int)

y_validation = df.loc[
    df["model_split"] == "validation",
    TARGET
].astype(int)

y_test = df.loc[
    df["model_split"] == "test",
    TARGET
].astype(int)

X_train = train.copy()
X_validation = validation.copy()
X_test = test.copy()

# REMOVE TARGET FROM X
for dataset in [
    X_train,
    X_validation,
    X_test
]:

    if TARGET in dataset.columns:

        dataset.drop(
            columns=[TARGET],
            inplace=True
        )

# MEDIAN IMPUTATION
print("\n" + "=" * 80)
print("NUMERICAL IMPUTATION")
print("=" * 80)

numeric_features = [
    column
    for column in X_train.columns
    if column in numeric_columns
]

print(
    f"Numerical features: "
    f"{len(numeric_features)}"
)

numeric_imputer = SimpleImputer(
    strategy="median"
)

X_train_numeric = numeric_imputer.fit_transform(
    X_train[numeric_features]
)

X_validation_numeric = numeric_imputer.transform(
    X_validation[numeric_features]
)

X_test_numeric = numeric_imputer.transform(
    X_test[numeric_features]
)

X_train_numeric = pd.DataFrame(
    X_train_numeric,
    columns=numeric_features,
    index=X_train.index
)

X_validation_numeric = pd.DataFrame(
    X_validation_numeric,
    columns=numeric_features,
    index=X_validation.index
)

X_test_numeric = pd.DataFrame(
    X_test_numeric,
    columns=numeric_features,
    index=X_test.index
)

# CATEGORICAL IMPUTATION + ONE-HOT ENCODING
print("\n" + "=" * 80)
print("CATEGORICAL ENCODING")
print("=" * 80)

if categorical_columns:

    categorical_imputer = SimpleImputer(
        strategy="most_frequent"
    )

    X_train_cat = categorical_imputer.fit_transform(
        X_train[categorical_columns]
    )

    X_validation_cat = categorical_imputer.transform(
        X_validation[categorical_columns]
    )

    X_test_cat = categorical_imputer.transform(
        X_test[categorical_columns]
    )

    encoder = OneHotEncoder(
        handle_unknown="ignore",
        sparse_output=False
    )

    X_train_cat_encoded = encoder.fit_transform(
        X_train_cat
    )

    X_validation_cat_encoded = encoder.transform(
        X_validation_cat
    )

    X_test_cat_encoded = encoder.transform(
        X_test_cat
    )

    encoded_columns = encoder.get_feature_names_out(
        categorical_columns
    )

    X_train_cat_encoded = pd.DataFrame(
        X_train_cat_encoded,
        columns=encoded_columns,
        index=X_train.index
    )

    X_validation_cat_encoded = pd.DataFrame(
        X_validation_cat_encoded,
        columns=encoded_columns,
        index=X_validation.index
    )

    X_test_cat_encoded = pd.DataFrame(
        X_test_cat_encoded,
        columns=encoded_columns,
        index=X_test.index
    )

else:

    encoded_columns = []

    X_train_cat_encoded = pd.DataFrame(
        index=X_train.index
    )

    X_validation_cat_encoded = pd.DataFrame(
        index=X_validation.index
    )

    X_test_cat_encoded = pd.DataFrame(
        index=X_test.index
    )

# COMBINE NUMERICAL + CATEGORICAL FEATURES
X_train_processed = pd.concat(
    [
        X_train_numeric,
        X_train_cat_encoded
    ],
    axis=1
)

X_validation_processed = pd.concat(
    [
        X_validation_numeric,
        X_validation_cat_encoded
    ],
    axis=1
)

X_test_processed = pd.concat(
    [
        X_test_numeric,
        X_test_cat_encoded
    ],
    axis=1
)

# ALIGN COLUMNS
X_validation_processed = (
    X_validation_processed
    .reindex(
        columns=X_train_processed.columns,
        fill_value=0
    )
)

X_test_processed = (
    X_test_processed
    .reindex(
        columns=X_train_processed.columns,
        fill_value=0
    )
)

# NEAR-ZERO-VARIANCE FILTER
print("\n" + "=" * 80)
print("NEAR-ZERO-VARIANCE FILTER")
print("=" * 80)

variance_filter = VarianceThreshold(
    threshold=0.0
)

X_train_filtered_array = (
    variance_filter.fit_transform(
        X_train_processed
    )
)

X_validation_filtered_array = (
    variance_filter.transform(
        X_validation_processed
    )
)

X_test_filtered_array = (
    variance_filter.transform(
        X_test_processed
    )
)

kept_columns = (
    X_train_processed.columns[
        variance_filter.get_support()
    ]
)

removed_columns = (
    X_train_processed.columns[
        ~variance_filter.get_support()
    ]
)

X_train_processed = pd.DataFrame(
    X_train_filtered_array,
    columns=kept_columns,
    index=X_train.index
)

X_validation_processed = pd.DataFrame(
    X_validation_filtered_array,
    columns=kept_columns,
    index=X_validation.index
)

X_test_processed = pd.DataFrame(
    X_test_filtered_array,
    columns=kept_columns,
    index=X_test.index
)

print(
    f"Features before variance filtering: "
    f"{len(variance_filter.get_support())}"
)

print(
    f"Features retained: "
    f"{len(kept_columns)}"
)

print(
    f"Features removed: "
    f"{len(removed_columns)}"
)

if len(removed_columns) > 0:

    print("\nRemoved features:")

    for column in removed_columns:
        print(f"  - {column}")

# FINAL VALIDATION
print("\n" + "=" * 80)
print("FINAL PREPROCESSING VALIDATION")
print("=" * 80)

print(
    f"Training shape:   "
    f"{X_train_processed.shape}"
)

print(
    f"Validation shape: "
    f"{X_validation_processed.shape}"
)

print(
    f"Test shape:       "
    f"{X_test_processed.shape}"
)

print(
    f"\nTraining default rate:   "
    f"{y_train.mean():.2%}"
)

print(
    f"Validation default rate: "
    f"{y_validation.mean():.2%}"
)

print(
    f"Test default rate:       "
    f"{y_test.mean():.2%}"
)

print(
    "\nRemaining missing values:"
)

print(
    f"Training:   "
    f"{X_train_processed.isna().sum().sum():,}"
)

print(
    f"Validation: "
    f"{X_validation_processed.isna().sum().sum():,}"
)

print(
    f"Test:       "
    f"{X_test_processed.isna().sum().sum():,}"
)

print(
    "\nRemaining infinite values:"
)

print(
    f"Training:   "
    f"{np.isinf(X_train_processed.to_numpy()).sum():,}"
)

print(
    f"Validation: "
    f"{np.isinf(X_validation_processed.to_numpy()).sum():,}"
)

print(
    f"Test:       "
    f"{np.isinf(X_test_processed.to_numpy()).sum():,}"
)

# SAVING MODEL-READY DATASETS
print("\n" + "=" * 80)
print("SAVING PREPROCESSED DATASETS")
print("=" * 80)

train_output = X_train_processed.copy()
train_output[TARGET] = y_train

validation_output = X_validation_processed.copy()
validation_output[TARGET] = y_validation

test_output = X_test_processed.copy()
test_output[TARGET] = y_test

train_output.to_csv(
    OUTPUT_DIR / "model_train_preprocessed.csv",
    index=False
)

validation_output.to_csv(
    OUTPUT_DIR / "model_validation_preprocessed.csv",
    index=False
)

test_output.to_csv(
    OUTPUT_DIR / "model_test_preprocessed.csv",
    index=False
)

# SAVE FEATURE LIST
feature_list = pd.DataFrame({
    "feature": list(X_train_processed.columns)
})

feature_list.to_csv(
    OUTPUT_DIR / "preprocessed_feature_list.csv",
    index=False
)

# SAVE REMOVED FEATURE LIST
removed_feature_list = pd.DataFrame({
    "feature": list(removed_columns),
    "reason": "zero variance in training data"
})

removed_feature_list.to_csv(
    OUTPUT_DIR / "removed_low_variance_features.csv",
    index=False
)

# SAVE PREPROCESSING METADATA
metadata = {
    "target": TARGET,

    "input_file": str(INPUT_FILE),

    "original_rows": int(len(pd.read_csv(INPUT_FILE))),

    "observable_rows": int(len(df)),

    "train_rows": int(len(X_train_processed)),
    "validation_rows": int(len(X_validation_processed)),
    "test_rows": int(len(X_test_processed)),

    "train_default_rate": float(y_train.mean()),
    "validation_default_rate": float(y_validation.mean()),
    "test_default_rate": float(y_test.mean()),

    "transaction_features_excluded": transaction_columns_present,

    "missingness_indicators_created": created_indicators,

    "categorical_columns": categorical_columns,

    "encoded_categorical_features": list(encoded_columns),

    "numeric_features_before_filter": len(numeric_features),

    "features_before_variance_filter": int(
        len(variance_filter.get_support())
    ),

    "features_after_variance_filter": int(
        len(kept_columns)
    ),

    "features_removed_low_variance": int(
        len(removed_columns)
    ),

    "remaining_training_missing_values": int(
        X_train_processed.isna().sum().sum()
    ),

    "remaining_validation_missing_values": int(
        X_validation_processed.isna().sum().sum()
    ),

    "remaining_test_missing_values": int(
        X_test_processed.isna().sum().sum()
    ),

    "businesses_in_multiple_splits": int(
        businesses_in_multiple_splits
    ),

    "preprocessing_rule": (
        "Imputation and categorical encoding were fitted "
        "on training data only."
    )
}

with open(
    OUTPUT_DIR / "preprocessing_metadata.json",
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        metadata,
        file,
        indent=4
    )

# COMPLETION
print("\n" + "=" * 80)
print("PREPROCESSING COMPLETE")
print("=" * 80)

print("\nOutputs saved to:")

print(OUTPUT_DIR)

print("\nGenerated files:")

print("  - model_train_preprocessed.csv")
print("  - model_validation_preprocessed.csv")
print("  - model_test_preprocessed.csv")
print("  - preprocessed_feature_list.csv")
print("  - removed_low_variance_features.csv")
print("  - preprocessing_metadata.json")

print("\nSource datasets were not modified.")

print("\nNext stage:")
print("04 — WoE, binning and Information Value")