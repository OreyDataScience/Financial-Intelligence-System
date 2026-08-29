"""
Orey Analytics
Financial Health Scoring — Population Model

Stage 08 — Applicant Scoring & Reason Codes

Purpose:
Score the SME applicant population (new deals, no known outcome yet) using
the trained Stage 05 scorecard, and produce underwriter- and applicant-
facing reason codes explaining each score.

This stage does NOT retrain or refit anything. Every transformation applied
to applicants — feature engineering, missing-value treatment, WoE binning,
model coefficients, score scaling and risk bands — is replayed exactly as
it was fitted on the training population in Stages 02–06, using only the
artifacts those stages already saved to disk.

Pipeline replayed here:
    1. Feature engineering (Stage 02 ratio/structure formulas only —
       transaction-level features are excluded, exactly as Stage 03
       excluded them from the primary scorecard).
    2. Missing-value treatment, using training medians and categorical
       fill rules reconstructed from the Stage 02 engineered panel's
       training split (Stage 03 fit these on training data but did not
       persist the fitted values, so they are rebuilt here from the same
       filter/split logic and are byte-for-byte reproducible).
    3. Column alignment to Stage 03's final preprocessed feature schema.
    4. WoE transformation using Stage 04's saved bin edges and WoE
       mappings (woe_binning_definitions.json, woe_mappings.json).
       Unseen applicant values receive neutral WoE, exactly as Stage 04
       treated unseen validation/test values.
    5. Scoring using the Stage 05 pickled logistic regression and its
       saved score-scaling factor/offset.
    6. Risk-band assignment using Stage 06's validation-derived cutoffs.
    7. Lending decision policy, matching Stage 07's business-rules layer.
    8. Reason codes: per-applicant point contributions derived from
       scorecard_feature_points.csv, ranked to surface the top adverse
       and top protective factors behind each score.

Key principles:
    1. No model is retrained. No bin edges, WoE values or coefficients are
       recomputed from applicant data.
    2. Applicants are new, unscored deals — there is no outcome to
       validate against, so this stage produces scores and explanations,
       not performance metrics.
    3. Any applicant feature engineering, imputation or WoE step that
       cannot be completed exactly as it was for training data is treated
       as a hard error rather than an approximation.
    4. Source datasets and upstream stage outputs are never modified.
    5. Reason codes are derived directly from the fitted scorecard's own
       points table — no separate explanation model is introduced.

Folder layout:
    This stage lives in a separate phase folder from the population
    model build (02-individual-assessment), since applicant scoring is a
    repeatable production activity while the population model itself is
    only built/retrained periodically. It reads Stage 01-07 artifacts
    from a sibling 01-population-model folder and never writes to it.
"""

# IMPORTS
from pathlib import Path
import json
import pickle
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

#===========================================================================
# PROJECT PATHS
#===========================================================================
# This stage lives in a separate phase folder from the population model
# (individual/applicant assessment is a distinct, repeatable production
# consumer of a model that is only trained once). It therefore reads
# Stages 01-07's artifacts from the population-model folder, and writes
# its own outputs into its own folder.
#
# Assumed folder layout (siblings under one parent, e.g. "Financial
# Health Scoring/"):
#
#   01-population-model/
#       data/        <- historical panel data
#       outputs/     <- Stage 01-07 CSV/JSON outputs (read here)
#       models/      <- financial_health_scorecard.pkl (read here)
#       scripts/     <- 01_...py ... 07_...py
#   02-individual-assessment/
#       data/        <- applicant population file goes here
#       outputs/     <- Stage 08 outputs are written here
#       scripts/     <- this script
#
# If your folder names differ, only POPULATION_MODEL_FOLDER_NAME below
# needs to change.

SCRIPT_DIR = Path(__file__).resolve().parent
ASSESSMENT_DIR = SCRIPT_DIR.parent
PHASE_DIR = ASSESSMENT_DIR.parent

POPULATION_MODEL_FOLDER_NAME = "01-population-model"
POPULATION_MODEL_DIR = PHASE_DIR / POPULATION_MODEL_FOLDER_NAME

# Inputs — read from the population model phase (never written to)
POPULATION_OUTPUT_DIR = POPULATION_MODEL_DIR / "outputs"
POPULATION_MODELS_DIR = POPULATION_MODEL_DIR / "models"

# Outputs — this phase's own data/outputs
DATA_DIR = ASSESSMENT_DIR / "data"
OUTPUT_DIR = ASSESSMENT_DIR / "outputs"

DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

APPLICANT_FILE = DATA_DIR / "sme applicant scoring population.csv"
ENGINEERED_FILE = (
    POPULATION_OUTPUT_DIR / "financial_health_panel_engineered.csv"
)

PREPROCESSED_FEATURE_LIST_FILE = (
    POPULATION_OUTPUT_DIR / "preprocessed_feature_list.csv"
)

WOE_BINNING_DEFINITIONS_FILE = (
    POPULATION_OUTPUT_DIR / "woe_binning_definitions.json"
)
WOE_MAPPINGS_FILE = POPULATION_OUTPUT_DIR / "woe_mappings.json"

SCORECARD_METADATA_FILE = (
    POPULATION_OUTPUT_DIR / "scorecard_metadata.json"
)
SCORECARD_POINTS_FILE = (
    POPULATION_OUTPUT_DIR / "scorecard_feature_points.csv"
)
FEATURE_METADATA_FILE = POPULATION_OUTPUT_DIR / "feature_metadata.csv"
MODEL_FILE = POPULATION_MODELS_DIR / "financial_health_scorecard.pkl"

RISK_BAND_DEFINITIONS_FILE = (
    POPULATION_OUTPUT_DIR / "risk_band_definitions.csv"
)

#===========================================================================
# CONFIGURATION
#===========================================================================

TARGET = "default_event_12m"
PROBABILITY_COLUMN = "predicted_default_probability"
SCORE_COLUMN = "orey_financial_health_score"

# Replicated from Stage 03 — required to rebuild training-consistent
# imputation and column selection, since the fitted imputer itself was
# not persisted.
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

OUTCOME_COLUMNS = [TARGET]

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

IDENTIFIER_COLUMNS = [
    "business_id",
    "snapshot_date",
    "province",
    "industry_sector",
    "legal_entity_type",
    "business_age_years",
    "annual_revenue"
]

RISK_BAND_ORDER = [
    "Very High Risk",
    "High Risk",
    "Moderate Risk",
    "Low Risk",
    "Very Low Risk"
]

# Raw applicant-population columns required to reproduce Stage 02's
# non-transaction (categories 1-9) feature engineering.
REQUIRED_RAW_COLUMNS = [
    "business_id",
    "snapshot_date",
    "province",
    "industry_sector",
    "legal_entity_type",
    "credit_volatility_90d",
    "cash_flow_trend_90d",
    "min_balance_90d",
    "avg_balance_90d",
    "avg_weekly_credits_90d",
    "fixed_monthly_debits",
    "total_credits_90d",
    "total_credits_180d",
    "total_credits_365d",
    "monthly_expenses",
    "negative_balance_frequency_90d",
    "negative_balance_days_90d",
    "free_cash_flow",
    "monthly_revenue",
    "debt_service_coverage_ratio",
    "total_liabilities",
    "total_assets",
    "total_equity",
    "annual_revenue",
    "existing_debt_exposure",
    "num_bounced_payments_90d",
    "num_reversed_transactions_90d",
    "num_debit_orders_90d",
    "total_fees_90d",
    "credit_score_business",
    "credit_utilization_business",
    "arrears_days_bureau",
    "judgments_count",
    "num_credit_facilities",
    "director_credit_score",
    "director_credit_utilization",
    "director_judgments_count",
    "business_age_years",
    "num_directors",
]

REASON_CODES_PER_APPLICANT = 5

# Lending decision policy — kept identical to Stage 07 so applicants and
# the historical portfolio are treated under the same business rules.
LENDING_DECISION_POLICY = {
    "Very High Risk": {
        "lending_decision": "Decline",
        "indicative_pricing_tier": "N/A",
        "indicative_monthly_rate": "N/A",
        "facility_limit_guidance": "No facility offered",
        "monitoring_frequency": "N/A"
    },
    "High Risk": {
        "lending_decision": "Refer for manual underwriting",
        "indicative_pricing_tier": "Tier D",
        "indicative_monthly_rate": "5.5% - 7.0%",
        "facility_limit_guidance": (
            "Reduced limit, short tenor, with additional bureau/"
            "affordability checks"
        ),
        "monitoring_frequency": "Monthly"
    },
    "Moderate Risk": {
        "lending_decision": "Approve with conditions",
        "indicative_pricing_tier": "Tier C",
        "indicative_monthly_rate": "4.0% - 5.5%",
        "facility_limit_guidance": (
            "Standard limit with tighter covenant (e.g. minimum balance, "
            "revenue-linked repayment)"
        ),
        "monitoring_frequency": "Monthly"
    },
    "Low Risk": {
        "lending_decision": "Approve",
        "indicative_pricing_tier": "Tier B",
        "indicative_monthly_rate": "2.75% - 4.0%",
        "facility_limit_guidance": "Standard limit, standard tenor",
        "monitoring_frequency": "Quarterly"
    },
    "Very Low Risk": {
        "lending_decision": "Approve — preferred terms",
        "indicative_pricing_tier": "Tier A",
        "indicative_monthly_rate": "2.0% - 2.75%",
        "facility_limit_guidance": (
            "Higher limit eligible, longer tenor eligible"
        ),
        "monitoring_frequency": "Quarterly"
    }
}

