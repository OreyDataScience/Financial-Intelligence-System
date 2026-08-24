"""
Orey Analytics
Financial Health Scoring - Preprocessing & Leakage Control

Purpose:
Prepare the engineered SME population dataset for WoE, binning and
credit-risk scorecard development.

Key principles:
    1. The 12-month default event is the modelling target.
    2. Preprocessing parameters are learned from training data only.
    3. Validation and test data use training-derived preprocessing values.
    4. Structural transaction-data missingness is preserved.
    5. Missingness indicators preserve information about unavailable data.
    6. Categorical variables remain available for Stage 04 WoE treatment.
    7. Zero-variance predictors are removed using training data only.
    8. Outcome and administrative variables are excluded from predictors.
    9. Historical observations must not use future information.
"""

#Imports
from pathlib import Path
import json
import warnings

import numpy as np
import pandas as pd

from sklearn.impute import SimpleImputer
from sklearn.feature_selection import VarianceThreshold

warnings.filterwarnings("ignore")

#Project paths
SCRIPT_DIR = Path(__file__).resolve().parent
MODEL_DIR = SCRIPT_DIR.parent

DATA_DIR = MODEL_DIR / "data"
OUTPUT_DIR = MODEL_DIR / "outputs"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

INPUT_FILE = OUTPUT_DIR / "financial_health_panel_engineered.csv"

#Configuration
TARGET = "default_event_12m"

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

OUTCOME_COLUMNS = [
    TARGET,
]

TRANSACTION_FEATURE_PREFIX = "fe_transaction_"

CATEGORICAL_COLUMNS = [
    "province",
    "industry_sector",
    "legal_entity_type",
]

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

#Header
print("=" * 80)
print("OREY ANALYTICS — FINANCIAL HEALTH SCORING")
print("03 — PREPROCESSING & LEAKAGE CONTROL")
print("=" * 80)

#Load engineered data
print("\nLoading engineered population dataset...")

df = pd.read_csv(INPUT_FILE)

print(f"Rows loaded: {len(df):,}")
print(f"Columns loaded: {len(df.columns):,}")

#Basic validation
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

#Target validation
print("\n" + "=" * 80)
print("TARGET VALIDATION")
print("=" * 80)

print("\nTarget distribution before filtering:")

print(
    df[TARGET]
    .value_counts(dropna=False)
    .sort_index()
)

print("\nFiltering to observations with observable outcomes...")

df = df.loc[
    df["outcome_observable"] == True
].copy()

print(
    f"Observable outcome observations: {len(df):,}"
)

df[TARGET] = pd.to_numeric(
    df[TARGET],
    errors="coerce"
)

if df[TARGET].isna().any():
    raise ValueError(
        "Observable observations contain missing target values."
    )

df = df.loc[
    df[TARGET].isin([0, 1])
].copy()

df[TARGET] = df[TARGET].astype(int)

print("\nFinal target distribution:")

target_counts = (
    df[TARGET]
    .value_counts()
    .sort_index()
)

print(target_counts)

target_rate = df[TARGET].mean()

print(
    f"\nObserved 12-month default rate: "
    f"{target_rate:.2%}"
)

#Model split validation
print("\n" + "=" * 80)
print("MODEL SPLIT VALIDATION")
print("=" * 80)

print(
    df["model_split"]
    .value_counts(dropna=False)
)

VALID_SPLITS = {
    "train",
    "validation",
    "test"
}

invalid_splits = (
    set(df["model_split"].dropna().unique())
    - VALID_SPLITS
)

if invalid_splits:
    raise ValueError(
        f"Unexpected model splits found: {invalid_splits}"
    )

if df["model_split"].isna().any():
    raise ValueError(
        "Missing model_split values detected."
    )

#Business-level split check
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
        "\nThe existing population split may be observation-based."
        "\nThis will be reviewed before final model validation."
    )

#Transaction feature control
print("\n" + "=" * 80)
print("TRANSACTION FEATURE CONTROL")
print("=" * 80)

transaction_columns_present = [
    column
    for column in df.columns
    if column.startswith(
        TRANSACTION_FEATURE_PREFIX
    )
]

print(
    f"Transaction-derived features detected: "
    f"{len(transaction_columns_present)}"
)

for column in transaction_columns_present:
    print(f"  - {column}")

print(
    "\nTransaction-derived features will remain excluded "
    "from the primary population scorecard at this stage."
)

df = df.drop(
    columns=transaction_columns_present,
    errors="ignore"
)

#Remove administrative and outcome variables
print("\nRemoving administrative and outcome variables...")

