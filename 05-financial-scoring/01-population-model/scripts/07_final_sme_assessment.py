"""
Orey Analytics
Financial Health Scoring - Final SME Assessment

Purpose:
Apply the validated Orey Financial Health Scorecard to
model-ready WoE SME data and produce final financial
health scores, default probabilities and risk classifications.

Important:
    - The model is NOT retrained in this stage.
    - The validated logistic regression model expects the
      20 selected WoE-transformed features.
    - Score scaling follows the validated scorecard metadata.
    - Risk bands follow the validated empirical score-band
      definitions.
"""

# ============================================================================
# IMPORTS
# ============================================================================

from pathlib import Path
from datetime import date
import json
import uuid
import warnings

import numpy as np
import pandas as pd
import joblib

warnings.filterwarnings("ignore")


# ============================================================================
# PROJECT PATHS
# ============================================================================

SCRIPT_DIR = Path(__file__).resolve().parent
MODEL_DIR = SCRIPT_DIR.parent

DATA_DIR = MODEL_DIR / "data"
OUTPUT_DIR = MODEL_DIR / "outputs"
MODELS_DIR = MODEL_DIR / "models"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# FILE PATHS
# ============================================================================

MODEL_FILE = (
    MODELS_DIR /
    "financial_health_scorecard.pkl"
)

COEFFICIENT_FILE = (
    OUTPUT_DIR /
    "scorecard_model_coefficients.csv"
)

FEATURE_POINTS_FILE = (
    OUTPUT_DIR /
    "scorecard_feature_points.csv"
)

METADATA_FILE = (
    OUTPUT_DIR /
    "scorecard_metadata.json"
)

# Existing validated model-test WoE dataset.
#
# This is used because an external SME assessment input file
# does not yet exist.
#
# Once an SME-level input pipeline is available, this can be
# replaced with the appropriate assessment dataset.
INPUT_FILE = (
    OUTPUT_DIR /
    "model_test_woe.csv"
)


# ============================================================================
# CONFIGURATION
# ============================================================================

TARGET = "default_event_12m"

PROBABILITY_COLUMN = (
    "predicted_default_probability"
)

SCORE_COLUMN = (
    "orey_financial_health_score"
)

MODEL_VERSION = (
    "Orey Financial Health Scorecard v1.0"
)

SCORE_MIN = 300
SCORE_MAX = 850

BASE_SCORE = 600
BASE_ODDS = 5.0
PDO = 20

SCORE_SCALING_FACTOR = 28.85390081777927
SCORE_SCALING_OFFSET = 553.5614381022527


# ============================================================================
# VALIDATED EMPIRICAL RISK BANDS
# ============================================================================

VERY_HIGH_RISK_MAX = 580
HIGH_RISK_MAX = 606
MODERATE_RISK_MAX = 629
LOW_RISK_MAX = 657


# ============================================================================
# HEADER
# ============================================================================

print("=" * 80)
print("OREY ANALYTICS — FINANCIAL HEALTH SCORING")
print("07 — FINAL SME ASSESSMENT")
print("=" * 80)


# ============================================================================
# LOAD VALIDATED MODEL
# ============================================================================

print("\nLoading validated scorecard model...")

if not MODEL_FILE.exists():

    raise FileNotFoundError(
        f"Validated model not found:\n{MODEL_FILE}"
    )

model = joblib.load(
    MODEL_FILE
)

print(
    f"Model loaded successfully:\n"
    f"{MODEL_FILE}"
)


# ============================================================================
# LOAD MODEL METADATA
# ============================================================================

print("\nLoading scorecard metadata...")

if not METADATA_FILE.exists():

    raise FileNotFoundError(
        f"Scorecard metadata not found:\n{METADATA_FILE}"
    )

with open(
    METADATA_FILE,
    "r",
    encoding="utf-8"
) as file:

    model_metadata = json.load(file)

print(
    f"Model: "
    f"{model_metadata.get('model_name', 'Unknown')}"
)

print(
    f"Model type: "
    f"{model_metadata.get('model_type', 'Unknown')}"
)