# HEADER
print("=" * 80)
print("OREY ANALYTICS — FINANCIAL HEALTH SCORING")
print("08 — APPLICANT SCORING & REASON CODES")
print("=" * 80)

#===========================================================================
# CHECK REQUIRED FILES
#===========================================================================

print("\nChecking required files...")

if not POPULATION_MODEL_DIR.exists():
    raise FileNotFoundError(
        f"Population model folder not found: {POPULATION_MODEL_DIR}\n"
        "Expected it as a sibling of this phase's folder. If your "
        "population model folder has a different name, update "
        "POPULATION_MODEL_FOLDER_NAME at the top of this script."
    )

required_files = [
    APPLICANT_FILE,
    ENGINEERED_FILE,
    PREPROCESSED_FEATURE_LIST_FILE,
    WOE_BINNING_DEFINITIONS_FILE,
    WOE_MAPPINGS_FILE,
    SCORECARD_METADATA_FILE,
    SCORECARD_POINTS_FILE,
    MODEL_FILE,
    RISK_BAND_DEFINITIONS_FILE
]

for file in required_files:
    if not file.exists():
        raise FileNotFoundError(
            f"Required file not found: {file}"
        )

print("Required files confirmed.")

#===========================================================================
# LOAD SAVED PIPELINE ARTIFACTS
#===========================================================================

print("\nLoading saved pipeline artifacts...")

with open(SCORECARD_METADATA_FILE, "r", encoding="utf-8") as file:
    scorecard_metadata = json.load(file)

with open(WOE_BINNING_DEFINITIONS_FILE, "r", encoding="utf-8") as file:
    binning_metadata = json.load(file)

with open(WOE_MAPPINGS_FILE, "r", encoding="utf-8") as file:
    woe_mappings = json.load(file)

with open(MODEL_FILE, "rb") as file:
    model = pickle.load(file)

preprocessed_feature_list = pd.read_csv(
    PREPROCESSED_FEATURE_LIST_FILE
)

scorecard_points = pd.read_csv(SCORECARD_POINTS_FILE)

risk_band_definitions = pd.read_csv(RISK_BAND_DEFINITIONS_FILE)

selected_original_features = scorecard_metadata["selected_features"]
selected_woe_features = scorecard_metadata["selected_woe_features"]

score_min = float(scorecard_metadata["score_minimum"])
score_max = float(scorecard_metadata["score_maximum"])
scaling_factor = float(scorecard_metadata["score_scaling_factor"])
scaling_offset = float(scorecard_metadata["score_scaling_offset"])

feature_descriptions = {}

if FEATURE_METADATA_FILE.exists():
    feature_metadata_table = pd.read_csv(FEATURE_METADATA_FILE)

    feature_descriptions = dict(
        zip(
            feature_metadata_table["feature"],
            feature_metadata_table["description"]
        )
    )

print(
    f"Scorecard requires {len(selected_original_features)} "
    "final features."
)

band_bounds = {
    row["risk_band"]: (row["minimum_score"], row["maximum_score"])
    for _, row in risk_band_definitions.iterrows()
}


def assign_risk_band(score):
    for band in RISK_BAND_ORDER:
        minimum_score, maximum_score = band_bounds[band]
        if minimum_score <= score <= maximum_score:
            return band
    return "Unclassified"


#===========================================================================
# LOAD APPLICANT POPULATION
#===========================================================================

print("\n" + "=" * 80)
print("LOADING APPLICANT POPULATION")
print("=" * 80)

applicants = pd.read_csv(APPLICANT_FILE)

