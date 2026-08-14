"""
Orey Analytics
Financial Health Scoring - WoE, Binning & Information Value

Purpose: Transform model-ready predictors into credit-risk WoE features and
evaluate their predictive information value.

Key principles:
    1. Binning rules are learned from TRAINING data only.
    2. WoE and Information Value are calculated using TRAINING outcomes only.
    3. Validation and test data use training-derived binning and WoE mappings.
    4. Binary predictors are treated as discrete risk groups.
    5. Continuous predictors are transformed using quantile-based bins.
    6. Missing and unseen values are handled explicitly.
    7. Zero event/non-event bins use a smoothing adjustment.
    8. Target information is never used to construct validation/test features.
"""

# IMPORTS
from pathlib import Path
import json
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# PROJECT PATHS
SCRIPT_DIR = Path(__file__).resolve().parent
MODEL_DIR = SCRIPT_DIR.parent

DATA_DIR = MODEL_DIR / "data"
OUTPUT_DIR = MODEL_DIR / "outputs"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TRAIN_FILE = OUTPUT_DIR / "model_train_preprocessed.csv"
VALIDATION_FILE = OUTPUT_DIR / "model_validation_preprocessed.csv"
TEST_FILE = OUTPUT_DIR / "model_test_preprocessed.csv"

# CONFIGURATION
TARGET = "default_event_12m"

N_BINS = 10
MIN_BIN_SIZE = 0.01
SMOOTHING = 0.5

# HEADER
print("=" * 80)
print("OREY ANALYTICS — FINANCIAL HEALTH SCORING")
print("04 — WoE, BINNING & INFORMATION VALUE")
print("=" * 80)

# LOAD PREPROCESSED DATA
print("\nLoading preprocessed datasets...")

train = pd.read_csv(TRAIN_FILE)
validation = pd.read_csv(VALIDATION_FILE)
test = pd.read_csv(TEST_FILE)

print(f"Training observations:   {len(train):,}")
print(f"Validation observations: {len(validation):,}")
print(f"Test observations:       {len(test):,}")

# BASIC VALIDATION
required_files = [
    TRAIN_FILE,
    VALIDATION_FILE,
    TEST_FILE,
]

for file in required_files:

    if not file.exists():

        raise FileNotFoundError(
            f"Required input file not found: {file}"
        )

required_columns = [
    TARGET,
]

for column in required_columns:

    if column not in train.columns:

        raise ValueError(
            f"Required column missing from training data: {column}"
        )

if TARGET not in validation.columns:
    raise ValueError(
        f"Target column missing from validation data: {TARGET}"
    )

if TARGET not in test.columns:
    raise ValueError(
        f"Target column missing from test data: {TARGET}"
    )

# TARGET VALIDATION
print("\n" + "=" * 80)
print("TARGET VALIDATION")
print("=" * 80)

for name, dataset in [
    ("Training", train),
    ("Validation", validation),
    ("Test", test),
]:

    invalid_target = ~dataset[TARGET].isin([0, 1])

    if invalid_target.any():

        raise ValueError(
            f"{name} dataset contains invalid target values."
        )

    print(
        f"{name} default rate: "
        f"{dataset[TARGET].mean():.2%}"
    )

# IDENTIFY FEATURES
features = [
    column
    for column in train.columns
    if column != TARGET
]

print(
    f"\nPredictor features available: "
    f"{len(features)}"
)

# CHECK TRAIN / VALIDATION / TEST ALIGNMENT
print("\nChecking feature alignment...")

validation_features = [
    column
    for column in validation.columns
    if column != TARGET
]

test_features = [
    column
    for column in test.columns
    if column != TARGET
]

if set(features) != set(validation_features):

    raise ValueError(
        "Training and validation predictors do not match."
    )

if set(features) != set(test_features):

    raise ValueError(
        "Training and test predictors do not match."
    )

print("Feature alignment confirmed.")

# IDENTIFY BINARY FEATURES
print("\n" + "=" * 80)
print("FEATURE TYPE IDENTIFICATION")
print("=" * 80)

binary_features = []
continuous_features = []

for feature in features:

    unique_values = (
        train[feature]
        .dropna()
        .unique()
    )

    if len(unique_values) <= 2:

        binary_features.append(feature)

    else:

        continuous_features.append(feature)

