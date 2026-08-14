"""
Orey Analytics
Financial Health Scoring - Feature Selection & Scorecard Modelling

Purpose: Select stable predictors and build a logistic-regression credit scorecard.

Key principles:
    1. Feature selection is performed using training data only.
    2. Information Value is used as the initial predictive filter.
    3. Highly correlated predictors are reduced to avoid redundant information.
    4. Logistic regression provides an interpretable scorecard model.
    5. Validation and test data are used only for model evaluation.
    6. The final score is scaled to a 3-digit Orey Financial Health Score.
    7. Model coefficients, selected features and scoring metadata are saved.
"""

# IMPORTS
from pathlib import Path
import json
import warnings
import pickle

import numpy as np
import pandas as pd

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    roc_auc_score,
    accuracy_score,
    precision_score,
    recall_score,
    confusion_matrix,
    brier_score_loss
)

warnings.filterwarnings("ignore")

# PROJECT PATHS
SCRIPT_DIR = Path(__file__).resolve().parent
MODEL_DIR = SCRIPT_DIR.parent

DATA_DIR = MODEL_DIR / "data"
OUTPUT_DIR = MODEL_DIR / "outputs"
MODELS_DIR = MODEL_DIR / "models"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

TRAIN_FILE = OUTPUT_DIR / "model_train_woe.csv"
VALIDATION_FILE = OUTPUT_DIR / "model_validation_woe.csv"
TEST_FILE = OUTPUT_DIR / "model_test_woe.csv"
IV_FILE = OUTPUT_DIR / "feature_iv_summary.csv"

# CONFIGURATION
TARGET = "default_event_12m"

IV_MINIMUM = 0.02
CORRELATION_THRESHOLD = 0.70

SCORE_MIN = 300
SCORE_MAX = 850

BASE_SCORE = 600
BASE_ODDS = 5.0
PDO = 20

RANDOM_STATE = 42

# HEADER
print("=" * 80)
print("OREY ANALYTICS — FINANCIAL HEALTH SCORING")
print("05 — FEATURE SELECTION & SCORECARD MODELLING")
print("=" * 80)

# LOAD DATA
print("\nLoading WoE datasets...")

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
    IV_FILE
]

for file in required_files:

    if not file.exists():

        raise FileNotFoundError(
            f"Required file not found: {file}"
        )

required_columns = [
    TARGET
]

for column in required_columns:

    if column not in train.columns:
        raise ValueError(
            f"Required column missing from training data: {column}"
        )

    if column not in validation.columns:
        raise ValueError(
            f"Required column missing from validation data: {column}"
        )

    if column not in test.columns:
        raise ValueError(
            f"Required column missing from test data: {column}"
        )

# TARGET VALIDATION
print("\n" + "=" * 80)
print("TARGET VALIDATION")
print("=" * 80)

print(
    f"Training default rate: "
    f"{train[TARGET].mean():.2%}"
)

print(
    f"Validation default rate: "
    f"{validation[TARGET].mean():.2%}"
)

print(
    f"Test default rate: "
    f"{test[TARGET].mean():.2%}"
)

for dataset_name, dataset in [
    ("training", train),
    ("validation", validation),
    ("test", test)
]:

    if dataset[TARGET].isna().any():

        raise ValueError(
            f"Missing target values detected in {dataset_name} data."
        )

    if not dataset[TARGET].isin([0, 1]).all():

        raise ValueError(
            f"Unexpected target values detected in {dataset_name} data."
        )

# FEATURE ALIGNMENT
print("\nPredictor features available:")

woe_feature_columns = [
    column
    for column in train.columns
    if column != TARGET
]

print(
    f"{len(woe_feature_columns)}"
)

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

if woe_feature_columns != validation_features:

    raise ValueError(
        "Training and validation predictors are not aligned."
    )

if woe_feature_columns != test_features:

    raise ValueError(
        "Training and test predictors are not aligned."
    )

print("\nChecking feature alignment...")
print("Feature alignment confirmed.")

# MAP WOE FEATURES TO ORIGINAL FEATURES
print("\nMapping WoE features to original feature names...")

woe_feature_map = {}

for column in woe_feature_columns:

    if column.startswith("woe_"):

        original_feature = column.replace(
            "woe_",
            "",
            1
        )

        woe_feature_map[original_feature] = column

    else:

        woe_feature_map[column] = column