print(f"Applicant observations: {len(applicants):,}")

missing_raw_columns = [
    column
    for column in REQUIRED_RAW_COLUMNS
    if column not in applicants.columns
]

if missing_raw_columns:
    raise ValueError(
        "Applicant population is missing columns required to "
        f"reproduce Stage 02 feature engineering: {missing_raw_columns}"
    )

duplicate_applicants = int(
    applicants.duplicated(
        subset=["business_id", "snapshot_date"]
    ).sum()
)

if duplicate_applicants > 0:
    raise ValueError(
        f"{duplicate_applicants} duplicate business/snapshot rows "
        "detected in the applicant population."
    )

print("Required raw columns confirmed. No duplicate applicants detected.")

#===========================================================================
# FEATURE ENGINEERING (STAGE 02 CATEGORIES 1-9, REPLAYED)
#===========================================================================

print("\n" + "=" * 80)
print("APPLICANT FEATURE ENGINEERING")
print("=" * 80)

print(
    "\nReplaying Stage 02's non-transaction ratio and structure "
    "features. Transaction-level features are intentionally excluded, "
    "matching Stage 03's treatment of the primary scorecard."
)


def safe_divide(numerator, denominator):
    numerator = pd.to_numeric(numerator, errors="coerce")
    denominator = pd.to_numeric(denominator, errors="coerce")
    return numerator.div(denominator.replace(0, np.nan))


def engineer_core_features(df):
    """
    Reproduce Stage 02's categories 1-9 (cash-flow, liquidity, debt
    serviceability, profitability, leverage, operational distress,
    business bureau, director risk and business structure). Formulas
    are unchanged from Stage 02.
    """

    df = df.copy()

    # 1. Cash-flow stability
    df["fe_credit_volatility"] = df["credit_volatility_90d"]
    df["fe_cash_flow_trend"] = df["cash_flow_trend_90d"]
    df["fe_min_to_avg_balance"] = safe_divide(
        df["min_balance_90d"], df["avg_balance_90d"]
    )
    df["fe_weekly_credits_to_fixed_debits"] = safe_divide(
        df["avg_weekly_credits_90d"] * 4.33, df["fixed_monthly_debits"]
    )
    df["fe_credit_growth_90_vs_180"] = (
        safe_divide(df["total_credits_90d"] * 2, df["total_credits_180d"])
        - 1
    )
    df["fe_credit_growth_180_vs_365"] = (
        safe_divide(df["total_credits_180d"] * 2, df["total_credits_365d"])
        - 1
    )

    # 2. Liquidity
    df["fe_balance_to_monthly_expenses"] = safe_divide(
        df["avg_balance_90d"], df["monthly_expenses"]
    )
    df["fe_min_balance_to_expenses"] = safe_divide(
        df["min_balance_90d"], df["monthly_expenses"]
    )
    df["fe_negative_balance_frequency"] = (
        df["negative_balance_frequency_90d"]
    )
    df["fe_negative_balance_days"] = df["negative_balance_days_90d"]

    # 3. Debt serviceability
    df["fe_free_cash_after_fixed_debits"] = (
        df["free_cash_flow"] - df["fixed_monthly_debits"]
    )
    df["fe_free_cash_margin"] = safe_divide(
        df["free_cash_flow"], df["monthly_revenue"]
    )
    df["fe_fixed_debit_burden"] = safe_divide(
        df["fixed_monthly_debits"], df["monthly_revenue"]
    )
    df["fe_fixed_debits_to_credits"] = safe_divide(
        df["fixed_monthly_debits"], df["total_credits_90d"] / 3
    )
    df["fe_dscr"] = df["debt_service_coverage_ratio"]

    # 4. Profitability
    df["fe_operating_margin"] = safe_divide(
        df["monthly_revenue"] - df["monthly_expenses"], df["monthly_revenue"]
    )
    df["fe_expense_to_revenue"] = safe_divide(
        df["monthly_expenses"], df["monthly_revenue"]
    )
    df["fe_free_cash_to_expenses"] = safe_divide(
        df["free_cash_flow"], df["monthly_expenses"]
    )

    # 5. Balance sheet / leverage
    df["fe_debt_to_assets"] = safe_divide(
        df["total_liabilities"], df["total_assets"]
    )
    df["fe_debt_to_equity"] = safe_divide(
        df["total_liabilities"], df["total_equity"]
    )
    df["fe_equity_to_assets"] = safe_divide(
        df["total_equity"], df["total_assets"]
    )
    df["fe_liabilities_to_annual_revenue"] = safe_divide(
        df["total_liabilities"], df["annual_revenue"]
    )
    df["fe_debt_exposure_to_revenue"] = safe_divide(
        df["existing_debt_exposure"], df["annual_revenue"]
    )

    # 6. Operational distress
    df["fe_bounced_payment_count"] = df["num_bounced_payments_90d"]
    df["fe_reversed_transaction_count"] = (
        df["num_reversed_transactions_90d"]
    )
    df["fe_debit_order_count"] = df["num_debit_orders_90d"]
    df["fe_operational_distress_events"] = (
        df["num_bounced_payments_90d"] + df["num_reversed_transactions_90d"]
    )
    df["fe_distress_to_debit_orders"] = safe_divide(
        df["fe_operational_distress_events"], df["num_debit_orders_90d"]
    )
    df["fe_fees_to_credits"] = safe_divide(
        df["total_fees_90d"], df["total_credits_90d"]
    )

    # 7. Business bureau
    df["fe_business_credit_score"] = df["credit_score_business"]
    df["fe_business_credit_utilization"] = df["credit_utilization_business"]
    df["fe_business_arrears_days"] = df["arrears_days_bureau"]
    df["fe_business_judgments"] = df["judgments_count"]
    df["fe_business_credit_facilities"] = df["num_credit_facilities"]
    df["fe_bureau_debt_to_revenue"] = safe_divide(
        df["existing_debt_exposure"], df["annual_revenue"]
    )

    # 8. Director risk
    df["fe_director_credit_score"] = df["director_credit_score"]
    df["fe_director_credit_utilization"] = df["director_credit_utilization"]
    df["fe_director_judgments"] = df["director_judgments_count"]
    df["fe_business_vs_director_utilization"] = (
        df["credit_utilization_business"] - df["director_credit_utilization"]
    )

    # 9. Business structure
    df["fe_business_age"] = df["business_age_years"]
    df["fe_num_directors"] = df["num_directors"]
    df["fe_revenue_per_director"] = safe_divide(
        df["monthly_revenue"], df["num_directors"]
    )

    return df


