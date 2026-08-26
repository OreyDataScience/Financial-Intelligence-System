"""
Orey Analytics
Financial Health Scoring - Model Validation, Calibration & Risk Bands

Stage 06

Purpose:
Validate the Orey Financial Health Scorecard, assess probability calibration,
measure discrimination, test model stability and develop empirically supported
risk bands.

Key principles:
1. Stage 05 model outputs are evaluated without retraining the model.
2. Training, validation and test datasets remain separated.
3. Discrimination is assessed using AUC, Gini and KS.
4. Calibration compares predicted and observed default rates.
5. Score bands evaluate default-rate separation across score ranges.
6. Risk-band thresholds are derived from validation data only.
7. Higher-risk bands should generally show higher default rates.
8. Validation and test performance are compared for stability.
9. Test data is used only for final out-of-sample evaluation.
10. All validation outputs and decisions are saved for auditability.
"""

# IMPORTS
from pathlib import Path
import json
import warnings

import numpy as np
import pandas as pd

from sklearn.metrics import (
    roc_auc_score,
    roc_curve,
    brier_score_loss
)
from sklearn.calibration import calibration_curve

warnings.filterwarnings("ignore")

# PROJECT PATHS
SCRIPT_DIR = Path(__file__).resolve().parent
MODEL_DIR = SCRIPT_DIR.parent

OUTPUT_DIR = MODEL_DIR / "outputs"
MODELS_DIR = MODEL_DIR / "models"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

TRAIN_SCORE_FILE = OUTPUT_DIR / "model_train_scores.csv"
VALIDATION_SCORE_FILE = OUTPUT_DIR / "model_validation_scores.csv"
TEST_SCORE_FILE = OUTPUT_DIR / "model_test_scores.csv"

# CONFIGURATION
TARGET = "default_event_12m"
PROBABILITY_COLUMN = "predicted_default_probability"
SCORE_COLUMN = "orey_financial_health_score"

NUMBER_OF_SCORE_BANDS = 10
CALIBRATION_BINS = 10

SCORE_MIN = 300
SCORE_MAX = 850

AUC_MINIMUM = 0.70
GINI_MINIMUM = 0.40
KS_MINIMUM = 0.30

MAX_AUC_DEGRADATION = 0.05
MAX_GINI_DEGRADATION = 0.10
MAX_KS_DEGRADATION = 0.10

MAX_CALIBRATION_ERROR = 0.05

# HEADER
print("=" * 80)
print("OREY ANALYTICS — FINANCIAL HEALTH SCORING")
print("06 — MODEL VALIDATION, CALIBRATION & RISK BANDS")
print("=" * 80)

# VALIDATE INPUT FILES
print("\nChecking required files...")

required_files = [
    TRAIN_SCORE_FILE,
    VALIDATION_SCORE_FILE,
    TEST_SCORE_FILE
]

for file in required_files:
    if not file.exists():
        raise FileNotFoundError(
            f"Required file not found: {file}"
        )

print("Required files confirmed.")

# LOAD SCORECARD OUTPUTS
print("\nLoading scorecard outputs...")

train = pd.read_csv(TRAIN_SCORE_FILE)
validation = pd.read_csv(VALIDATION_SCORE_FILE)
test = pd.read_csv(TEST_SCORE_FILE)

print(f"Training observations:   {len(train):,}")
print(f"Validation observations: {len(validation):,}")
print(f"Test observations:       {len(test):,}")

# BASIC VALIDATION
print("\nChecking required columns...")

required_columns = [
    TARGET,
    PROBABILITY_COLUMN,
    SCORE_COLUMN
]

for dataset_name, dataset in [
    ("training", train),
    ("validation", validation),
    ("test", test)
]:
    for column in required_columns:
        if column not in dataset.columns:
            raise ValueError(
                f"{column} is missing from {dataset_name} score data."
            )

    if dataset[TARGET].isna().any():
        raise ValueError(
            f"Missing target values detected in {dataset_name} data."
        )

    if not dataset[TARGET].isin([0, 1]).all():
        raise ValueError(
            f"Unexpected target values detected in {dataset_name} data."
        )

    if dataset[PROBABILITY_COLUMN].isna().any():
        raise ValueError(
            f"Missing predicted probabilities detected in {dataset_name} data."
        )

    if dataset[SCORE_COLUMN].isna().any():
        raise ValueError(
            f"Missing scores detected in {dataset_name} data."
        )

    if not np.isfinite(
        dataset[PROBABILITY_COLUMN].to_numpy(dtype=float)
    ).all():
        raise ValueError(
            f"Invalid predicted probabilities detected in {dataset_name} data."
        )

    if not np.isfinite(
        dataset[SCORE_COLUMN].to_numpy(dtype=float)
    ).all():
        raise ValueError(
            f"Invalid scores detected in {dataset_name} data."
        )