print(
    f"Target: "
    f"{model_metadata.get('target', TARGET)}"
)


# ============================================================================
# VALIDATE SCORECARD CONFIGURATION
# ============================================================================

print("\nValidating scorecard configuration...")

metadata_score_min = model_metadata.get(
    "score_minimum"
)

metadata_score_max = model_metadata.get(
    "score_maximum"
)

metadata_base_score = model_metadata.get(
    "base_score"
)

metadata_base_odds = model_metadata.get(
    "base_odds"
)

metadata_pdo = model_metadata.get(
    "pdo"
)

metadata_factor = model_metadata.get(
    "score_scaling_factor"
)

metadata_offset = model_metadata.get(
    "score_scaling_offset"
)


if metadata_score_min is not None:
    SCORE_MIN = int(metadata_score_min)

if metadata_score_max is not None:
    SCORE_MAX = int(metadata_score_max)

if metadata_base_score is not None:
    BASE_SCORE = float(metadata_base_score)

if metadata_base_odds is not None:
    BASE_ODDS = float(metadata_base_odds)

if metadata_pdo is not None:
    PDO = float(metadata_pdo)

if metadata_factor is not None:
    SCORE_SCALING_FACTOR = float(metadata_factor)

if metadata_offset is not None:
    SCORE_SCALING_OFFSET = float(metadata_offset)


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
    f"{BASE_ODDS}"
)

print(
    f"PDO: "
    f"{PDO}"
)

print(
    f"Scaling factor: "
    f"{SCORE_SCALING_FACTOR}"
)

print(
    f"Scaling offset: "
    f"{SCORE_SCALING_OFFSET}"
)


# ============================================================================
# LOAD COEFFICIENTS
# ============================================================================

if not COEFFICIENT_FILE.exists():

    raise FileNotFoundError(
        f"Scorecard coefficient file not found:\n"
        f"{COEFFICIENT_FILE}"
    )

coefficients = pd.read_csv(
    COEFFICIENT_FILE
)

print(
    f"\nModel coefficients loaded: "
    f"{len(coefficients)}"
)


# ============================================================================
# IDENTIFY VALIDATED WoE FEATURES
# ============================================================================

SELECTED_WOE_FEATURES = model_metadata.get(
    "selected_woe_features"
)

if not SELECTED_WOE_FEATURES:

    raise ValueError(
        "selected_woe_features were not found "
        "in scorecard metadata."
    )

print(
    f"\nValidated WoE model features: "
    f"{len(SELECTED_WOE_FEATURES)}"
)

for feature in SELECTED_WOE_FEATURES:

    print(
        f"  - {feature}"
    )


# ============================================================================
# VALIDATE MODEL FEATURE COUNT
# ============================================================================

if hasattr(
    model,
    "n_features_in_"
):

    model_feature_count = (
        model.n_features_in_
    )

    if (
        model_feature_count
        != len(SELECTED_WOE_FEATURES)
    ):

        raise ValueError(
            "Model feature count does not match "
            "the validated selected WoE feature list.\n"
            f"Model expects: {model_feature_count}\n"
            f"Metadata specifies: "
            f"{len(SELECTED_WOE_FEATURES)}"
        )


# ============================================================================
# RISK BAND ASSIGNMENT
# ============================================================================

def assign_risk_band(score):

    if score <= VERY_HIGH_RISK_MAX:

        return "Very High Risk"

    if score <= HIGH_RISK_MAX:

        return "High Risk"

    if score <= MODERATE_RISK_MAX:

        return "Moderate Risk"

    if score <= LOW_RISK_MAX:

        return "Low Risk"

    return "Very Low Risk"


# ============================================================================
# FINANCIAL HEALTH INTERPRETATION
# ============================================================================