columns_to_exclude = list(
    dict.fromkeys(
        ADMIN_COLUMNS
        + OUTCOME_COLUMNS
    )
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

#Infinite value control
print("\nChecking for infinite values...")

numeric_columns_all = (
    df_model
    .select_dtypes(include=np.number)
    .columns
)

infinity_counts = {}

for column in numeric_columns_all:

    values = df_model[column].to_numpy(
        dtype=float
    )

    count = np.isinf(values).sum()

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

if infinity_counts:

    df_model[numeric_columns_all] = (
        df_model[numeric_columns_all]
        .replace(
            [np.inf, -np.inf],
            np.nan
        )
    )

#Missingness indicators
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

#Categorical variables
categorical_columns = [
    column
    for column in CATEGORICAL_COLUMNS
    if column in df_model.columns
]

print("\nCategorical variables retained for Stage 04:")

for column in categorical_columns:

    print(
        f"  - {column}: "
        f"{df_model[column].nunique(dropna=True)} "
        f"categories"
    )

#Identify numeric variables
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

    print(
        "\nNon-numeric non-categorical columns "
        "excluded:"
    )

    for column in non_numeric_columns:
        print(
            f"  - {column}: "
            f"{df_model[column].dtype}"
        )

    df_model = df_model.drop(
        columns=non_numeric_columns,
        errors="ignore"
    )

numeric_columns = [
    column
    for column in df_model.columns
    if pd.api.types.is_numeric_dtype(
        df_model[column]
    )
]

print(
    f"\nNumerical variables available: "
    f"{len(numeric_columns)}"
)

#Split data
print("\n" + "=" * 80)
print("TRAIN / VALIDATION / TEST SPLIT")
print("=" * 80)

train_mask = (
    df["model_split"] == "train"
)

validation_mask = (
    df["model_split"] == "validation"
)

test_mask = (
    df["model_split"] == "test"
)

train = df_model.loc[
    train_mask
].copy()

validation = df_model.loc[
    validation_mask
].copy()

test = df_model.loc[
    test_mask
].copy()

print(
    f"Training observations:   {len(train):,}"
)

print(
    f"Validation observations: {len(validation):,}"
)

print(
    f"Test observations:       {len(test):,}"
)

#Targets
y_train = (
    df.loc[
        train_mask,
        TARGET
    ]
    .astype(int)
)

y_validation = (
    df.loc[
        validation_mask,
        TARGET
    ]
    .astype(int)
)

y_test = (
    df.loc[
        test_mask,
        TARGET
    ]
    .astype(int)
)

#Separate predictors
X_train = train.copy()
X_validation = validation.copy()
X_test = test.copy()

#Remove target if present
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

#Numerical imputation
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

X_train_numeric = (
    numeric_imputer
    .fit_transform(
        X_train[numeric_features]
    )
)

X_validation_numeric = (
    numeric_imputer
    .transform(
        X_validation[numeric_features]
    )
)

X_test_numeric = (
    numeric_imputer
    .transform(
        X_test[numeric_features]
    )
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

#Categorical missingness treatment
print("\n" + "=" * 80)
print("CATEGORICAL MISSINGNESS")
print("=" * 80)

X_train_cat = X_train[
    categorical_columns
].copy()

X_validation_cat = X_validation[
    categorical_columns
].copy()

X_test_cat = X_test[
    categorical_columns
].copy()

for column in categorical_columns:

    X_train_cat[column] = (
        X_train_cat[column]
        .fillna("Missing")
        .astype(str)
    )

    X_validation_cat[column] = (
        X_validation_cat[column]
        .fillna("Missing")
        .astype(str)
    )

    X_test_cat[column] = (
        X_test_cat[column]
        .fillna("Missing")
        .astype(str)
    )

print(
    "Categorical missing values converted "
    "to explicit 'Missing' category."
)

#Combine numerical and categorical data
X_train_processed = pd.concat(
    [
        X_train_numeric,
        X_train_cat
    ],
    axis=1
)

X_validation_processed = pd.concat(
    [
        X_validation_numeric,
        X_validation_cat
    ],
    axis=1
)

X_test_processed = pd.concat(
    [
        X_test_numeric,
        X_test_cat
    ],
    axis=1
)

#Align columns
X_validation_processed = (
    X_validation_processed
    .reindex(
        columns=X_train_processed.columns
    )
)

X_test_processed = (
    X_test_processed
    .reindex(
        columns=X_train_processed.columns
    )
)

#Zero-variance filtering
print("\n" + "=" * 80)
print("ZERO-VARIANCE FILTER")
print("=" * 80)

variance_features = [
    column
    for column in X_train_processed.columns
    if column in numeric_features
]

variance_filter = VarianceThreshold(
    threshold=0.0
)

X_train_numeric_filtered = (
    variance_filter.fit_transform(
        X_train_numeric
    )
)

X_validation_numeric_filtered = (
    variance_filter.transform(
        X_validation_numeric
    )
)

X_test_numeric_filtered = (
    variance_filter.transform(
        X_test_numeric
    )
)

kept_numeric_columns = (
    X_train_numeric.columns[
        variance_filter.get_support()
    ]
)

removed_numeric_columns = (
    X_train_numeric.columns[
        ~variance_filter.get_support()
    ]
)

X_train_numeric_filtered = pd.DataFrame(
    X_train_numeric_filtered,
    columns=kept_numeric_columns,
    index=X_train.index
)

X_validation_numeric_filtered = pd.DataFrame(
    X_validation_numeric_filtered,
    columns=kept_numeric_columns,
    index=X_validation.index
)

X_test_numeric_filtered = pd.DataFrame(
    X_test_numeric_filtered,
    columns=kept_numeric_columns,
    index=X_test.index
)

X_train_processed = pd.concat(
    [
        X_train_numeric_filtered,
        X_train_cat
    ],
    axis=1
)

X_validation_processed = pd.concat(
    [
        X_validation_numeric_filtered,
        X_validation_cat
    ],
    axis=1
)

X_test_processed = pd.concat(
    [
        X_test_numeric_filtered,
        X_test_cat
    ],
    axis=1
)

print(
    f"Numerical features before filtering: "
    f"{len(numeric_features)}"
)

print(
    f"Numerical features retained: "
    f"{len(kept_numeric_columns)}"
)

print(
    f"Numerical features removed: "
    f"{len(removed_numeric_columns)}"
)

if len(removed_numeric_columns) > 0:

    print("\nRemoved numerical features:")

    for column in removed_numeric_columns:
        print(f"  - {column}")

#Final validation
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

print("\nRemaining missing values:")

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

print("\nRemaining infinite values:")

print(
    f"Training:   "
    f"{np.isinf(
        X_train_processed.select_dtypes(
            include=np.number
        ).to_numpy()
    ).sum():,}"
)