print("Required columns and values confirmed.")

# TARGET VALIDATION
print("\n" + "=" * 80)
print("TARGET VALIDATION")
print("=" * 80)

for dataset_name, dataset in [
    ("Training", train),
    ("Validation", validation),
    ("Test", test)
]:
    print(
        f"{dataset_name} default rate: "
        f"{dataset[TARGET].mean():.2%}"
    )

# SCORE VALIDATION
print("\n" + "=" * 80)
print("SCORE VALIDATION")
print("=" * 80)

for dataset_name, dataset in [
    ("Training", train),
    ("Validation", validation),
    ("Test", test)
]:
    minimum_score = dataset[SCORE_COLUMN].min()
    median_score = dataset[SCORE_COLUMN].median()
    maximum_score = dataset[SCORE_COLUMN].max()

    print(
        f"{dataset_name}: "
        f"minimum={minimum_score:.0f}, "
        f"median={median_score:.0f}, "
        f"maximum={maximum_score:.0f}"
    )

    if minimum_score < SCORE_MIN:
        raise ValueError(
            f"{dataset_name} contains scores below {SCORE_MIN}."
        )

    if maximum_score > SCORE_MAX:
        raise ValueError(
            f"{dataset_name} contains scores above {SCORE_MAX}."
        )

# PROBABILITY VALIDATION
print("\n" + "=" * 80)
print("PROBABILITY VALIDATION")
print("=" * 80)

for dataset_name, dataset in [
    ("Training", train),
    ("Validation", validation),
    ("Test", test)
]:
    minimum_probability = dataset[PROBABILITY_COLUMN].min()
    maximum_probability = dataset[PROBABILITY_COLUMN].max()

    print(
        f"{dataset_name}: "
        f"minimum={minimum_probability:.6f}, "
        f"maximum={maximum_probability:.6f}"
    )

    if minimum_probability < 0 or maximum_probability > 1:
        raise ValueError(
            f"{dataset_name} contains probabilities outside 0-1."
        )

# DISCRIMINATION PERFORMANCE
print("\n" + "=" * 80)
print("DISCRIMINATION PERFORMANCE")
print("=" * 80)

def calculate_discrimination_metrics(dataset):
    y_true = dataset[TARGET].astype(int)
    probability = dataset[PROBABILITY_COLUMN].astype(float)

    auc = roc_auc_score(
        y_true,
        probability
    )

    gini = (2 * auc) - 1

    false_positive_rate, true_positive_rate, thresholds = roc_curve(
        y_true,
        probability
    )

    ks_values = (
        true_positive_rate
        - false_positive_rate
    )

    ks_index = int(
        np.argmax(ks_values)
    )

    ks_statistic = ks_values[ks_index]
    ks_threshold = thresholds[ks_index]

    brier = brier_score_loss(
        y_true,
        probability
    )

    return {
        "auc": float(auc),
        "gini": float(gini),
        "ks_statistic": float(ks_statistic),
        "ks_probability_threshold": float(ks_threshold),
        "brier_score": float(brier)
    }

train_discrimination = calculate_discrimination_metrics(train)
validation_discrimination = calculate_discrimination_metrics(validation)
test_discrimination = calculate_discrimination_metrics(test)

discrimination_output = pd.DataFrame([
    {
        "dataset": "train",
        **train_discrimination
    },
    {
        "dataset": "validation",
        **validation_discrimination
    },
    {
        "dataset": "test",
        **test_discrimination
    }
])

print(
    discrimination_output.to_string(
        index=False
    )
)

discrimination_output.to_csv(
    OUTPUT_DIR / "model_discrimination_validation.csv",
    index=False
)