def create_financial_health_status(
    risk_band
):

    descriptions = {

        "Very High Risk":
            "The business demonstrates very high financial "
            "risk and a materially elevated estimated "
            "probability of 12-month default.",

        "High Risk":
            "The business demonstrates high financial risk "
            "with an elevated estimated probability of "
            "12-month default.",

        "Moderate Risk":
            "The business demonstrates moderate financial "
            "risk with an intermediate estimated probability "
            "of 12-month default.",

        "Low Risk":
            "The business demonstrates relatively low "
            "financial risk with a comparatively low "
            "estimated probability of 12-month default.",

        "Very Low Risk":
            "The business demonstrates very low financial "
            "risk with a comparatively low estimated "
            "probability of 12-month default."
    }

    return descriptions[risk_band]


# ============================================================================
# PROBABILITY → SCORE CONVERSION
# ============================================================================

def probability_to_score(
    probability
):

    probability = np.clip(
        probability,
        0.0001,
        0.9999
    )

    odds = (
        (1 - probability)
        / probability
    )

    score = (
        SCORE_SCALING_OFFSET
        +
        SCORE_SCALING_FACTOR
        * np.log(odds)
    )

    score = np.clip(
        score,
        SCORE_MIN,
        SCORE_MAX
    )

    return score


# ============================================================================
# ASSESS SME DATA
# ============================================================================

def assess_sme(
    sme_data
):

    print("\nValidating assessment dataset...")

    missing_features = [
        feature
        for feature in SELECTED_WOE_FEATURES
        if feature not in sme_data.columns
    ]

    if missing_features:

        raise ValueError(
            "Assessment dataset is missing validated "
            "WoE model features:\n"
            +
            "\n".join(
                f"  - {feature}"
                for feature in missing_features
            )
        )

    # ------------------------------------------------------------------------
    # SELECT VALIDATED WOE FEATURES
    # ------------------------------------------------------------------------

    X = sme_data[
        SELECTED_WOE_FEATURES
    ].copy()

    # ------------------------------------------------------------------------
    # CHECK MISSING VALUES
    # ------------------------------------------------------------------------

    missing_values = (
        X.isna()
        .sum()
        .sum()
    )

    if missing_values > 0:

        raise ValueError(
            "Missing values detected in validated "
            f"WoE model features: {missing_values:,}"
        )

    # ------------------------------------------------------------------------
    # CHECK INFINITE VALUES
    # ------------------------------------------------------------------------

    infinite_values = np.isinf(
        X.to_numpy(
            dtype=float
        )
    ).sum()

    if infinite_values > 0:

        raise ValueError(
            "Infinite values detected in "
            f"WoE model features: {infinite_values:,}"
        )

    # ------------------------------------------------------------------------
    # MODEL PREDICTION
    # ------------------------------------------------------------------------

    print(
        "\nGenerating predicted default probabilities..."
    )

    predicted_probability = (
        model.predict_proba(X)[:, 1]
    )

    result = sme_data.copy()

    result[
        PROBABILITY_COLUMN
    ] = predicted_probability

    # ------------------------------------------------------------------------
    # CONVERT PROBABILITY TO OREY SCORE
    # ------------------------------------------------------------------------

    print(
        "Converting default probabilities "
        "to Orey Financial Health Scores..."
    )

    result[
        SCORE_COLUMN
    ] = (
        result[
            PROBABILITY_COLUMN
        ]
        .apply(probability_to_score)
        .round()
        .astype(int)
    )

    # ------------------------------------------------------------------------
    # ASSIGN RISK BAND
    # ------------------------------------------------------------------------

    result[
        "risk_band"
    ] = (
        result[
            SCORE_COLUMN
        ]
        .apply(assign_risk_band)
    )

    # ------------------------------------------------------------------------
    # FINANCIAL HEALTH STATUS
    # ------------------------------------------------------------------------

    result[
        "financial_health_status"
    ] = (
        result[
            "risk_band"
        ]
        .apply(
            create_financial_health_status
        )
    )

    # ------------------------------------------------------------------------
    # ASSESSMENT METADATA
    # ------------------------------------------------------------------------

    result[
        "assessment_id"
    ] = [
        str(uuid.uuid4())
        for _ in range(len(result))
    ]

    result[
        "assessment_date"
    ] = date.today().isoformat()

    result[
        "model_version"
    ] = MODEL_VERSION

    return result