applicants_engineered = engineer_core_features(applicants)

engineered_feature_count = sum(
    1
    for column in applicants_engineered.columns
    if column.startswith("fe_")
    and not column.startswith(TRANSACTION_FEATURE_PREFIX)
)

print(
    f"Non-transaction engineered features created: "
    f"{engineered_feature_count}"
)

#===========================================================================
# REBUILD TRAINING-CONSISTENT IMPUTATION VALUES
#===========================================================================

print("\n" + "=" * 80)
print("REBUILDING TRAINING-CONSISTENT IMPUTATION VALUES")
print("=" * 80)

print(
    "\nStage 03 fit numerical imputation on training data only, but did "
    "not persist the fitted median values. They are reconstructed here "
    "from the Stage 02 engineered panel using the identical filter, "
    "split and column-exclusion logic, and are therefore reproducible "
    "exactly."
)

engineered = pd.read_csv(ENGINEERED_FILE)

engineered_observable = engineered.loc[
    engineered["outcome_observable"] == True
].copy()

train_raw = engineered_observable.loc[
    engineered_observable["model_split"] == "train"
].copy()

print(f"Training observations reconstructed: {len(train_raw):,}")

transaction_columns_present = [
    column
    for column in train_raw.columns
    if column.startswith(TRANSACTION_FEATURE_PREFIX)
]

train_raw = train_raw.drop(
    columns=transaction_columns_present, errors="ignore"
)

columns_to_exclude = list(
    dict.fromkeys(ADMIN_COLUMNS + OUTCOME_COLUMNS)
)

train_raw = train_raw.drop(
    columns=[
        column for column in columns_to_exclude
        if column in train_raw.columns
    ],
    errors="ignore"
)

for column in MISSINGNESS_INDICATOR_COLUMNS:
    if column not in train_raw.columns:
        continue
    train_raw[f"{column}_missing"] = (
        train_raw[column].isna().astype(int)
    )

categorical_columns = [
    column for column in CATEGORICAL_COLUMNS if column in train_raw.columns
]

numeric_columns_train = [
    column
    for column in train_raw.columns
    if pd.api.types.is_numeric_dtype(train_raw[column])
    and column not in categorical_columns
]

