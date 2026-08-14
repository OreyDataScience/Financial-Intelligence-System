"""
Orey Analytics
Financial Health Scoring — Model Validation, Calibration & Risk Bands Stage 06

Purpose:
Validate the Orey Financial Health Scorecard, assess probability calibration,
measure discrimination and develop empirically supported risk bands.

Principles:
1. Validation is separate from model training.
2. Test data remains unseen until final evaluation.
3. Discrimination uses AUC, Gini and KS.
4. Calibration compares predicted and observed default rates.
5. Score bands use observed 12-month default rates.
6. Risk bands are derived from validation score quantiles.
7. Risk-band default rates must decrease as score increases.
8. Validation and test performance are compared for stability.
"""

from pathlib import Path
import json
import warnings

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, roc_curve, brier_score_loss
from sklearn.calibration import calibration_curve

warnings.filterwarnings("ignore")

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
MODEL_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = MODEL_DIR / "outputs"
MODELS_DIR = MODEL_DIR / "models"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

TRAIN_SCORE_FILE = OUTPUT_DIR / "model_train_scores.csv"
VALIDATION_SCORE_FILE = OUTPUT_DIR / "model_validation_scores.csv"
TEST_SCORE_FILE = OUTPUT_DIR / "model_test_scores.csv"

# Configuration
TARGET = "default_event_12m"
PROBABILITY_COLUMN = "predicted_default_probability"
SCORE_COLUMN = "orey_financial_health_score"

NUMBER_OF_SCORE_BANDS = 10
CALIBRATION_BINS = 10
SCORE_MIN = 300
SCORE_MAX = 850

print("OREY ANALYTICS — FINANCIAL HEALTH SCORING")
print("06 — MODEL VALIDATION, CALIBRATION & RISK BANDS")

# Load score data
print("\nLoading scorecard outputs...")

train = pd.read_csv(TRAIN_SCORE_FILE)
validation = pd.read_csv(VALIDATION_SCORE_FILE)
test = pd.read_csv(TEST_SCORE_FILE)

print(f"Training observations:   {len(train):,}")
print(f"Validation observations: {len(validation):,}")
print(f"Test observations:       {len(test):,}")

# Basic validation
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

# Target validation
print("\nTARGET VALIDATION")

for dataset_name, dataset in [
    ("Training", train),
    ("Validation", validation),
    ("Test", test)
]:
    print(
        f"{dataset_name} default rate: "
        f"{dataset[TARGET].mean():.2%}"
    )

# Score validation
print("\nSCORE VALIDATION")

for dataset_name, dataset in [
    ("Training", train),
    ("Validation", validation),
    ("Test", test)
]:
    minimum_score = dataset[SCORE_COLUMN].min()
    maximum_score = dataset[SCORE_COLUMN].max()

    print(
        f"{dataset_name}: minimum={minimum_score:.0f}, "
        f"median={dataset[SCORE_COLUMN].median():.0f}, "
        f"maximum={maximum_score:.0f}"
    )

    if minimum_score < SCORE_MIN:
        raise ValueError(
            f"{dataset_name} contains scores below the configured minimum."
        )

    if maximum_score > SCORE_MAX:
        raise ValueError(
            f"{dataset_name} contains scores above the configured maximum."
        )

# Discrimination performance
print("\nDISCRIMINATION PERFORMANCE")

def calculate_discrimination_metrics(dataset):
    y_true = dataset[TARGET].astype(int)
    probability = dataset[PROBABILITY_COLUMN].astype(float)

    auc = roc_auc_score(y_true, probability)
    gini = (2 * auc) - 1

    false_positive_rate, true_positive_rate, thresholds = roc_curve(
        y_true,
        probability
    )

    ks_values = true_positive_rate - false_positive_rate
    ks_index = np.argmax(ks_values)

    ks_statistic = ks_values[ks_index]
    ks_threshold = thresholds[ks_index]

    brier = brier_score_loss(y_true, probability)

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
    {"dataset": "train", **train_discrimination},
    {"dataset": "validation", **validation_discrimination},
    {"dataset": "test", **test_discrimination}
])

print(discrimination_output.to_string(index=False))

discrimination_output.to_csv(
    OUTPUT_DIR / "model_discrimination_validation.csv",
    index=False
)

# Probability calibration
print("\nPROBABILITY CALIBRATION")