# ============================================================================
# LOAD ASSESSMENT INPUT
# ============================================================================

print("\n" + "=" * 80)
print("ASSESSMENT INPUT")
print("=" * 80)

if not INPUT_FILE.exists():

    raise FileNotFoundError(
        f"""
Assessment input file not found:

{INPUT_FILE}

The current Stage 07 script expects the validated
model-test WoE dataset.

This is intentional because an external
sme_assessment_input.csv does not yet exist.
"""
    )

sme_data = pd.read_csv(
    INPUT_FILE
)

print(
    f"Input file: "
    f"{INPUT_FILE.name}"
)

print(
    f"Observations loaded: "
    f"{len(sme_data):,}"
)


# ============================================================================
# RUN FINAL ASSESSMENT
# ============================================================================

print("\n" + "=" * 80)
print("RUNNING FINAL SME ASSESSMENT")
print("=" * 80)

assessment_output = assess_sme(
    sme_data
)


# ============================================================================
# SUMMARY
# ============================================================================

summary_columns = [
    "business_id",
    "assessment_id",
    "assessment_date",
    SCORE_COLUMN,
    PROBABILITY_COLUMN,
    "risk_band",
    "financial_health_status",
    "model_version"
]

summary_columns = [
    column
    for column in summary_columns
    if column in assessment_output.columns
]

summary = assessment_output[
    summary_columns
].copy()


# ============================================================================
# RISK BAND SUMMARY
# ============================================================================

risk_band_summary = (
    assessment_output[
        "risk_band"
    ]
    .value_counts()
    .rename_axis("risk_band")
    .reset_index(
        name="number_of_smes"
    )
)

risk_band_summary[
    "percentage"
] = (
    risk_band_summary[
        "number_of_smes"
    ]
    /
    len(assessment_output)
    *
    100
).round(2)


# ============================================================================
# SCORE SUMMARY
# ============================================================================

score_summary = {

    "minimum_score": int(
        assessment_output[
            SCORE_COLUMN
        ].min()
    ),

    "maximum_score": int(
        assessment_output[
            SCORE_COLUMN
        ].max()
    ),

    "mean_score": float(
        assessment_output[
            SCORE_COLUMN
        ].mean()
    ),

    "median_score": float(
        assessment_output[
            SCORE_COLUMN
        ].median()
    ),

    "minimum_predicted_default_probability":
        float(
            assessment_output[
                PROBABILITY_COLUMN
            ].min()
        ),

    "maximum_predicted_default_probability":
        float(
            assessment_output[
                PROBABILITY_COLUMN
            ].max()
        ),

    "mean_predicted_default_probability":
        float(
            assessment_output[
                PROBABILITY_COLUMN
            ].mean()
        )
}


# ============================================================================
# SAVE FINAL ASSESSMENTS
# ============================================================================

ASSESSMENT_FILE = (
    OUTPUT_DIR /
    "final_sme_assessments.csv"
)

assessment_output.to_csv(
    ASSESSMENT_FILE,
    index=False
)


# ============================================================================
# SAVE SUMMARY
# ============================================================================

SUMMARY_FILE = (
    OUTPUT_DIR /
    "sme_scorecard_summary.csv"
)

summary.to_csv(
    SUMMARY_FILE,
    index=False
)


# ============================================================================
# SAVE RISK BAND SUMMARY
# ============================================================================

RISK_SUMMARY_FILE = (
    OUTPUT_DIR /
    "risk_band_summary.csv"
)

risk_band_summary.to_csv(
    RISK_SUMMARY_FILE,
    index=False
)


# ============================================================================
# SAVE ASSESSMENT METADATA
# ============================================================================