training_medians = (
    train_raw[numeric_columns_train]
    .median(numeric_only=True)
)

print(
    f"Training medians reconstructed for "
    f"{training_medians.notna().sum()} numeric features."
)

#===========================================================================
# APPLY MISSINGNESS INDICATORS TO APPLICANTS
#===========================================================================

for column in MISSINGNESS_INDICATOR_COLUMNS:
    if column not in applicants_engineered.columns:
        continue
    applicants_engineered[f"{column}_missing"] = (
        applicants_engineered[column].isna().astype(int)
    )

#===========================================================================
# ALIGN TO FINAL PREPROCESSED FEATURE SCHEMA
#===========================================================================

print("\n" + "=" * 80)
print("ALIGNING TO FINAL PREPROCESSED FEATURE SCHEMA")
print("=" * 80)

final_feature_columns = preprocessed_feature_list["feature"].tolist()

final_categorical_columns = (
    preprocessed_feature_list
    .loc[
        preprocessed_feature_list["feature_type"] == "categorical",
        "feature"
    ]
    .tolist()
)

final_numeric_columns = (
    preprocessed_feature_list
    .loc[
        preprocessed_feature_list["feature_type"] == "numeric",
        "feature"
    ]
    .tolist()
)

missing_from_applicants = [
    column
    for column in final_feature_columns
    if column not in applicants_engineered.columns
]

if missing_from_applicants:
    raise ValueError(
        "Applicant feature engineering did not reproduce all required "
        f"model features: {missing_from_applicants}"
    )

applicants_model_ready = applicants_engineered[final_feature_columns].copy()

# Numeric imputation using reconstructed training medians
for column in final_numeric_columns:

    if column not in training_medians.index:
        raise ValueError(
            f"No reconstructed training median available for "
            f"required numeric feature: {column}"
        )

    applicants_model_ready[column] = applicants_model_ready[column].fillna(
        training_medians[column]
    )

# Categorical missingness treatment, matching Stage 03
for column in final_categorical_columns:
    applicants_model_ready[column] = (
        applicants_model_ready[column].fillna("Missing").astype(str)
    )

remaining_missing = int(
    applicants_model_ready[final_numeric_columns].isna().sum().sum()
)

if remaining_missing > 0:
    raise ValueError(
        f"{remaining_missing} missing numeric values remain after "
        "imputation. Applicant scoring cannot proceed."
    )

print("Applicant feature matrix aligned and imputed successfully.")

#===========================================================================
# WoE TRANSFORMATION (STAGE 04 ARTIFACTS, REPLAYED)
#===========================================================================

print("\n" + "=" * 80)
print("APPLYING TRAINED WoE TRANSFORMATION")
print("=" * 80)


def transform_applicants_to_woe(dataset, mappings, metadata, feature_list):
    """
    Apply Stage 04's saved bin edges and WoE mappings. No target
    information is used, and no bins or mappings are refit.
    """

    transformed = pd.DataFrame(index=dataset.index)

    for feature in feature_list:

        if feature not in metadata:
            raise ValueError(
                f"No saved WoE binning definition found for "
                f"required feature: {feature}"
            )

        values = dataset[feature]
        feature_metadata = metadata[feature]
        feature_type = feature_metadata["type"]

        if feature_type == "quantile":
            bin_edges = feature_metadata["bin_edges"]
            bins = pd.cut(values, bins=bin_edges, include_lowest=True)
            bins = bins.astype(object)
            bins[values.isna()] = "MISSING"
            bins = bins.astype(str)
        else:
            bins = (
                values.where(values.notna(), "MISSING").astype(str)
            )

        mapping = mappings[feature]
        transformed_values = bins.map(mapping)

        unseen_count = int(transformed_values.isna().sum())

        if unseen_count > 0:
            print(
                f"  {feature}: {unseen_count:,} applicant values fell "
                "outside the training bins and received neutral WoE."
            )

        transformed_values = transformed_values.fillna(0.0)

        transformed[f"woe_{feature}"] = transformed_values.astype(float)

    return transformed


applicants_woe = transform_applicants_to_woe(
    applicants_model_ready,
    woe_mappings,
    binning_metadata,
    selected_original_features
)

missing_woe_columns = [
    column
    for column in selected_woe_features
    if column not in applicants_woe.columns
]

if missing_woe_columns:
    raise ValueError(
        f"WoE transformation did not produce required columns: "
        f"{missing_woe_columns}"
    )