original_feature_columns = list(
    woe_feature_map.keys()
)

print(
    f"Original features represented in WoE dataset: "
    f"{len(original_feature_columns)}"
)

# LOAD INFORMATION VALUE
print("\n" + "=" * 80)
print("INFORMATION VALUE FILTER")
print("=" * 80)

iv_summary = pd.read_csv(IV_FILE)

required_iv_columns = [
    "feature",
    "information_value"
]

for column in required_iv_columns:

    if column not in iv_summary.columns:

        raise ValueError(
            f"IV summary is missing required column: {column}"
        )

iv_summary["feature"] = (
    iv_summary["feature"]
    .astype(str)
    .str.strip()
)

iv_summary["information_value"] = pd.to_numeric(
    iv_summary["information_value"],
    errors="coerce"
)

iv_summary = iv_summary.dropna(
    subset=["information_value"]
)

iv_summary = iv_summary[
    iv_summary["feature"].isin(
        original_feature_columns
    )
].copy()

print(
    f"Features in WoE dataset: "
    f"{len(original_feature_columns)}"
)

print(
    f"Features in IV summary: "
    f"{len(pd.read_csv(IV_FILE))}"
)

print(
    f"Features matched between datasets: "
    f"{len(iv_summary)}"
)

if iv_summary.empty:

    print("\nExample WoE feature names:")

    for feature in woe_feature_columns[:10]:
        print(f"  - {feature}")

    print("\nExample IV feature names:")

    for feature in pd.read_csv(IV_FILE)["feature"].head(10):
        print(f"  - {feature}")

    raise ValueError(
        "No feature names in the IV summary matched the original "
        "feature names represented by the WoE training dataset."
    )

print(
    f"\nIV threshold: "
    f"{IV_MINIMUM}"
)

iv_selected_original = iv_summary.loc[
    iv_summary["information_value"] >= IV_MINIMUM,
    "feature"
].tolist()

iv_removed = [
    feature
    for feature in original_feature_columns
    if feature not in iv_selected_original
]

print(
    f"Features before IV filtering: "
    f"{len(original_feature_columns)}"
)

print(
    f"Features retained after IV filtering: "
    f"{len(iv_selected_original)}"
)

print(
    f"Features removed by IV filtering: "
    f"{len(iv_removed)}"
)

# CONVERT SELECTED ORIGINAL FEATURES TO WOE FEATURES
iv_selected_woe = [
    woe_feature_map[feature]
    for feature in iv_selected_original
    if feature in woe_feature_map
]

# SAVE IV FILTER RESULTS
iv_filter_output = iv_summary.copy()

iv_filter_output["selected"] = (
    iv_filter_output["feature"]
    .isin(iv_selected_original)
)

iv_filter_output["woe_feature"] = (
    iv_filter_output["feature"]
    .map(woe_feature_map)
)

iv_filter_output.to_csv(
    OUTPUT_DIR / "feature_selection_iv_results.csv",
    index=False
)

# CORRELATION / REDUNDANCY CONTROL
print("\n" + "=" * 80)
print("CORRELATION & REDUNDANCY CONTROL")
print("=" * 80)

X_train_iv = train[
    iv_selected_woe
].copy()

X_train_iv = X_train_iv.apply(
    pd.to_numeric,
    errors="coerce"
)

correlation_matrix = X_train_iv.corr(
    method="spearman"
).abs()

upper_triangle = correlation_matrix.where(
    np.triu(
        np.ones(
            correlation_matrix.shape,
            dtype=bool
        ),
        k=1
    )
)

correlated_features = set()

for column in upper_triangle.columns:

    correlated_columns = upper_triangle.index[
        upper_triangle[column] >= CORRELATION_THRESHOLD
    ].tolist()

    if not correlated_columns:
        continue

    for correlated_column in correlated_columns:

        original_column = column.replace(
            "woe_",
            "",
            1
        )

        original_correlated = correlated_column.replace(
            "woe_",
            "",
            1
        )

        iv_column = iv_summary.loc[
            iv_summary["feature"] == original_column,
            "information_value"
        ]

        iv_correlated = iv_summary.loc[
            iv_summary["feature"] == original_correlated,
            "information_value"
        ]

        if iv_column.empty or iv_correlated.empty:
            continue

        iv_column = float(
            iv_column.iloc[0]
        )

        iv_correlated = float(
            iv_correlated.iloc[0]
        )

        if iv_column >= iv_correlated:

            correlated_features.add(
                correlated_column
            )

        else:

            correlated_features.add(
                column
            )