print(
    f"Binary/discrete features: "
    f"{len(binary_features)}"
)

print(
    f"Continuous features: "
    f"{len(continuous_features)}"
)

# CREATE WOE FUNCTION
def calculate_woe(
    grouped_data,
    target_column=TARGET,
    smoothing=SMOOTHING
):

    grouped_data = grouped_data.copy()

    total_events = (
        grouped_data["event_count"]
        .sum()
    )

    total_non_events = (
        grouped_data["non_event_count"]
        .sum()
    )

    number_of_bins = len(grouped_data)

    grouped_data["event_rate_distribution"] = (
        (
            grouped_data["event_count"]
            + smoothing
        )
        /
        (
            total_events
            + smoothing * number_of_bins
        )
    )

    grouped_data["non_event_rate_distribution"] = (
        (
            grouped_data["non_event_count"]
            + smoothing
        )
        /
        (
            total_non_events
            + smoothing * number_of_bins
        )
    )

    grouped_data["woe"] = np.log(
        grouped_data["non_event_rate_distribution"]
        /
        grouped_data["event_rate_distribution"]
    )

    grouped_data["iv"] = (
        grouped_data["non_event_rate_distribution"]
        -
        grouped_data["event_rate_distribution"]
    ) * grouped_data["woe"]

    return grouped_data

# STORAGE
woe_mappings = {}
iv_records = []
binning_metadata = {}

# PROCESS FEATURES
print("\n" + "=" * 80)
print("BINNING & WoE CALCULATION")
print("=" * 80)

for feature_number, feature in enumerate(features, start=1):

    if feature_number % 10 == 0 or feature_number == 1:

        print(
            f"Processing feature "
            f"{feature_number}/{len(features)}: "
            f"{feature}"
        )

    train_feature = train[feature].copy()
    train_target = train[TARGET]

    # BINARY FEATURES
    if feature in binary_features:

        bin_column = (
            train_feature
            .fillna(-999999)
            .astype(str)
        )

        grouped = (
            pd.DataFrame({
                "bin": bin_column,
                TARGET: train_target,
            })
            .groupby("bin", dropna=False)[TARGET]
            .agg(
                event_count="sum",
                total_count="count",
            )
            .reset_index()
        )

        grouped["non_event_count"] = (
            grouped["total_count"]
            -
            grouped["event_count"]
        )

        grouped = calculate_woe(grouped)

        feature_iv = grouped["iv"].sum()

        mapping = dict(
            zip(
                grouped["bin"].astype(str),
                grouped["woe"]
            )
        )

        woe_mappings[feature] = mapping

        binning_metadata[feature] = {
            "type": "binary_or_discrete",
            "bins": list(mapping.keys()),
        }

    # CONTINUOUS FEATURES
    else:

        non_missing = train_feature.dropna()

        if non_missing.nunique() <= 1:

            bin_column = (
                train_feature
                .fillna(-999999)
                .astype(str)
            )

            grouped = (
                pd.DataFrame({
                    "bin": bin_column,
                    TARGET: train_target,
                })
                .groupby("bin", dropna=False)[TARGET]
                .agg(
                    event_count="sum",
                    total_count="count",
                )
                .reset_index()
            )

            grouped["non_event_count"] = (
                grouped["total_count"]
                -
                grouped["event_count"]
            )

            grouped = calculate_woe(grouped)

            feature_iv = grouped["iv"].sum()

            mapping = dict(
                zip(
                    grouped["bin"].astype(str),
                    grouped["woe"]
                )
            )

            woe_mappings[feature] = mapping

            binning_metadata[feature] = {
                "type": "constant_or_near_constant",
                "bins": list(mapping.keys()),
            }

        else:

            try:

                quantile_bins = pd.qcut(
                    non_missing,
                    q=N_BINS,
                    duplicates="drop"
                )

                bin_edges = (
                    quantile_bins
                    .cat
                    .categories
                )

                train_bins = pd.cut(
                    train_feature,
                    bins=[
                        -np.inf
                    ]
                    +
                    [
                        float(interval.right)
                        for interval in bin_edges
                    ],
                    include_lowest=True
                )

                train_bins = train_bins.astype(object)

                train_bins[
                    train_feature.isna()
                ] = "MISSING"

                train_bins = train_bins.astype(str)

                grouped = (
                    pd.DataFrame({
                        "bin": train_bins,
                        TARGET: train_target,
                    })
                    .groupby("bin", dropna=False)[TARGET]
                    .agg(
                        event_count="sum",
                        total_count="count",
                    )
                    .reset_index()
                )

                grouped["non_event_count"] = (
                    grouped["total_count"]
                    -
                    grouped["event_count"]
                )

                grouped = calculate_woe(grouped)

                feature_iv = grouped["iv"].sum()

                mapping = dict(
                    zip(
                        grouped["bin"].astype(str),
                        grouped["woe"]
                    )
                )

                woe_mappings[feature] = mapping

                binning_metadata[feature] = {
                    "type": "quantile",
                    "bin_edges": [
                        -np.inf
                    ]
                    +
                    [
                        float(interval.right)
                        for interval in bin_edges
                    ],
                    "bins": list(mapping.keys()),
                }

            except Exception:

                bin_column = (
                    train_feature
                    .fillna(-999999)
                    .astype(str)
                )

                grouped = (
                    pd.DataFrame({
                        "bin": bin_column,
                        TARGET: train_target,
                    })
                    .groupby("bin", dropna=False)[TARGET]
                    .agg(
                        event_count="sum",
                        total_count="count",
                    )
                    .reset_index()
                )

                grouped["non_event_count"] = (
                    grouped["total_count"]
                    -
                    grouped["event_count"]
                )

                grouped = calculate_woe(grouped)

                feature_iv = grouped["iv"].sum()

                mapping = dict(
                    zip(
                        grouped["bin"].astype(str),
                        grouped["woe"]
                    )
                )

                woe_mappings[feature] = mapping

                binning_metadata[feature] = {
                    "type": "fallback_discrete",
                    "bins": list(mapping.keys()),
                }

    iv_records.append({
        "feature": feature,
        "information_value": float(feature_iv),
        "feature_type": binning_metadata[feature]["type"],
    })