X_applicants = applicants_woe[selected_woe_features].copy()

if X_applicants.isna().sum().sum() > 0:
    raise ValueError(
        "Missing values detected in the applicant WoE feature matrix."
    )

print(
    f"\nApplicant WoE feature matrix ready: {X_applicants.shape}"
)

#===========================================================================
# SCORE APPLICANTS
#===========================================================================

print("\n" + "=" * 80)
print("SCORING APPLICANTS")
print("=" * 80)

applicant_probability = model.predict_proba(X_applicants)[:, 1]


def probability_to_score(probability):
    probability = np.clip(probability, 1e-6, 1 - 1e-6)
    odds = (1 - probability) / probability
    score = scaling_offset + scaling_factor * np.log(odds)
    return np.clip(score, score_min, score_max)


applicant_score = probability_to_score(applicant_probability)

print(
    f"Applicant score range: "
    f"minimum={applicant_score.min():.0f}, "
    f"median={np.median(applicant_score):.0f}, "
    f"maximum={applicant_score.max():.0f}"
)

#===========================================================================
# BUILD APPLICANT ASSESSMENT
#===========================================================================

applicant_assessment = applicants_engineered[IDENTIFIER_COLUMNS].copy()

applicant_assessment[PROBABILITY_COLUMN] = applicant_probability
applicant_assessment[SCORE_COLUMN] = (
    applicant_score.round().astype(int)
)

applicant_assessment["risk_band"] = (
    applicant_assessment[SCORE_COLUMN].apply(assign_risk_band)
)

unclassified = int(
    (applicant_assessment["risk_band"] == "Unclassified").sum()
)

if unclassified > 0:
    raise ValueError(
        f"{unclassified} applicants fell outside the defined risk-band "
        "ranges. Risk-band assignment cannot be accepted."
    )

applicant_assessment["risk_band"] = pd.Categorical(
    applicant_assessment["risk_band"],
    categories=RISK_BAND_ORDER,
    ordered=True
)

decision_policy_df = pd.DataFrame(
    [
        {"risk_band": band, **policy}
        for band, policy in LENDING_DECISION_POLICY.items()
    ]
)

decision_policy_df["risk_band"] = pd.Categorical(
    decision_policy_df["risk_band"], categories=RISK_BAND_ORDER, ordered=True
)

applicant_assessment = applicant_assessment.merge(
    decision_policy_df, on="risk_band", how="left", validate="many_to_one"
)

#===========================================================================
# REASON CODES
#===========================================================================

print("\n" + "=" * 80)
print("GENERATING REASON CODES")
print("=" * 80)

print(
    "\nPer-applicant point contributions are derived directly from the "
    "fitted scorecard's own points table (points_at_woe_1 x the "
    "applicant's WoE value for that feature). Positive contributions "
    "are protective (raise the score); negative contributions are "
    "adverse (lower the score)."
)

points_lookup = scorecard_points.set_index("feature")

reason_records = []

for row_position, business_id in enumerate(
    applicant_assessment["business_id"]
):

    contributions = []

    for feature in selected_original_features:

        woe_column = f"woe_{feature}"
        woe_value = X_applicants.iloc[row_position][woe_column]

        points_at_woe_1 = float(
            points_lookup.loc[feature, "points_at_woe_1"]
        )

        contribution = points_at_woe_1 * woe_value

        contributions.append(
            {
                "feature": feature,
                "woe_value": float(woe_value),
                "point_contribution": float(contribution)
            }
        )

    contributions_df = pd.DataFrame(contributions).sort_values(
        "point_contribution"
    )

    adverse_factors = contributions_df.head(REASON_CODES_PER_APPLICANT)
    protective_factors = (
        contributions_df.tail(REASON_CODES_PER_APPLICANT).iloc[::-1]
    )

    for rank, (_, factor_row) in enumerate(
        adverse_factors.iterrows(), start=1
    ):
        reason_records.append(
            {
                "business_id": business_id,
                "reason_type": "adverse",
                "rank": rank,
                "feature": factor_row["feature"],
                "description": feature_descriptions.get(
                    factor_row["feature"], ""
                ),
                "point_contribution": factor_row["point_contribution"]
            }
        )

    for rank, (_, factor_row) in enumerate(
        protective_factors.iterrows(), start=1
    ):
        reason_records.append(
            {
                "business_id": business_id,
                "reason_type": "protective",
                "rank": rank,
                "feature": factor_row["feature"],
                "description": feature_descriptions.get(
                    factor_row["feature"], ""
                ),
                "point_contribution": factor_row["point_contribution"]
            }
        )