selected_features = [
    feature
    for feature in iv_selected_woe
    if feature not in correlated_features
]

selected_original_features = [
    feature.replace(
        "woe_",
        "",
        1
    )
    for feature in selected_features
]

print(
    f"Correlation threshold: "
    f"{CORRELATION_THRESHOLD:.2f}"
)

print(
    f"Features before correlation filtering: "
    f"{len(iv_selected_woe)}"
)

print(
    f"Redundant features removed: "
    f"{len(correlated_features)}"
)

print(
    f"Features retained: "
    f"{len(selected_features)}"
)

if correlated_features:

    print("\nRemoved redundant features:")

    for feature in sorted(correlated_features):

        print(
            f"  - {feature}"
        )

# SAVE SELECTED FEATURES
selected_feature_output = pd.DataFrame({
    "feature": selected_original_features,
    "woe_feature": selected_features
})

selected_feature_output = selected_feature_output.merge(
    iv_summary[
        [
            "feature",
            "information_value"
        ]
    ],
    on="feature",
    how="left"
)

selected_feature_output = selected_feature_output.sort_values(
    "information_value",
    ascending=False
)

selected_feature_output.to_csv(
    OUTPUT_DIR / "selected_features.csv",
    index=False
)

# BUILD MODEL MATRICES
print("\n" + "=" * 80)
print("BUILDING SCORECARD MODEL DATA")
print("=" * 80)

X_train = train[
    selected_features
].copy()

X_validation = validation[
    selected_features
].copy()

X_test = test[
    selected_features
].copy()

y_train = train[
    TARGET
].astype(int)

y_validation = validation[
    TARGET
].astype(int)

y_test = test[
    TARGET
].astype(int)

# CHECK MODEL INPUTS
for dataset_name, dataset in [
    ("training", X_train),
    ("validation", X_validation),
    ("test", X_test)
]:

    missing_values = int(
        dataset.isna().sum().sum()
    )

    infinite_values = int(
        np.isinf(
            dataset.to_numpy(
                dtype=float
            )
        ).sum()
    )

    print(
        f"{dataset_name.capitalize()} missing values: "
        f"{missing_values:,}"
    )

    print(
        f"{dataset_name.capitalize()} infinite values: "
        f"{infinite_values:,}"
    )

    if missing_values > 0:

        raise ValueError(
            f"Missing values detected in {dataset_name} predictors."
        )

    if infinite_values > 0:

        raise ValueError(
            f"Infinite values detected in {dataset_name} predictors."
        )

# LOGISTIC REGRESSION
print("\n" + "=" * 80)
print("LOGISTIC REGRESSION SCORECARD")
print("=" * 80)

print(
    f"Final model features: "
    f"{len(selected_features)}"
)

model = LogisticRegression(
    penalty="l2",
    C=1.0,
    solver="liblinear",
    max_iter=2000,
    random_state=RANDOM_STATE
)

print("\nFitting logistic regression on training data...")

model.fit(
    X_train,
    y_train
)

print("Model fitting complete.")

# MODEL COEFFICIENTS
coefficients = pd.DataFrame({
    "feature": selected_original_features,
    "woe_feature": selected_features,
    "coefficient": model.coef_[0]
})

coefficients["odds_ratio"] = np.exp(
    coefficients["coefficient"]
)

coefficients = coefficients.merge(
    iv_summary[
        [
            "feature",
            "information_value"
        ]
    ],
    on="feature",
    how="left"
)

coefficients["absolute_coefficient"] = (
    coefficients["coefficient"]
    .abs()
)

coefficients = coefficients.sort_values(
    "absolute_coefficient",
    ascending=False
)

coefficients.to_csv(
    OUTPUT_DIR / "scorecard_model_coefficients.csv",
    index=False
)

# PREDICT DEFAULT PROBABILITIES
print("\n" + "=" * 80)
print("MODEL PERFORMANCE")
print("=" * 80)