# CALIBRATION TABLE
print("\n" + "=" * 80)
print("PROBABILITY CALIBRATION")
print("=" * 80)

def create_calibration_table(
    dataset,
    dataset_name
):
    calibration_data = dataset[
        [
            TARGET,
            PROBABILITY_COLUMN
        ]
    ].copy()

    unique_probabilities = (
        calibration_data[PROBABILITY_COLUMN]
        .nunique()
    )

    number_of_bins = min(
        CALIBRATION_BINS,
        unique_probabilities
    )

    if number_of_bins < 2:
        raise ValueError(
            f"Insufficient probability variation in {dataset_name}."
        )

    calibration_data["probability_bin"] = pd.qcut(
        calibration_data[PROBABILITY_COLUMN],
        q=number_of_bins,
        duplicates="drop"
    )

    calibration_table = (
        calibration_data
        .groupby(
            "probability_bin",
            observed=True
        )
        .agg(
            observations=(TARGET, "size"),
            defaults=(TARGET, "sum"),
            observed_default_rate=(TARGET, "mean"),
            mean_predicted_probability=(
                PROBABILITY_COLUMN,
                "mean"
            ),
            minimum_predicted_probability=(
                PROBABILITY_COLUMN,
                "min"
            ),
            maximum_predicted_probability=(
                PROBABILITY_COLUMN,
                "max"
            )
        )
        .reset_index()
    )

    calibration_table.insert(
        0,
        "dataset",
        dataset_name
    )

    calibration_table[
        "calibration_difference"
    ] = (
        calibration_table["observed_default_rate"]
        -
        calibration_table["mean_predicted_probability"]
    )

    calibration_table[
        "absolute_calibration_difference"
    ] = (
        calibration_table["calibration_difference"]
        .abs()
    )

    return calibration_table

train_calibration = create_calibration_table(
    train,
    "train"
)

validation_calibration = create_calibration_table(
    validation,
    "validation"
)

test_calibration = create_calibration_table(
    test,
    "test"
)

calibration_output = pd.concat(
    [
        train_calibration,
        validation_calibration,
        test_calibration
    ],
    ignore_index=True
)

print(
    calibration_output.to_string(
        index=False
    )
)

calibration_output.to_csv(
    OUTPUT_DIR / "probability_calibration_validation.csv",
    index=False
)

# CALIBRATION SUMMARY
print("\nCALIBRATION SUMMARY")

def calculate_calibration_summary(
    calibration_table,
    dataset_name
):
    differences = (
        calibration_table[
            "absolute_calibration_difference"
        ]
    )

    return {
        "dataset": dataset_name,
        "mean_absolute_calibration_error": float(
            differences.mean()
        ),
        "maximum_absolute_calibration_error": float(
            differences.max()
        )
    }

calibration_summary = pd.DataFrame([
    calculate_calibration_summary(
        train_calibration,
        "train"
    ),
    calculate_calibration_summary(
        validation_calibration,
        "validation"
    ),
    calculate_calibration_summary(
        test_calibration,
        "test"
    )
])

print(
    calibration_summary.to_string(
        index=False
    )
)

calibration_summary.to_csv(
    OUTPUT_DIR / "calibration_summary.csv",
    index=False
)

# CALIBRATION CURVE
print("\nCalculating calibration curves...")

calibration_curve_output = []

for dataset_name, dataset in [
    ("train", train),
    ("validation", validation),
    ("test", test)
]:
    observed_probability, mean_prediction = calibration_curve(
        dataset[TARGET].astype(int),
        dataset[PROBABILITY_COLUMN].astype(float),
        n_bins=CALIBRATION_BINS,
        strategy="quantile"
    )

    for observed, predicted in zip(
        observed_probability,
        mean_prediction
    ):
        calibration_curve_output.append({
            "dataset": dataset_name,
            "observed_default_rate": float(
                observed
            ),
            "mean_predicted_probability": float(
                predicted
            ),
            "calibration_difference": float(
                observed - predicted
            )
        })

calibration_curve_output = pd.DataFrame(
    calibration_curve_output
)

calibration_curve_output.to_csv(
    OUTPUT_DIR / "calibration_curve_data.csv",
    index=False
)