# IV SUMMARY
print("\n" + "=" * 80)
print("INFORMATION VALUE SUMMARY")
print("=" * 80)

iv_summary = pd.DataFrame(
    iv_records
).sort_values(
    "information_value",
    ascending=False
)

iv_summary["information_value"] = (
    iv_summary["information_value"]
    .round(6)
)

print(
    "\nTop 20 features by Information Value:"
)

print(
    iv_summary
    .head(20)
    .to_string(index=False)
)

# IV INTERPRETATION
def interpret_iv(iv):

    if iv < 0.02:
        return "Very weak"

    if iv < 0.10:
        return "Weak"

    if iv < 0.30:
        return "Medium"

    if iv < 0.50:
        return "Strong"

    return "Very strong"

iv_summary["iv_strength"] = (
    iv_summary["information_value"]
    .apply(interpret_iv)
)

print("\nIV strength distribution:")

print(
    iv_summary["iv_strength"]
    .value_counts()
)

# TRANSFORM DATASET USING TRAINING MAPPINGS
print("\n" + "=" * 80)
print("APPLYING TRAINING-DERIVED WoE")
print("=" * 80)

def transform_dataset(
    dataset,
    mappings,
    metadata
):

    transformed = pd.DataFrame(
        index=dataset.index
    )

    for feature in features:

        values = dataset[feature]

        feature_metadata = metadata[feature]
        feature_type = feature_metadata["type"]

        if feature_type == "quantile":

            bin_edges = feature_metadata["bin_edges"]

            bins = pd.cut(
                values,
                bins=bin_edges,
                include_lowest=True
            )

            bins = bins.astype(object)

            bins[
                values.isna()
            ] = "MISSING"

            bins = bins.astype(str)

        else:

            bins = (
                values
                .fillna(-999999)
                .astype(str)
            )

        mapping = mappings[feature]

        transformed_values = (
            bins
            .map(mapping)
        )

        transformed_values = (
            transformed_values
            .fillna(0.0)
        )

        transformed[
            f"woe_{feature}"
        ] = transformed_values.astype(float)

    return transformed

X_train_woe = transform_dataset(
    train,
    woe_mappings,
    binning_metadata
)

X_validation_woe = transform_dataset(
    validation,
    woe_mappings,
    binning_metadata
)

X_test_woe = transform_dataset(
    test,
    woe_mappings,
    binning_metadata
)