train_probability = model.predict_proba(
    X_train
)[:, 1]

validation_probability = model.predict_proba(
    X_validation
)[:, 1]

test_probability = model.predict_proba(
    X_test
)[:, 1]

train_prediction = (
    train_probability >= 0.50
).astype(int)

validation_prediction = (
    validation_probability >= 0.50
).astype(int)

test_prediction = (
    test_probability >= 0.50
).astype(int)

# PERFORMANCE FUNCTION
def calculate_metrics(
    y_true,
    probability,
    prediction
):

    tn, fp, fn, tp = confusion_matrix(
        y_true,
        prediction,
        labels=[0, 1]
    ).ravel()

    return {
        "auc": float(
            roc_auc_score(
                y_true,
                probability
            )
        ),
        "accuracy": float(
            accuracy_score(
                y_true,
                prediction
            )
        ),
        "precision": float(
            precision_score(
                y_true,
                prediction,
                zero_division=0
            )
        ),
        "recall": float(
            recall_score(
                y_true,
                prediction,
                zero_division=0
            )
        ),
        "brier_score": float(
            brier_score_loss(
                y_true,
                probability
            )
        ),
        "true_negatives": int(tn),
        "false_positives": int(fp),
        "false_negatives": int(fn),
        "true_positives": int(tp)
    }

train_metrics = calculate_metrics(
    y_train,
    train_probability,
    train_prediction
)

validation_metrics = calculate_metrics(
    y_validation,
    validation_probability,
    validation_prediction
)

test_metrics = calculate_metrics(
    y_test,
    test_probability,
    test_prediction
)

performance = pd.DataFrame([
    {
        "dataset": "train",
        **train_metrics
    },
    {
        "dataset": "validation",
        **validation_metrics
    },
    {
        "dataset": "test",
        **test_metrics
    }
])

print("\nModel performance:")

print(
    performance.to_string(
        index=False
    )
)

performance.to_csv(
    OUTPUT_DIR / "scorecard_model_performance.csv",
    index=False
)

# SCORE SCALING
print("\n" + "=" * 80)
print("OREY FINANCIAL HEALTH SCORE SCALING")
print("=" * 80)

print(
    f"Score range: "
    f"{SCORE_MIN}–{SCORE_MAX}"
)

print(
    f"Base score: "
    f"{BASE_SCORE}"
)

print(
    f"Base odds: "
    f"{BASE_ODDS}:1"
)

print(
    f"Points to double the odds: "
    f"{PDO}"
)

# SCORECARD SCALING
factor = PDO / np.log(2)

offset = (
    BASE_SCORE
    - factor * np.log(BASE_ODDS)
)

def probability_to_score(
    probability
):

    probability = np.clip(
        probability,
        1e-6,
        1 - 1e-6
    )

    odds = (
        (1 - probability)
        / probability
    )

    score = (
        offset
        + factor * np.log(odds)
    )

    return np.clip(
        score,
        SCORE_MIN,
        SCORE_MAX
    )

train_score = probability_to_score(
    train_probability
)

validation_score = probability_to_score(
    validation_probability
)

test_score = probability_to_score(
    test_probability
)

# SCORECARD FEATURE POINTS
scorecard_points = pd.DataFrame({
    "feature": selected_original_features,
    "woe_feature": selected_features,
    "coefficient": model.coef_[0]
})

scorecard_points["points_at_woe_1"] = (
    -factor
    * scorecard_points["coefficient"]
)

scorecard_points = scorecard_points.merge(
    iv_summary[
        [
            "feature",
            "information_value"
        ]
    ],
    on="feature",
    how="left"
)

scorecard_points.to_csv(
    OUTPUT_DIR / "scorecard_feature_points.csv",
    index=False
)

# SCORE OUTPUTS
train_scores = pd.DataFrame({
    "default_event_12m": y_train.values,
    "predicted_default_probability": train_probability,
    "orey_financial_health_score": train_score.round().astype(int)
})

validation_scores = pd.DataFrame({
    "default_event_12m": y_validation.values,
    "predicted_default_probability": validation_probability,
    "orey_financial_health_score": validation_score.round().astype(int)
})