assessment_metadata = {

    "model_name":
        model_metadata.get(
            "model_name",
            "Orey Financial Health Scorecard"
        ),

    "model_version":
        MODEL_VERSION,

    "model_type":
        model_metadata.get(
            "model_type",
            "Logistic Regression"
        ),

    "target":
        TARGET,

    "assessment_stage":
        "07 — Final Orey Financial Health Score & SME Assessment",

    "assessment_date":
        date.today().isoformat(),

    "input_file":
        str(INPUT_FILE),

    "number_of_smes":
        int(len(assessment_output)),

    "score_minimum":
        SCORE_MIN,

    "score_maximum":
        SCORE_MAX,

    "base_score":
        BASE_SCORE,

    "base_odds":
        BASE_ODDS,

    "pdo":
        PDO,

    "score_scaling_factor":
        SCORE_SCALING_FACTOR,

    "score_scaling_offset":
        SCORE_SCALING_OFFSET,

    "risk_bands": {

        "Very High Risk":
            f"<= {VERY_HIGH_RISK_MAX}",

        "High Risk":
            f"{VERY_HIGH_RISK_MAX + 1}–{HIGH_RISK_MAX}",

        "Moderate Risk":
            f"{HIGH_RISK_MAX + 1}–{MODERATE_RISK_MAX}",

        "Low Risk":
            f"{MODERATE_RISK_MAX + 1}–{LOW_RISK_MAX}",

        "Very Low Risk":
            f">= {LOW_RISK_MAX + 1}"
    },

    "selected_features":
        model_metadata.get(
            "selected_features",
            []
        ),

    "selected_woe_features":
        SELECTED_WOE_FEATURES,

    "model_performance": {

        "train_auc":
            model_metadata.get(
                "train_auc"
            ),

        "validation_auc":
            model_metadata.get(
                "validation_auc"
            ),

        "test_auc":
            model_metadata.get(
                "test_auc"
            ),

        "train_brier_score":
            model_metadata.get(
                "train_brier_score"
            ),

        "validation_brier_score":
            model_metadata.get(
                "validation_brier_score"
            ),

        "test_brier_score":
            model_metadata.get(
                "test_brier_score"
            )
    },

    "score_summary":
        score_summary,

    "validation_status":
        "PASS",

    "model_retrained":
        False,

    "assessment_rule":
        "The validated logistic regression scorecard "
        "was applied to the selected WoE-transformed "
        "features without retraining.",

    "score_scaling_rule":
        "Score = offset + scaling_factor × ln((1-p)/p), "
        "bounded to the validated 300–850 score range."
}


ASSESSMENT_METADATA_FILE = (
    OUTPUT_DIR /
    "assessment_metadata.json"
)

with open(
    ASSESSMENT_METADATA_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        assessment_metadata,
        file,
        indent=4
    )


# ============================================================================
# DISPLAY RESULTS
# ============================================================================

print("\n" + "=" * 80)
print("FINAL SME ASSESSMENT RESULTS")
print("=" * 80)

print(
    summary.to_string(
        index=False
    )
)


print("\n" + "=" * 80)
print("RISK BAND DISTRIBUTION")
print("=" * 80)

print(
    risk_band_summary.to_string(
        index=False
    )
)


print("\n" + "=" * 80)
print("SCORE SUMMARY")
print("=" * 80)

print(
    f"Minimum score: "
    f"{score_summary['minimum_score']}"
)

print(
    f"Maximum score: "
    f"{score_summary['maximum_score']}"
)

print(
    f"Mean score: "
    f"{score_summary['mean_score']:.1f}"
)

print(
    f"Median score: "
    f"{score_summary['median_score']:.1f}"
)

print(
    f"Mean predicted default probability: "
    f"{score_summary['mean_predicted_default_probability']:.2%}"
)


# ============================================================================
# OUTPUTS
# ============================================================================

print("\n" + "=" * 80)
print("ASSESSMENT OUTPUTS SAVED")
print("=" * 80)

print(
    f"  - {ASSESSMENT_FILE.name}"
)

print(
    f"  - {SUMMARY_FILE.name}"
)

print(
    f"  - {RISK_SUMMARY_FILE.name}"
)

print(
    f"  - {ASSESSMENT_METADATA_FILE.name}"
)

print("\nModel was NOT retrained.")

print("\nStage 07 complete.")

print("\nNext stage:")
print("08 — Case Studies")