# SCORE BANDS
print("\n" + "=" * 80)
print("SCORE BAND DEVELOPMENT")
print("=" * 80)

def create_score_bands(
    dataset,
    dataset_name
):
    score_data = dataset[
        [
            TARGET,
            PROBABILITY_COLUMN,
            SCORE_COLUMN
        ]
    ].copy()

    unique_scores = (
        score_data[SCORE_COLUMN]
        .nunique()
    )

    number_of_bands = min(
        NUMBER_OF_SCORE_BANDS,
        unique_scores
    )

    if number_of_bands < 2:
        raise ValueError(
            f"Insufficient score variation in {dataset_name}."
        )

    score_data["score_band"] = pd.qcut(
        score_data[SCORE_COLUMN],
        q=number_of_bands,
        duplicates="drop"
    )

    band_table = (
        score_data
        .groupby(
            "score_band",
            observed=True
        )
        .agg(
            observations=(TARGET, "size"),
            defaults=(TARGET, "sum"),
            observed_default_rate=(TARGET, "mean"),
            mean_score=(SCORE_COLUMN, "mean"),
            minimum_score=(SCORE_COLUMN, "min"),
            maximum_score=(SCORE_COLUMN, "max"),
            mean_predicted_probability=(
                PROBABILITY_COLUMN,
                "mean"
            )
        )
        .reset_index()
    )

    band_table.insert(
        0,
        "dataset",
        dataset_name
    )

    band_table["score_band_number"] = range(
        1,
        len(band_table) + 1
    )

    return band_table

train_score_bands = create_score_bands(
    train,
    "train"
)

validation_score_bands = create_score_bands(
    validation,
    "validation"
)

test_score_bands = create_score_bands(
    test,
    "test"
)

score_band_output = pd.concat(
    [
        train_score_bands,
        validation_score_bands,
        test_score_bands
    ],
    ignore_index=True
)

print(
    score_band_output.to_string(
        index=False
    )
)

score_band_output.to_csv(
    OUTPUT_DIR / "score_band_validation.csv",
    index=False
)

# SCORE MONOTONICITY
print("\nSCORE MONOTONICITY CHECK")

def calculate_monotonicity(
    score_band_table
):
    rates = (
        score_band_table
        .sort_values("mean_score")[
            "observed_default_rate"
        ]
        .dropna()
        .to_numpy()
    )

    if len(rates) < 2:
        return False

    violations = np.sum(
        np.diff(rates) > 0
    )

    return bool(
        violations == 0
    )

train_monotonic = calculate_monotonicity(
    train_score_bands
)

validation_monotonic = calculate_monotonicity(
    validation_score_bands
)

test_monotonic = calculate_monotonicity(
    test_score_bands
)

print(
    f"Training score monotonicity: "
    f"{train_monotonic}"
)

print(
    f"Validation score monotonicity: "
    f"{validation_monotonic}"
)

print(
    f"Test score monotonicity: "
    f"{test_monotonic}"
)

# EMPIRICAL RISK BANDS
print("\n" + "=" * 80)
print("EMPIRICAL RISK BAND DEVELOPMENT")
print("=" * 80)

score_quantiles = validation[
    SCORE_COLUMN
].quantile(
    [0.20, 0.40, 0.60, 0.80]
)

very_high_cutoff = int(
    np.floor(
        score_quantiles.loc[0.20]
    )
)

high_cutoff = int(
    np.floor(
        score_quantiles.loc[0.40]
    )
)

moderate_cutoff = int(
    np.floor(
        score_quantiles.loc[0.60]
    )
)

low_cutoff = int(
    np.floor(
        score_quantiles.loc[0.80]
    )
)

print(
    f"Very High Risk: <= {very_high_cutoff}"
)

print(
    f"High Risk: "
    f"{very_high_cutoff + 1}–{high_cutoff}"
)

print(
    f"Moderate Risk: "
    f"{high_cutoff + 1}–{moderate_cutoff}"
)

print(
    f"Low Risk: "
    f"{moderate_cutoff + 1}–{low_cutoff}"
)

print(
    f"Very Low Risk: >= {low_cutoff + 1}"
)

def assign_risk_band(score):
    if score <= very_high_cutoff:
        return "Very High Risk"

    if score <= high_cutoff:
        return "High Risk"

    if score <= moderate_cutoff:
        return "Moderate Risk"

    if score <= low_cutoff:
        return "Low Risk"

    return "Very Low Risk"