test_scores = pd.DataFrame({
    "default_event_12m": y_test.values,
    "predicted_default_probability": test_probability,
    "orey_financial_health_score": test_score.round().astype(int)
})

train_scores.to_csv(
    OUTPUT_DIR / "model_train_scores.csv",
    index=False
)

validation_scores.to_csv(
    OUTPUT_DIR / "model_validation_scores.csv",
    index=False
)

test_scores.to_csv(
    OUTPUT_DIR / "model_test_scores.csv",
    index=False
)

# SCORE DISTRIBUTION
print("\nScore distributions:")

for dataset_name, scores in [
    ("Training", train_score),
    ("Validation", validation_score),
    ("Test", test_score)
]:

    print(
        f"{dataset_name}: "
        f"minimum={scores.min():.0f}, "
        f"median={np.median(scores):.0f}, "
        f"maximum={scores.max():.0f}"
    )

# SAVE MODEL
print("\n" + "=" * 80)
print("SAVING SCORECARD MODEL")
print("=" * 80)

model_file = (
    MODELS_DIR
    / "financial_health_scorecard.pkl"
)

with open(
    model_file,
    "wb"
) as file:

    pickle.dump(
        model,
        file
    )

print(
    f"Model saved to: "
    f"{model_file}"
)

# SAVE MODEL METADATA
metadata = {
    "model_name": "Orey Financial Health Scorecard",
    "model_type": "Logistic Regression",
    "target": TARGET,
    "training_rows": int(len(train)),
    "validation_rows": int(len(validation)),
    "test_rows": int(len(test)),
    "original_features": int(len(woe_feature_columns)),
    "iv_threshold": float(IV_MINIMUM),
    "features_after_iv_filter": int(len(iv_selected_original)),
    "correlation_threshold": float(CORRELATION_THRESHOLD),
    "features_removed_by_correlation": int(
        len(correlated_features)
    ),
    "final_features": int(len(selected_features)),
    "selected_features": selected_original_features,
    "selected_woe_features": selected_features,
    "score_minimum": int(SCORE_MIN),
    "score_maximum": int(SCORE_MAX),
    "base_score": int(BASE_SCORE),
    "base_odds": float(BASE_ODDS),
    "pdo": int(PDO),
    "score_scaling_factor": float(factor),
    "score_scaling_offset": float(offset),
    "train_auc": train_metrics["auc"],
    "validation_auc": validation_metrics["auc"],
    "test_auc": test_metrics["auc"],
    "train_brier_score": train_metrics["brier_score"],
    "validation_brier_score": validation_metrics["brier_score"],
    "test_brier_score": test_metrics["brier_score"],
    "random_state": RANDOM_STATE,
    "feature_selection_rule": (
        "Predictors were first filtered using training-derived "
        "Information Value and then reduced for high Spearman "
        "correlation, retaining the predictor with higher IV."
    ),
    "model_training_rule": (
        "The logistic regression model was fitted using training "
        "observations only. Validation and test datasets were used "
        "only for performance evaluation."
    ),
    "score_scaling_rule": (
        "Score is scaled using a base score, base odds and points "
        "to double the odds."
    )
}

with open(
    OUTPUT_DIR / "scorecard_metadata.json",
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
print("FEATURE SELECTION & SCORECARD MODELLING COMPLETE")
print("=" * 80)

print(
    f"\nFinal scorecard features: "
    f"{len(selected_features)}"
)

print(
    f"Validation AUC: "
    f"{validation_metrics['auc']:.4f}"
)

print(
    f"Test AUC: "
    f"{test_metrics['auc']:.4f}"
)

print(
    "\nOutputs saved to:"
)

print(
    OUTPUT_DIR
)

print("\nGenerated files:")

print("  - feature_selection_iv_results.csv")
print("  - selected_features.csv")
print("  - scorecard_model_coefficients.csv")
print("  - scorecard_model_performance.csv")
print("  - scorecard_feature_points.csv")
print("  - model_train_scores.csv")
print("  - model_validation_scores.csv")
print("  - model_test_scores.csv")
print("  - scorecard_metadata.json")

print("\nModel saved to:")

print(
    model_file
)

print("\nSource datasets were not modified.")

print("\nNext stage:")
print("06 — Model validation, calibration and risk band development")