def create_calibration_table(dataset, dataset_name):
    calibration_data = dataset.copy()

    calibration_data["probability_bin"] = pd.qcut(
        calibration_data[PROBABILITY_COLUMN],
        q=CALIBRATION_BINS,
        duplicates="drop"
    )

    calibration_table = (
        calibration_data
        .groupby("probability_bin", observed=True)
        .agg(
            observations=(TARGET, "size"),
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

    calibration_table.insert(0, "dataset", dataset_name)

    calibration_table["calibration_difference"] = (
        calibration_table["observed_default_rate"]
        - calibration_table["mean_predicted_probability"]
    )

    return calibration_table

train_calibration = create_calibration_table(train, "train")
validation_calibration = create_calibration_table(validation, "validation")
test_calibration = create_calibration_table(test, "test")

calibration_output = pd.concat(
    [
        train_calibration,
        validation_calibration,
        test_calibration
    ],
    ignore_index=True
)

print(calibration_output.to_string(index=False))

calibration_output.to_csv(
    OUTPUT_DIR / "probability_calibration_validation.csv",
    index=False
)

# Calibration summary
print("\nCALIBRATION SUMMARY")

def calculate_calibration_summary(calibration_table, dataset_name):
    differences = calibration_table["calibration_difference"].abs()

    return {
        "dataset": dataset_name,
        "mean_absolute_calibration_error": float(differences.mean()),
        "maximum_absolute_calibration_error": float(differences.max())
    }

calibration_summary = pd.DataFrame([
    calculate_calibration_summary(train_calibration, "train"),
    calculate_calibration_summary(validation_calibration, "validation"),
    calculate_calibration_summary(test_calibration, "test")
])

print(calibration_summary.to_string(index=False))

calibration_summary.to_csv(
    OUTPUT_DIR / "calibration_summary.csv",
    index=False
)

# Calibration curve data
print("\nCalculating calibration curves...")

calibration_curve_output = []

for dataset_name, dataset in [
    ("train", train),
    ("validation", validation),
    ("test", test)
]:
    observed_probability, mean_prediction = calibration_curve(
        dataset[TARGET],
        dataset[PROBABILITY_COLUMN],
        n_bins=CALIBRATION_BINS,
        strategy="quantile"
    )

    for observed, predicted in zip(
        observed_probability,
        mean_prediction
    ):
        calibration_curve_output.append({
            "dataset": dataset_name,
            "observed_default_rate": float(observed),
            "mean_predicted_probability": float(predicted),
            "calibration_difference": float(observed - predicted)
        })

calibration_curve_output = pd.DataFrame(
    calibration_curve_output
)

calibration_curve_output.to_csv(
    OUTPUT_DIR / "calibration_curve_data.csv",
    index=False
)

# Score band development
print("\nSCORE BAND DEVELOPMENT")

def create_score_bands(dataset, dataset_name):
    score_data = dataset.copy()

    score_data["score_band"] = pd.qcut(
        score_data[SCORE_COLUMN],
        q=NUMBER_OF_SCORE_BANDS,
        duplicates="drop"
    )

    band_table = (
        score_data
        .groupby("score_band", observed=True)
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

    band_table.insert(0, "dataset", dataset_name)

    band_table["score_band_number"] = range(
        1,
        len(band_table) + 1
    )

    return band_table

train_score_bands = create_score_bands(train, "train")
validation_score_bands = create_score_bands(validation, "validation")
test_score_bands = create_score_bands(test, "test")

score_band_output = pd.concat(
    [
        train_score_bands,
        validation_score_bands,
        test_score_bands
    ],
    ignore_index=True
)

print(score_band_output.to_string(index=False))

score_band_output.to_csv(
    OUTPUT_DIR / "score_band_validation.csv",
    index=False
)

# Score monotonicity
print("\nSCORE MONOTONICITY CHECK")

def check_score_monotonicity(score_band_table):
    rates = score_band_table["observed_default_rate"].to_numpy()

    return bool(
        np.all(
            np.diff(rates) <= 0
        )
    )

train_monotonic = check_score_monotonicity(train_score_bands)
validation_monotonic = check_score_monotonicity(validation_score_bands)
test_monotonic = check_score_monotonicity(test_score_bands)

print(f"Training score monotonicity: {train_monotonic}")
print(f"Validation score monotonicity: {validation_monotonic}")
print(f"Test score monotonicity: {test_monotonic}")

# Empirical risk band development
print("\nEMPIRICAL RISK BAND DEVELOPMENT")

score_quantiles = validation[SCORE_COLUMN].quantile(
    [0.20, 0.40, 0.60, 0.80]
)

very_high_cutoff = int(np.floor(score_quantiles.loc[0.20]))
high_cutoff = int(np.floor(score_quantiles.loc[0.40]))
moderate_cutoff = int(np.floor(score_quantiles.loc[0.60]))
low_cutoff = int(np.floor(score_quantiles.loc[0.80]))

print(f"Very High Risk: <= {very_high_cutoff}")
print(f"High Risk: {very_high_cutoff + 1}–{high_cutoff}")
print(f"Moderate Risk: {high_cutoff + 1}–{moderate_cutoff}")
print(f"Low Risk: {moderate_cutoff + 1}–{low_cutoff}")
print(f"Very Low Risk: >= {low_cutoff + 1}")

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

for dataset in [train, validation, test]:
    dataset["risk_band"] = dataset[SCORE_COLUMN].apply(
        assign_risk_band
    )

risk_band_order = [
    "Very High Risk",
    "High Risk",
    "Moderate Risk",
    "Low Risk",
    "Very Low Risk"
]

def create_risk_band_summary(dataset, dataset_name):
    summary = (
        dataset
        .groupby("risk_band", observed=False)
        .agg(
            observations=(TARGET, "size"),
            defaults=(TARGET, "sum"),
            observed_default_rate=(TARGET, "mean"),
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

    summary.insert(0, "dataset", dataset_name)

    return summary

train_risk_summary = create_risk_band_summary(train, "train")
validation_risk_summary = create_risk_band_summary(
    validation,
    "validation"
)
test_risk_summary = create_risk_band_summary(test, "test")

risk_band_output = pd.concat(
    [
        train_risk_summary,
        validation_risk_summary,
        test_risk_summary
    ],
    ignore_index=True
)

print(risk_band_output.to_string(index=False))

risk_band_output.to_csv(
    OUTPUT_DIR / "risk_band_validation.csv",
    index=False
)

# Risk band monotonicity
print("\nChecking empirical risk-band monotonicity...")

def check_risk_band_monotonicity(summary):
    rates = (
        summary["observed_default_rate"]
        .dropna()
        .to_numpy()
    )

    if len(rates) < 2:
        return False

    # Bands are ordered from highest risk to lowest risk.
    # Default rates should therefore decrease.
    return bool(
        np.all(
            np.diff(rates) <= 0
        )
    )

train_risk_monotonic = check_risk_band_monotonicity(
    train_risk_summary
)

validation_risk_monotonic = check_risk_band_monotonicity(
    validation_risk_summary
)

test_risk_monotonic = check_risk_band_monotonicity(
    test_risk_summary
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

# Risk band definitions
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

# Model stability
print("\nMODEL STABILITY CHECK")

auc_difference = abs(
    validation_discrimination["auc"]
    - test_discrimination["auc"]
)

gini_difference = abs(
    validation_discrimination["gini"]
    - test_discrimination["gini"]
)

ks_difference = abs(
    validation_discrimination["ks_statistic"]
    - test_discrimination["ks_statistic"]
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

# Final validation summary
print("\nFINAL MODEL VALIDATION SUMMARY")

print(
    f"Training AUC: {train_discrimination['auc']:.4f}"
)

print(
    f"Validation AUC: {validation_discrimination['auc']:.4f}"
)

print(
    f"Test AUC: {test_discrimination['auc']:.4f}"
)

print(
    f"Training Gini: {train_discrimination['gini']:.4f}"
)

print(
    f"Validation Gini: {validation_discrimination['gini']:.4f}"
)

print(
    f"Test Gini: {test_discrimination['gini']:.4f}"
)

print(
    f"Training KS: {train_discrimination['ks_statistic']:.4f}"
)

print(
    f"Validation KS: {validation_discrimination['ks_statistic']:.4f}"
)

print(
    f"Test KS: {test_discrimination['ks_statistic']:.4f}"
)

print(
    f"Validation risk-band monotonicity: "
    f"{validation_risk_monotonic}"
)

print(
    f"Test risk-band monotonicity: "
    f"{test_risk_monotonic}"
)

# Validation status
model_validation_pass = all([
    validation_monotonic,
    test_monotonic,
    validation_risk_monotonic,
    test_risk_monotonic
])

print(
    "\nMODEL VALIDATION STATUS: "
    f"{'PASS' if model_validation_pass else 'REVIEW REQUIRED'}"
)

# Metadata
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
    "train_score_monotonicity": train_monotonic,
    "validation_score_monotonicity": validation_monotonic,
    "test_score_monotonicity": test_monotonic,
    "train_risk_band_monotonicity": train_risk_monotonic,
    "validation_risk_band_monotonicity": (
        validation_risk_monotonic
    ),
    "test_risk_band_monotonicity": test_risk_monotonic,
    "validation_test_auc_difference": float(auc_difference),
    "validation_test_gini_difference": float(gini_difference),
    "validation_test_ks_difference": float(ks_difference),
    "model_validation_pass": bool(model_validation_pass),
    "calibration_summary": {
        row["dataset"]: {
            "mean_absolute_calibration_error": float(
                row["mean_absolute_calibration_error"]
            ),
            "maximum_absolute_calibration_error": float(
                row["maximum_absolute_calibration_error"]
            )
        }
        for _, row in calibration_summary.iterrows()
    },
    "risk_band_cutoffs": {
        "very_high_risk_max": int(very_high_cutoff),
        "high_risk_max": int(high_cutoff),
        "moderate_risk_max": int(moderate_cutoff),
        "low_risk_max": int(low_cutoff)
    },
    "risk_band_methodology": (
        "Candidate risk bands were derived from validation "
        "score quantiles at the 20th, 40th, 60th and 80th "
        "percentiles. The resulting bands were evaluated "
        "on training, validation and test datasets using "
        "observed 12-month default rates. Risk-band "
        "monotonicity is defined as non-increasing default "
        "rates from Very High Risk through Very Low Risk."
    ),
    "validation_rule": (
        "Model discrimination, probability calibration, "
        "score separation and empirical risk-band performance "
        "were evaluated using training, validation and test "
        "data. Validation data was used to establish candidate "
        "risk thresholds. The test dataset was retained for "
        "final out-of-sample evaluation."
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

# Completion
print("\nMODEL VALIDATION & RISK BAND DEVELOPMENT COMPLETE")

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
print("  - model_validation_metadata.json")

print("\nSource datasets were not modified.")
print("\nNext stage:")
print("07 — Final Orey Financial Health Score & SME Assessment")