for dataset in [
    train,
    validation,
    test
]:
    dataset["risk_band"] = dataset[
        SCORE_COLUMN
    ].apply(
        assign_risk_band
    )

risk_band_order = [
    "Very High Risk",
    "High Risk",
    "Moderate Risk",
    "Low Risk",
    "Very Low Risk"
]

def create_risk_band_summary(
    dataset,
    dataset_name
):
    summary = (
        dataset
        .groupby(
            "risk_band",
            observed=False
        )
        .agg(
            observations=(TARGET, "size"),
            defaults=(TARGET, "sum"),
            observed_default_rate=(TARGET, "mean"),
            population_share=(TARGET, "size"),
            mean_score=(SCORE_COLUMN, "mean"),
            mean_predicted_probability=(
                PROBABILITY_COLUMN,
                "mean"
            ),
            minimum_score=(SCORE_COLUMN, "min"),
            maximum_score=(SCORE_COLUMN, "max")
        )
        .reindex(risk_band_order)
        .reset_index()
    )

    summary["population_share"] = (
        summary["population_share"]
        / len(dataset)
    )

    summary.insert(
        0,
        "dataset",
        dataset_name
    )

    return summary

train_risk_summary = create_risk_band_summary(
    train,
    "train"
)

validation_risk_summary = create_risk_band_summary(
    validation,
    "validation"
)

test_risk_summary = create_risk_band_summary(
    test,
    "test"
)

risk_band_output = pd.concat(
    [
        train_risk_summary,
        validation_risk_summary,
        test_risk_summary
    ],
    ignore_index=True
)

print(
    risk_band_output.to_string(
        index=False
    )
)

risk_band_output.to_csv(
    OUTPUT_DIR / "risk_band_validation.csv",
    index=False
)

# RISK BAND MONOTONICITY
print("\nChecking empirical risk-band monotonicity...")

def check_risk_band_monotonicity(
    summary
):
    rates = (
        summary[
            "observed_default_rate"
        ]
        .dropna()
        .to_numpy()
    )

    if len(rates) < 2:
        return False

    return bool(
        np.all(
            np.diff(rates) <= 0
        )
    )

train_risk_monotonic = (
    check_risk_band_monotonicity(
        train_risk_summary
    )
)

validation_risk_monotonic = (
    check_risk_band_monotonicity(
        validation_risk_summary
    )
)

test_risk_monotonic = (
    check_risk_band_monotonicity(
        test_risk_summary
    )
)

print(
    f"Training risk-band monotonicity: "
    f"{train_risk_monotonic}"
)

print(
    f"Validation risk-band monotonicity: "
    f"{validation_risk_monotonic}"
)

print(
    f"Test risk-band monotonicity: "
    f"{test_risk_monotonic}"
)

# RISK BAND DEFINITIONS
risk_band_definitions = pd.DataFrame([
    {
        "risk_band": "Very High Risk",
        "minimum_score": SCORE_MIN,
        "maximum_score": very_high_cutoff
    },
    {
        "risk_band": "High Risk",
        "minimum_score": very_high_cutoff + 1,
        "maximum_score": high_cutoff
    },
    {
        "risk_band": "Moderate Risk",
        "minimum_score": high_cutoff + 1,
        "maximum_score": moderate_cutoff
    },
    {
        "risk_band": "Low Risk",
        "minimum_score": moderate_cutoff + 1,
        "maximum_score": low_cutoff
    },
    {
        "risk_band": "Very Low Risk",
        "minimum_score": low_cutoff + 1,
        "maximum_score": SCORE_MAX
    }
])

risk_band_definitions.to_csv(
    OUTPUT_DIR / "risk_band_definitions.csv",
    index=False
)

# MODEL STABILITY
print("\n" + "=" * 80)
print("MODEL STABILITY CHECK")
print("=" * 80)

auc_difference = abs(
    validation_discrimination["auc"]
    -
    test_discrimination["auc"]
)

gini_difference = abs(
    validation_discrimination["gini"]
    -
    test_discrimination["gini"]
)