# ADD TARGET
X_train_woe[TARGET] = train[TARGET].astype(int)
X_validation_woe[TARGET] = validation[TARGET].astype(int)
X_test_woe[TARGET] = test[TARGET].astype(int)

print(
    f"Training WoE shape:   "
    f"{X_train_woe.shape}"
)

print(
    f"Validation WoE shape: "
    f"{X_validation_woe.shape}"
)

print(
    f"Test WoE shape:       "
    f"{X_test_woe.shape}"
)

# FINAL VALIDATION
print("\n" + "=" * 80)
print("FINAL WoE VALIDATION")
print("=" * 80)

for name, dataset in [
    ("Training", X_train_woe),
    ("Validation", X_validation_woe),
    ("Test", X_test_woe),
]:

    missing_values = (
        dataset
        .drop(columns=[TARGET])
        .isna()
        .sum()
        .sum()
    )

    infinite_values = np.isinf(
        dataset
        .drop(columns=[TARGET])
        .to_numpy()
    ).sum()

    print(
        f"{name} missing values: "
        f"{missing_values:,}"
    )

    print(
        f"{name} infinite values: "
        f"{infinite_values:,}"
    )

# SAVE WoE DATASETS
print("\n" + "=" * 80)
print("SAVING WoE DATASETS")
print("=" * 80)

X_train_woe.to_csv(
    OUTPUT_DIR / "model_train_woe.csv",
    index=False
)

X_validation_woe.to_csv(
    OUTPUT_DIR / "model_validation_woe.csv",
    index=False
)

X_test_woe.to_csv(
    OUTPUT_DIR / "model_test_woe.csv",
    index=False
)

# SAVE IV SUMMARY
iv_summary.to_csv(
    OUTPUT_DIR / "feature_iv_summary.csv",
    index=False
)

# SAVE BINNING METADATA
with open(
    OUTPUT_DIR / "woe_binning_definitions.json",
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        binning_metadata,
        file,
        indent=4
    )

# SAVE WOE MAPPINGS
with open(
    OUTPUT_DIR / "woe_mappings.json",
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        woe_mappings,
        file,
        indent=4
    )

# SAVE METADATA
metadata = {
    "target": TARGET,

    "train_file": str(TRAIN_FILE),
    "validation_file": str(VALIDATION_FILE),
    "test_file": str(TEST_FILE),

    "train_rows": int(len(train)),
    "validation_rows": int(len(validation)),
    "test_rows": int(len(test)),

    "predictor_features": int(len(features)),
    "binary_features": int(len(binary_features)),
    "continuous_features": int(len(continuous_features)),

    "number_of_bins": int(N_BINS),

    "minimum_bin_size": float(MIN_BIN_SIZE),

    "smoothing": float(SMOOTHING),

    "woe_training_only": True,

    "validation_and_test_use_training_mappings": True,

    "features_with_iv_below_0_02": int(
        (
            iv_summary["information_value"]
            < 0.02
        ).sum()
    ),

    "features_with_iv_0_02_to_0_10": int(
        (
            (
                iv_summary["information_value"]
                >= 0.02
            )
            &
            (
                iv_summary["information_value"]
                < 0.10
            )
        ).sum()
    ),

    "features_with_iv_0_10_to_0_30": int(
        (
            (
                iv_summary["information_value"]
                >= 0.10
            )
            &
            (
                iv_summary["information_value"]
                < 0.30
            )
        ).sum()
    ),

    "features_with_iv_above_0_30": int(
        (
            iv_summary["information_value"]
            >= 0.30
        ).sum()
    ),

    "preprocessing_rule": (
        "Binning and WoE mappings were learned from training "
        "data only and applied unchanged to validation and test."
    )
}

with open(
    OUTPUT_DIR / "woe_metadata.json",
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
print("WoE, BINNING & INFORMATION VALUE COMPLETE")
print("=" * 80)

print("\nOutputs saved to:")

print(OUTPUT_DIR)

print("\nGenerated files:")

print("  - model_train_woe.csv")
print("  - model_validation_woe.csv")
print("  - model_test_woe.csv")
print("  - feature_iv_summary.csv")
print("  - woe_binning_definitions.json")
print("  - woe_mappings.json")
print("  - woe_metadata.json")

print("\nSource datasets were not modified.")

print("\nNext stage:")
print("05 — Feature selection and scorecard modelling")