reason_codes = pd.DataFrame(reason_records)

print(
    f"Reason codes generated for {applicant_assessment.shape[0]:,} "
    f"applicants ({REASON_CODES_PER_APPLICANT} adverse + "
    f"{REASON_CODES_PER_APPLICANT} protective factors each)."
)

#===========================================================================
# PORTFOLIO-LEVEL APPLICANT SUMMARY
#===========================================================================

print("\n" + "=" * 80)
print("APPLICANT RISK BAND SUMMARY")
print("=" * 80)

applicant_band_summary = (
    applicant_assessment
    .groupby("risk_band", observed=False)
    .agg(
        applicants=("business_id", "size"),
        mean_score=(SCORE_COLUMN, "mean"),
        mean_predicted_probability=(PROBABILITY_COLUMN, "mean")
    )
    .reindex(RISK_BAND_ORDER)
    .reset_index()
)

applicant_band_summary["population_share"] = (
    applicant_band_summary["applicants"] / len(applicant_assessment)
)

print(applicant_band_summary.to_string(index=False))

decision_summary = (
    applicant_assessment
    .groupby("lending_decision", observed=False)
    .agg(applicants=("business_id", "size"))
    .reset_index()
)

decision_summary["population_share"] = (
    decision_summary["applicants"] / len(applicant_assessment)
)

print("\nApplicant lending decision summary:")
print(decision_summary.to_string(index=False))

#===========================================================================
# SAVE OUTPUTS
#===========================================================================

print("\n" + "=" * 80)
print("SAVING OUTPUTS")
print("=" * 80)

applicant_assessment.to_csv(
    OUTPUT_DIR / "applicant_scored_population.csv", index=False
)

reason_codes.to_csv(
    OUTPUT_DIR / "applicant_reason_codes.csv", index=False
)

applicant_band_summary.to_csv(
    OUTPUT_DIR / "applicant_risk_band_summary.csv", index=False
)

decision_summary.to_csv(
    OUTPUT_DIR / "applicant_lending_decision_summary.csv", index=False
)

applicant_scoring_metadata = {
    "stage": "08_applicant_scoring_and_reason_codes",
    "applicants_scored": int(len(applicant_assessment)),
    "final_features_used": selected_original_features,
    "number_of_final_features": len(selected_original_features),
    "score_minimum": score_min,
    "score_maximum": score_max,
    "reason_codes_per_applicant": REASON_CODES_PER_APPLICANT,
    "unseen_value_handling": (
        "Applicant values falling outside the training-derived bins "
        "received neutral WoE (0.0), matching Stage 04's treatment of "
        "unseen validation/test categories."
    ),
    "imputation_rule": (
        "Numeric features were imputed using training medians "
        "reconstructed from the Stage 02 engineered panel's training "
        "split, replaying Stage 03's exact filter and column logic. "
        "Categorical features were filled with 'Missing', matching "
        "Stage 03."
    ),
    "reason_code_methodology": (
        "Per-feature point contribution = points_at_woe_1 x the "
        "applicant's WoE value for that feature, using Stage 05's "
        "scorecard_feature_points.csv. Contributions are ranked per "
        "applicant to surface the largest adverse (score-reducing) and "
        "protective (score-increasing) factors."
    ),
    "no_retraining_performed": True
}

with open(
    OUTPUT_DIR / "applicant_scoring_metadata.json", "w", encoding="utf-8"
) as file:
    json.dump(applicant_scoring_metadata, file, indent=4, default=str)

# COMPLETION
print("\n" + "=" * 80)
print("APPLICANT SCORING & REASON CODES COMPLETE")
print("=" * 80)

print(f"\nApplicants scored: {len(applicant_assessment):,}")

print("\nOutputs saved to:")
print(OUTPUT_DIR)

print("\nGenerated files:")
print("  - applicant_scored_population.csv")
print("  - applicant_reason_codes.csv")
print("  - applicant_risk_band_summary.csv")
print("  - applicant_lending_decision_summary.csv")
print("  - applicant_scoring_metadata.json")

print("\nSource datasets and upstream stage outputs were not modified.")

print("\nNext stage:")
print(
    "09 — Score monitoring: track applicant score distribution and "
    "population stability against the training population over time "
    "(PSI / characteristic stability)."
)