ks_difference = abs(
    validation_discrimination["ks_statistic"]
    -
    test_discrimination["ks_statistic"]
)

validation_auc_degradation = max(
    0.0,
    validation_discrimination["auc"]
    -
    test_discrimination["auc"]
)

validation_gini_degradation = max(
    0.0,
    validation_discrimination["gini"]
    -
    test_discrimination["gini"]
)

validation_ks_degradation = max(
    0.0,
    validation_discrimination["ks_statistic"]
    -
    test_discrimination["ks_statistic"]
)

print(
    f"Validation-Test AUC difference: "
    f"{auc_difference:.4f}"
)

print(
    f"Validation-Test Gini difference: "
    f"{gini_difference:.4f}"
)

print(
    f"Validation-Test KS difference: "
    f"{ks_difference:.4f}"
)

print(
    f"Maximum allowed AUC degradation: "
    f"{MAX_AUC_DEGRADATION:.4f}"
)

print(
    f"Maximum allowed Gini degradation: "
    f"{MAX_GINI_DEGRADATION:.4f}"
)

print(
    f"Maximum allowed KS degradation: "
    f"{MAX_KS_DEGRADATION:.4f}"
)

# VALIDATION CRITERIA
print("\n" + "=" * 80)
print("VALIDATION CRITERIA")
print("=" * 80)

validation_auc_pass = (
    validation_discrimination["auc"]
    >= AUC_MINIMUM
)

test_auc_pass = (
    test_discrimination["auc"]
    >= AUC_MINIMUM
)

validation_gini_pass = (
    validation_discrimination["gini"]
    >= GINI_MINIMUM
)

test_gini_pass = (
    test_discrimination["gini"]
    >= GINI_MINIMUM
)

validation_ks_pass = (
    validation_discrimination["ks_statistic"]
    >= KS_MINIMUM
)

test_ks_pass = (
    test_discrimination["ks_statistic"]
    >= KS_MINIMUM
)

validation_calibration_error = float(
    calibration_summary.loc[
        calibration_summary["dataset"] == "validation",
        "mean_absolute_calibration_error"
    ].iloc[0]
)

test_calibration_error = float(
    calibration_summary.loc[
        calibration_summary["dataset"] == "test",
        "mean_absolute_calibration_error"
    ].iloc[0]
)

validation_calibration_pass = (
    validation_calibration_error
    <= MAX_CALIBRATION_ERROR
)

test_calibration_pass = (
    test_calibration_error
    <= MAX_CALIBRATION_ERROR
)

stability_auc_pass = (
    validation_auc_degradation
    <= MAX_AUC_DEGRADATION
)

stability_gini_pass = (
    validation_gini_degradation
    <= MAX_GINI_DEGRADATION
)

stability_ks_pass = (
    validation_ks_degradation
    <= MAX_KS_DEGRADATION
)

print(
    f"Validation AUC >= {AUC_MINIMUM}: "
    f"{validation_auc_pass}"
)

print(
    f"Test AUC >= {AUC_MINIMUM}: "
    f"{test_auc_pass}"
)

print(
    f"Validation Gini >= {GINI_MINIMUM}: "
    f"{validation_gini_pass}"
)

print(
    f"Test Gini >= {GINI_MINIMUM}: "
    f"{test_gini_pass}"
)

print(
    f"Validation KS >= {KS_MINIMUM}: "
    f"{validation_ks_pass}"
)

print(
    f"Test KS >= {KS_MINIMUM}: "
    f"{test_ks_pass}"
)

print(
    f"Validation calibration error <= "
    f"{MAX_CALIBRATION_ERROR:.2%}: "
    f"{validation_calibration_pass}"
)

print(
    f"Test calibration error <= "
    f"{MAX_CALIBRATION_ERROR:.2%}: "
    f"{test_calibration_pass}"
)

print(
    f"AUC stability: "
    f"{stability_auc_pass}"
)

print(
    f"Gini stability: "
    f"{stability_gini_pass}"
)

print(
    f"KS stability: "
    f"{stability_ks_pass}"
)

# FINAL VALIDATION STATUS
model_validation_pass = all([
    validation_auc_pass,
    test_auc_pass,
    validation_gini_pass,
    test_gini_pass,
    validation_ks_pass,
    test_ks_pass,
    validation_calibration_pass,
    test_calibration_pass,
    stability_auc_pass,
    stability_gini_pass,
    stability_ks_pass,
    validation_risk_monotonic,
    test_risk_monotonic
])

