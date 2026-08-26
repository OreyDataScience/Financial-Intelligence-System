"""
Orey Analytics
Financial Health Scoring — Population Model

Stage 04 — WoE, Binning & Information Value

Purpose:
    Transform model-ready predictors into credit-risk WoE features and
    evaluate their predictive Information Value (IV).

Key principles:
    1. Binning rules are learned from TRAINING data only.
    2. WoE and Information Value are calculated from TRAINING outcomes only.
    3. Validation and test data use unchanged training-derived mappings.
    4. Numerical variables use quantile-based bins.
    5. Categorical variables are treated as discrete risk groups.
    6. Missing values are explicitly represented.
    7. Zero event/non-event bins use smoothing.
    8. Unseen validation/test categories receive neutral WoE.
    9. Target information is never used to construct validation/test bins.
   10. Very high IV values are flagged for leakage investigation.
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

# Minimum proportion of training observations required in a bin.
MIN_BIN_SIZE = 0.01

# Smoothing applied to event/non-event counts.
SMOOTHING = 0.5

# IV thresholds.
VERY_HIGH_IV_THRESHOLD = 0.50
HIGH_IV_THRESHOLD = 0.30


# HEADER

print("=" * 80)
print("OREY ANALYTICS — FINANCIAL HEALTH SCORING")
print("04 — WoE, BINNING & INFORMATION VALUE")
print("=" * 80)


# LOAD PREPROCESSED DATA

print("\nLoading preprocessed datasets...")

for file in [
    TRAIN_FILE,
    VALIDATION_FILE,
    TEST_FILE
]:
    if not file.exists():
        raise FileNotFoundError(
            f"Required input file not found:\n{file}"
        )

train = pd.read_csv(TRAIN_FILE)
validation = pd.read_csv(VALIDATION_FILE)
test = pd.read_csv(TEST_FILE)

print(f"Training observations:   {len(train):,}")
print(f"Validation observations: {len(validation):,}")
print(f"Test observations:       {len(test):,}")


# BASIC VALIDATION

print("\nChecking required columns...")

if TARGET not in train.columns:
    raise ValueError(
        f"Target column missing from training data: {TARGET}"
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
        invalid_values = (
            dataset.loc[
                invalid_target,
                TARGET
            ]
            .unique()
            .tolist()
        )

        raise ValueError(
            f"{name} dataset contains invalid target values: "
            f"{invalid_values}"
        )

    print(
        f"{name} default rate: "
        f"{dataset[TARGET].mean():.2%}"
    )


# IDENTIFY PREDICTORS

features = [
    column
    for column in train.columns
    if column != TARGET
]

print(
    f"\nPredictor features available: "
    f"{len(features)}"
)


# FEATURE ALIGNMENT

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


# IDENTIFY FEATURE TYPES

print("\n" + "=" * 80)
print("FEATURE TYPE IDENTIFICATION")
print("=" * 80)

categorical_features = [
    "province",
    "industry_sector",
    "legal_entity_type"
]

categorical_features = [
    feature
    for feature in categorical_features
    if feature in features
]

numerical_features = [
    feature
    for feature in features
    if feature not in categorical_features
]

binary_features = []
continuous_features = []

for feature in numerical_features:

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
    f"Categorical features:      "
    f"{len(categorical_features)}"
)

for feature in categorical_features:
    print(
        f"  - {feature}: "
        f"{train[feature].nunique(dropna=True)} categories"
    )

print(
    f"\nBinary numerical features: "
    f"{len(binary_features)}"
)

print(
    f"Continuous numerical features: "
    f"{len(continuous_features)}"
)


# WoE CALCULATION

def calculate_woe(
    grouped_data,
    smoothing=SMOOTHING
):
    """
    Calculate WoE and Information Value using training data only.

    WoE convention:

        WoE = ln(non-event distribution / event distribution)

    Positive WoE:
        Lower observed default risk.

    Negative WoE:
        Higher observed default risk.
    """

    grouped_data = grouped_data.copy()

    total_events = grouped_data["event_count"].sum()
    total_non_events = grouped_data["non_event_count"].sum()

    number_of_bins = len(grouped_data)

    if total_events == 0:
        raise ValueError(
            "Training data contains zero events."
        )

    if total_non_events == 0:
        raise ValueError(
            "Training data contains zero non-events."
        )

    grouped_data["event_distribution"] = (
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

    grouped_data["non_event_distribution"] = (
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
        grouped_data["non_event_distribution"]
        /
        grouped_data["event_distribution"]
    )

    grouped_data["iv"] = (
        grouped_data["non_event_distribution"]
        -
        grouped_data["event_distribution"]
    ) * grouped_data["woe"]

    grouped_data["default_rate"] = (
        grouped_data["event_count"]
        /
        grouped_data["total_count"]
    )

    grouped_data["population_pct"] = (
        grouped_data["total_count"]
        /
        grouped_data["total_count"].sum()
    )

    return grouped_data


# HELPER — BUILD DISCRETE GROUPS

def build_discrete_groups(
    values,
    target
):
    """
    Build event/non-event statistics for categorical or binary variables.
    """

    clean_values = values.copy()

    clean_values = clean_values.astype(object)

    clean_values = clean_values.where(
        clean_values.notna(),
        "MISSING"
    )

    clean_values = clean_values.astype(str)

    grouped = (
        pd.DataFrame(
            {
                "bin": clean_values,
                TARGET: target
            }
        )
        .groupby(
            "bin",
            dropna=False
        )[TARGET]
        .agg(
            event_count="sum",
            total_count="count"
        )
        .reset_index()
    )

    grouped["non_event_count"] = (
        grouped["total_count"]
        -
        grouped["event_count"]
    )

    return grouped


# STORAGE

woe_mappings = {}
binning_metadata = {}

iv_records = []
bin_records = []


# PROCESS FEATURES

print("\n" + "=" * 80)
print("BINNING & WoE CALCULATION")
print("=" * 80)

total_features = len(features)

for feature_number, feature in enumerate(
    features,
    start=1
):

    if (
        feature_number == 1
        or feature_number % 10 == 0
        or feature_number == total_features
    ):
        print(
            f"Processing feature "
            f"{feature_number}/{total_features}: "
            f"{feature}"
        )

    train_feature = train[feature].copy()
    train_target = train[TARGET].astype(int)

    # CATEGORICAL FEATURES

    if feature in categorical_features:

        grouped = build_discrete_groups(
            train_feature,
            train_target
        )

        grouped = calculate_woe(grouped)

        mapping = dict(
            zip(
                grouped["bin"].astype(str),
                grouped["woe"].astype(float)
            )
        )

        feature_iv = grouped["iv"].sum()

        woe_mappings[feature] = mapping

        binning_metadata[feature] = {
            "type": "categorical",
            "bins": list(mapping.keys())
        }

    # BINARY NUMERICAL FEATURES

    elif feature in binary_features:

        grouped = build_discrete_groups(
            train_feature,
            train_target
        )

        grouped = calculate_woe(grouped)

        mapping = dict(
            zip(
                grouped["bin"].astype(str),
                grouped["woe"].astype(float)
            )
        )

        feature_iv = grouped["iv"].sum()

        woe_mappings[feature] = mapping

        binning_metadata[feature] = {
            "type": "binary",
            "bins": list(mapping.keys())
        }

    # CONTINUOUS NUMERICAL FEATURES

    else:

        non_missing = train_feature.dropna()

        # Constant / near-constant feature

        if non_missing.nunique() <= 1:

            grouped = build_discrete_groups(
                train_feature,
                train_target
            )

            grouped = calculate_woe(grouped)

            mapping = dict(
                zip(
                    grouped["bin"].astype(str),
                    grouped["woe"].astype(float)
                )
            )

            feature_iv = grouped["iv"].sum()

            woe_mappings[feature] = mapping

            binning_metadata[feature] = {
                "type": "constant",
                "bins": list(mapping.keys())
            }

        # Quantile binning

        else:

            try:

                # Generate training-only quantile bins.
                quantile_result = pd.qcut(
                    non_missing,
                    q=N_BINS,
                    duplicates="drop"
                )

                intervals = (
                    quantile_result
                    .cat
                    .categories
                )

                if len(intervals) < 2:
                    raise ValueError(
                        "Insufficient unique quantile bins."
                    )

                # Extract the right edges from training bins.
                bin_edges = [
                    -np.inf
                ]

                for interval in intervals:
                    bin_edges.append(
                        float(interval.right)
                    )

                # Ensure unique edges.
                bin_edges = list(
                    dict.fromkeys(bin_edges)
                )

                if len(bin_edges) < 3:
                    raise ValueError(
                        "Insufficient unique bin edges."
                    )

                train_bins = pd.cut(
                    train_feature,
                    bins=bin_edges,
                    include_lowest=True
                )

                train_bins = train_bins.astype(object)

                train_bins[
                    train_feature.isna()
                ] = "MISSING"

                train_bins = train_bins.astype(str)

                grouped = (
                    pd.DataFrame(
                        {
                            "bin": train_bins,
                            TARGET: train_target
                        }
                    )
                    .groupby(
                        "bin",
                        dropna=False
                    )[TARGET]
                    .agg(
                        event_count="sum",
                        total_count="count"
                    )
                    .reset_index()
                )

                grouped["non_event_count"] = (
                    grouped["total_count"]
                    -
                    grouped["event_count"]
                )

                # Minimum bin-size check

                grouped["population_pct"] = (
                    grouped["total_count"]
                    /
                    grouped["total_count"].sum()
                )

                small_bins = grouped[
                    (
                        grouped["population_pct"]
                        < MIN_BIN_SIZE
                    )
                    &
                    (
                        grouped["bin"]
                        != "MISSING"
                    )
                ]

                # Retain small bins but flag them for review.
                small_bin_count = len(small_bins)

                grouped = calculate_woe(
                    grouped
                )

                mapping = dict(
                    zip(
                        grouped["bin"].astype(str),
                        grouped["woe"].astype(float)
                    )
                )

                feature_iv = grouped["iv"].sum()

                woe_mappings[feature] = mapping

                binning_metadata[feature] = {
                    "type": "quantile",
                    "bin_edges": bin_edges,
                    "bins": list(mapping.keys()),
                    "small_bins_below_minimum": int(
                        small_bin_count
                    )
                }

            except Exception as error:

                print(
                    f"  Warning: quantile binning failed "
                    f"for {feature}. "
                    f"Using discrete fallback."
                )

                print(
                    f"  Reason: {error}"
                )

                grouped = build_discrete_groups(
                    train_feature,
                    train_target
                )

                grouped = calculate_woe(
                    grouped
                )

                mapping = dict(
                    zip(
                        grouped["bin"].astype(str),
                        grouped["woe"].astype(float)
                    )
                )

                feature_iv = grouped["iv"].sum()

                woe_mappings[feature] = mapping

                binning_metadata[feature] = {
                    "type": "discrete_fallback",
                    "bins": list(mapping.keys())
                }

    # STORE IV

    iv_records.append(
        {
            "feature": feature,
            "information_value": float(
                feature_iv
            ),
            "feature_type": (
                binning_metadata[feature]["type"]
            )
        }
    )

    # STORE BIN AUDIT INFORMATION

    for bin_name, woe_value in (
        woe_mappings[feature].items()
    ):

        bin_records.append(
            {
                "feature": feature,
                "bin": bin_name,
                "woe": float(woe_value),
                "information_value": float(
                    feature_iv
                )
            }
        )


# IV SUMMARY

print("\n" + "=" * 80)
print("INFORMATION VALUE SUMMARY")
print("=" * 80)

iv_summary = (
    pd.DataFrame(iv_records)
    .sort_values(
        "information_value",
        ascending=False
    )
    .reset_index(drop=True)
)

iv_summary["information_value"] = (
    iv_summary["information_value"]
    .round(6)
)


# IV INTERPRETATION

def interpret_iv(iv):

    if iv < 0.02:
        return "Very weak"

    elif iv < 0.10:
        return "Weak"

    elif iv < 0.30:
        return "Medium"

    elif iv < 0.50:
        return "Strong"

    else:
        return "Very strong"


iv_summary["iv_strength"] = (
    iv_summary["information_value"]
    .apply(interpret_iv)
)


# IV LEAKAGE FLAGS

iv_summary["high_iv_flag"] = (
    iv_summary["information_value"]
    >= HIGH_IV_THRESHOLD
)

iv_summary["very_high_iv_flag"] = (
    iv_summary["information_value"]
    >= VERY_HIGH_IV_THRESHOLD
)


print("\nTop 20 features by Information Value:")

print(
    iv_summary
    .head(20)
    .to_string(index=False)
)

print("\nIV strength distribution:")

print(
    iv_summary["iv_strength"]
    .value_counts()
)

high_iv_count = int(
    iv_summary["high_iv_flag"].sum()
)

very_high_iv_count = int(
    iv_summary["very_high_iv_flag"].sum()
)

print(
    f"\nFeatures with IV >= {HIGH_IV_THRESHOLD}: "
    f"{high_iv_count}"
)

print(
    f"Features with IV >= {VERY_HIGH_IV_THRESHOLD}: "
    f"{very_high_iv_count}"
)

if very_high_iv_count > 0:

    print("\nWARNING:")

    print(
        "Very high IV features detected."
    )

    print(
        "These features require leakage review before "
        "scorecard modelling."
    )


# TRANSFORM DATASETS USING TRAINING MAPPINGS

print("\n" + "=" * 80)
print("APPLYING TRAINING-DERIVED WoE")
print("=" * 80)


def transform_dataset(
    dataset,
    mappings,
    metadata,
    feature_list
):
    """
    Apply training-derived binning and WoE mappings.

    No target information is used here.
    """

    transformed = pd.DataFrame(
        index=dataset.index
    )

    for feature in feature_list:

        values = dataset[feature]

        feature_metadata = metadata[feature]

        feature_type = feature_metadata["type"]

        # Quantile numerical feature

        if feature_type == "quantile":

            bin_edges = (
                feature_metadata["bin_edges"]
            )

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

        # Categorical / binary / fallback

        else:

            bins = (
                values
                .where(
                    values.notna(),
                    "MISSING"
                )
                .astype(str)
            )

        mapping = mappings[feature]

        transformed_values = (
            bins.map(mapping)
        )

        # Unseen validation/test categories receive neutral WoE.
        unseen_count = int(
            transformed_values.isna().sum()
        )

        if unseen_count > 0:

            print(
                f"  {feature}: "
                f"{unseen_count:,} unseen values "
                f"assigned neutral WoE."
            )

        transformed_values = (
            transformed_values
            .fillna(0.0)
        )

        transformed[
            f"woe_{feature}"
        ] = transformed_values.astype(float)

    return transformed


# APPLY TRANSFORMATION

X_train_woe = transform_dataset(
    train,
    woe_mappings,
    binning_metadata,
    features
)

X_validation_woe = transform_dataset(
    validation,
    woe_mappings,
    binning_metadata,
    features
)

X_test_woe = transform_dataset(
    test,
    woe_mappings,
    binning_metadata,
    features
)


# ADD TARGET

X_train_woe[TARGET] = (
    train[TARGET]
    .astype(int)
)

X_validation_woe[TARGET] = (
    validation[TARGET]
    .astype(int)
)

X_test_woe[TARGET] = (
    test[TARGET]
    .astype(int)
)


print(
    f"\nTraining WoE shape:   "
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


# FINAL WoE VALIDATION

print("\n" + "=" * 80)
print("FINAL WoE VALIDATION")
print("=" * 80)

for name, dataset in [
    ("Training", X_train_woe),
    ("Validation", X_validation_woe),
    ("Test", X_test_woe),
]:

    predictors = dataset.drop(
        columns=[TARGET]
    )

    missing_values = int(
        predictors.isna()
        .sum()
        .sum()
    )

    infinite_values = int(
        np.isinf(
            predictors.to_numpy(
                dtype=float
            )
        )
        .sum()
    )

    print(
        f"{name} missing values: "
        f"{missing_values:,}"
    )

    print(
        f"{name} infinite values: "
        f"{infinite_values:,}"
    )

    if missing_values > 0:
        raise ValueError(
            f"{name} WoE dataset contains "
            f"missing values."
        )

    if infinite_values > 0:
        raise ValueError(
            f"{name} WoE dataset contains "
            f"infinite values."
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


# SAVE BIN-LEVEL AUDIT

bin_audit = pd.DataFrame(
    bin_records
)

bin_audit.to_csv(
    OUTPUT_DIR / "woe_bin_audit.csv",
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


# SAVE WoE MAPPINGS

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

    "stage": "04",

    "stage_name": (
        "WoE, Binning & Information Value"
    ),

    "target": TARGET,

    "train_file": str(
        TRAIN_FILE
    ),

    "validation_file": str(
        VALIDATION_FILE
    ),

    "test_file": str(
        TEST_FILE
    ),

    "train_rows": int(
        len(train)
    ),

    "validation_rows": int(
        len(validation)
    ),

    "test_rows": int(
        len(test)
    ),

    "predictor_features": int(
        len(features)
    ),

    "categorical_features": int(
        len(categorical_features)
    ),

    "binary_features": int(
        len(binary_features)
    ),

    "continuous_features": int(
        len(continuous_features)
    ),

    "number_of_bins": int(
        N_BINS
    ),

    "minimum_bin_size": float(
        MIN_BIN_SIZE
    ),

    "smoothing": float(
        SMOOTHING
    ),

    "woe_convention": (
        "WoE = ln(non_event_distribution / "
        "event_distribution)"
    ),

    "woe_training_only": True,

    "validation_and_test_use_training_mappings": True,

    "unseen_validation_test_values_use_neutral_woe": True,

    "features_with_iv_below_0_02": int(
        (
            iv_summary[
                "information_value"
            ]
            < 0.02
        ).sum()
    ),

    "features_with_iv_0_02_to_0_10": int(
        (
            (
                iv_summary[
                    "information_value"
                ]
                >= 0.02
            )
            &
            (
                iv_summary[
                    "information_value"
                ]
                < 0.10
            )
        ).sum()
    ),

    "features_with_iv_0_10_to_0_30": int(
        (
            (
                iv_summary[
                    "information_value"
                ]
                >= 0.10
            )
            &
            (
                iv_summary[
                    "information_value"
                ]
                < 0.30
            )
        ).sum()
    ),

    "features_with_iv_above_0_30": int(
        (
            iv_summary[
                "information_value"
            ]
            >= 0.30
        ).sum()
    ),

    "features_with_iv_above_0_50": int(
        (
            iv_summary[
                "information_value"
            ]
            >= 0.50
        ).sum()
    ),

    "high_iv_threshold": float(
        HIGH_IV_THRESHOLD
    ),

    "very_high_iv_threshold": float(
        VERY_HIGH_IV_THRESHOLD
    ),

    "preprocessing_rule": (
        "All binning, WoE mappings and Information Value "
        "calculations were learned from training data only. "
        "Validation and test datasets were transformed using "
        "unchanged training-derived mappings."
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
print("  - woe_bin_audit.csv")
print("  - woe_binning_definitions.json")
print("  - woe_mappings.json")
print("  - woe_metadata.json")

print("\nSource datasets were not modified.")

print("\nStage 04 status:")
print("PASS — WoE transformation and Information Value analysis completed.")

print("\nNext stage:")
print("05 — Feature selection and scorecard modelling")