print(
    f"Validation: "
    f"{np.isinf(
        X_validation_processed.select_dtypes(
            include=np.number
        ).to_numpy()
    ).sum():,}"
)

print(
    f"Test:       "
    f"{np.isinf(
        X_test_processed.select_dtypes(
            include=np.number
        ).to_numpy()
    ).sum():,}"
)

#WoE readiness validation
print("\n" + "=" * 80)
print("WOE READINESS CHECK")
print("=" * 80)

print(
    f"Numerical predictors ready for Stage 04: "
    f"{len(kept_numeric_columns)}"
)

print(
    f"Categorical predictors ready for Stage 04: "
    f"{len(categorical_columns)}"
)

print(
    "\nCategorical variables have NOT been one-hot encoded."
)

print(
    "They remain available for categorical grouping "
    "during WoE and Information Value analysis."
)

#Save model-ready datasets
print("\n" + "=" * 80)
print("SAVING PREPROCESSED DATASETS")
print("=" * 80)

train_output = X_train_processed.copy()
train_output[TARGET] = y_train.values

validation_output = X_validation_processed.copy()
validation_output[TARGET] = y_validation.values

test_output = X_test_processed.copy()
test_output[TARGET] = y_test.values

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

#Save feature list
feature_list = pd.DataFrame(
    {
        "feature": list(
            X_train_processed.columns
        ),
        "feature_type": [
            (
                "categorical"
                if column in categorical_columns
                else "numeric"
            )
            for column in X_train_processed.columns
        ]
    }
)

feature_list.to_csv(
    OUTPUT_DIR / "preprocessed_feature_list.csv",
    index=False
)

#Save removed feature list
removed_feature_list = pd.DataFrame(
    {
        "feature": list(
            removed_numeric_columns
        ),
        "reason": "zero variance in training data"
    }
)

removed_feature_list.to_csv(
    OUTPUT_DIR / "removed_low_variance_features.csv",
    index=False
)

#Save preprocessing metadata
metadata = {
    "stage": "03_preprocessing",
    "target": TARGET,
    "input_file": str(INPUT_FILE),
    "original_rows": int(
        len(pd.read_csv(INPUT_FILE))
    ),
    "observable_rows": int(len(df)),
    "train_rows": int(
        len(X_train_processed)
    ),
    "validation_rows": int(
        len(X_validation_processed)
    ),
    "test_rows": int(
        len(X_test_processed)
    ),
    "train_default_rate": float(
        y_train.mean()
    ),
    "validation_default_rate": float(
        y_validation.mean()
    ),
    "test_default_rate": float(
        y_test.mean()
    ),
    "transaction_features_excluded": (
        transaction_columns_present
    ),
    "missingness_indicators_created": (
        created_indicators
    ),
    "categorical_columns": (
        categorical_columns
    ),
    "categorical_encoding": (
        "Not one-hot encoded; retained for WoE treatment."
    ),
    "numeric_features_before_filter": (
        len(numeric_features)
    ),
    "numeric_features_after_filter": (
        len(kept_numeric_columns)
    ),
    "features_removed_zero_variance": (
        len(removed_numeric_columns)
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
        "Numerical imputation and zero-variance "
        "filtering were fitted on training data only."
    ),
    "woe_ready": True
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

#Completion
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

print("\nStage 03 status:")
print("PASS — preprocessing completed successfully.")

print("\nNext stage:")
print("04 — WoE, binning and Information Value")