print("\n" + "=" * 80)
print("FINAL MODEL VALIDATION SUMMARY")
print("=" * 80)

print(
    f"Training AUC: "
    f"{train_discrimination['auc']:.4f}"
)

print(
    f"Validation AUC: "
    f"{validation_discrimination['auc']:.4f}"
)

print(
    f"Test AUC: "
    f"{test_discrimination['auc']:.4f}"
)

print(
    f"Training Gini: "
    f"{train_discrimination['gini']:.4f}"
)

print(
    f"Validation Gini: "
    f"{validation_discrimination['gini']:.4f}"
)

print(
    f"Test Gini: "
    f"{test_discrimination['gini']:.4f}"
)

print(
    f"Training KS: "
    f"{train_discrimination['ks_statistic']:.4f}"
)

print(
    f"Validation KS: "
    f"{validation_discrimination['ks_statistic']:.4f}"
)

print(
    f"Test KS: "
    f"{test_discrimination['ks_statistic']:.4f}"
)

print(
    f"Validation calibration error: "
    f"{validation_calibration_error:.4f}"
)

print(
    f"Test calibration error: "
    f"{test_calibration_error:.4f}"
)

print(
    f"Validation risk-band monotonicity: "
    f"{validation_risk_monotonic}"
)

print(
    f"Test risk-band monotonicity: "
    f"{test_risk_monotonic}"
)

print(
    "\nMODEL VALIDATION STATUS: "
    f"{'PASS' if model_validation_pass else 'REVIEW REQUIRED'}"
)

# SAVE MODEL STABILITY
stability_output = pd.DataFrame([
    {
        "metric": "AUC",
        "validation_value": validation_discrimination["auc"],
        "test_value": test_discrimination["auc"],
        "absolute_difference": auc_difference,
        "maximum_allowed_degradation": MAX_AUC_DEGRADATION,
        "pass": stability_auc_pass
    },
    {
        "metric": "Gini",
        "validation_value": validation_discrimination["gini"],
        "test_value": test_discrimination["gini"],
        "absolute_difference": gini_difference,
        "maximum_allowed_degradation": MAX_GINI_DEGRADATION,
        "pass": stability_gini_pass
    },
    {
        "metric": "KS",
        "validation_value": validation_discrimination["ks_statistic"],
        "test_value": test_discrimination["ks_statistic"],
        "absolute_difference": ks_difference,
        "maximum_allowed_degradation": MAX_KS_DEGRADATION,
        "pass": stability_ks_pass
    }
])

stability_output.to_csv(
    OUTPUT_DIR / "model_stability_validation.csv",
    index=False
)

# SAVE METADATA
metadata = {
    "model_name": "Orey Financial Health Scorecard",
    "validation_stage": (
        "06 — Model Validation, Calibration & Risk Bands"
    ),
    "target": TARGET,
    "training_rows": int(len(train)),
    "validation_rows": int(len(validation)),
    "test_rows": int(len(test)),
    "score_minimum": int(SCORE_MIN),
    "score_maximum": int(SCORE_MAX),
    "calibration_bins": int(CALIBRATION_BINS),
    "score_bands": int(NUMBER_OF_SCORE_BANDS),
    "validation_thresholds": {
        "minimum_auc": float(AUC_MINIMUM),
        "minimum_gini": float(GINI_MINIMUM),
        "minimum_ks": float(KS_MINIMUM),
        "maximum_calibration_error": float(
            MAX_CALIBRATION_ERROR
        ),
        "maximum_auc_degradation": float(
            MAX_AUC_DEGRADATION
        ),
        "maximum_gini_degradation": float(
            MAX_GINI_DEGRADATION
        ),
        "maximum_ks_degradation": float(
            MAX_KS_DEGRADATION
        )
    },
    "train_auc": train_discrimination["auc"],
    "validation_auc": validation_discrimination["auc"],
    "test_auc": test_discrimination["auc"],
    "train_gini": train_discrimination["gini"],
    "validation_gini": validation_discrimination["gini"],
    "test_gini": test_discrimination["gini"],
    "train_ks": train_discrimination["ks_statistic"],
    "validation_ks": validation_discrimination["ks_statistic"],
    "test_ks": test_discrimination["ks_statistic"],
    "train_brier_score": train_discrimination["brier_score"],
    "validation_brier_score": (
        validation_discrimination["brier_score"]
    ),
    "test_brier_score": test_discrimination["brier_score"],
    "validation_calibration_error": (
        validation_calibration_error
    ),
    "test_calibration_error": (
        test_calibration_error
    ),
    "validation_test_auc_difference": float(
        auc_difference
    ),
    "validation_test_gini_difference": float(
        gini_difference
    ),
    "validation_test_ks_difference": float(
        ks_difference
    ),
    "train_score_monotonicity": train_monotonic,
    "validation_score_monotonicity": validation_monotonic,
    "test_score_monotonicity": test_monotonic,
    "train_risk_band_monotonicity": train_risk_monotonic,
    "validation_risk_band_monotonicity": (
        validation_risk_monotonic
    ),
    "test_risk_band_monotonicity": (
        test_risk_monotonic
    ),
    "validation_risk_band_cutoffs": {
        "very_high_risk_max": int(
            very_high_cutoff
        ),
        "high_risk_max": int(
            high_cutoff
        ),
        "moderate_risk_max": int(
            moderate_cutoff
        ),
        "low_risk_max": int(
            low_cutoff
        )
    },
    "validation_criteria": {
        "validation_auc_pass": bool(
            validation_auc_pass
        ),
        "test_auc_pass": bool(
            test_auc_pass
        ),
        "validation_gini_pass": bool(
            validation_gini_pass
        ),
        "test_gini_pass": bool(
            test_gini_pass
        ),
        "validation_ks_pass": bool(
            validation_ks_pass
        ),
        "test_ks_pass": bool(
            test_ks_pass
        ),
        "validation_calibration_pass": bool(
            validation_calibration_pass
        ),
        "test_calibration_pass": bool(
            test_calibration_pass
        ),
        "stability_auc_pass": bool(
            stability_auc_pass
        ),
        "stability_gini_pass": bool(
            stability_gini_pass
        ),
        "stability_ks_pass": bool(
            stability_ks_pass
        ),
        "validation_risk_monotonic": bool(
            validation_risk_monotonic
        ),
        "test_risk_monotonic": bool(
            test_risk_monotonic
        )
    },
    "model_validation_pass": bool(
        model_validation_pass
    ),
    "risk_band_methodology": (
        "Risk bands were derived using validation score "
        "quantiles at the 20th, 40th, 60th and 80th "
        "percentiles. The resulting thresholds were then "
        "evaluated across training, validation and test "
        "datasets."
    ),
    "validation_methodology": (
        "The Stage 05 scorecard was evaluated without "
        "retraining. Discrimination, calibration, score "
        "separation, risk-band behaviour and validation-test "
        "stability were assessed using separated datasets."
    )
}

with open(
    OUTPUT_DIR / "model_validation_metadata.json",
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
print("MODEL VALIDATION & RISK BAND DEVELOPMENT COMPLETE")
print("=" * 80)

print(
    f"\nModel validation status: "
    f"{'PASS' if model_validation_pass else 'REVIEW REQUIRED'}"
)

print(
    f"Validation AUC: "
    f"{validation_discrimination['auc']:.4f}"
)

print(
    f"Test AUC: "
    f"{test_discrimination['auc']:.4f}"
)

print(
    f"Validation calibration error: "
    f"{validation_calibration_error:.4f}"
)

print(
    f"Test calibration error: "
    f"{test_calibration_error:.4f}"
)

print("\nOutputs saved to:")
print(OUTPUT_DIR)

print("\nGenerated files:")
print("  - model_discrimination_validation.csv")
print("  - probability_calibration_validation.csv")
print("  - calibration_summary.csv")
print("  - calibration_curve_data.csv")
print("  - score_band_validation.csv")
print("  - risk_band_validation.csv")
print("  - risk_band_definitions.csv")
print("  - model_stability_validation.csv")
print("  - model_validation_metadata.json")

print("\nSource datasets were not modified.")

print("\nNext stage:")
print("07 — Final Orey Financial Health Score & SME Assessment")