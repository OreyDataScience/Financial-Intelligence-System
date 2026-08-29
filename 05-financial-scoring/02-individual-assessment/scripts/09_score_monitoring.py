"""
Orey Analytics
Financial Health Scoring — Individual Assessment

Stage 09 — Score Monitoring: Population Stability & Characteristic Shift

Purpose:
Compare the applicant population scored in Stage 08 against the training
population the scorecard was built on, at two levels:

    1. Score-level Population Stability Index (PSI) — has the overall
       score distribution drifted from what the model was trained on?
    2. Feature-level Characteristic Stability Index (CSI) — which
       individual features are driving that drift, if any?

This stage does not retrain, re-bin, or re-fit anything. It only measures
distributional distance between two populations that were already scored
using the same fixed artifacts (WoE bins, scorecard, risk bands).

Why this is needed:
    Stage 04 computed bin-level training population shares internally but
    did not persist them (only feature/bin/WoE/IV were saved to
    woe_bin_audit.csv). Stage 09 therefore reconstructs the training
    population's raw feature values and bin assignments from the Stage 02
    engineered panel's training split — replaying the identical feature
    engineering and bin-edge logic used in Stages 02 and 04 — and compares
    them against the applicant population's own bin assignments.

Key principles:
    1. No model, bin edges or WoE values are refit. Stage 04's saved bin
       edges (woe_binning_definitions.json) are the single source of
       truth for how any value — training or applicant — is binned.
    2. PSI/CSI are computed against the TRAINING population specifically
       (not validation/test), since training is the population the model's
       bins and coefficients were fitted on — the correct stability
       baseline.
    3. Standard credit-risk interpretation thresholds are applied:
           PSI/CSI < 0.10            : no significant shift
           0.10 <= PSI/CSI < 0.25    : moderate shift — monitor
           PSI/CSI >= 0.25           : material shift — investigate/
                                        consider recalibration
    4. Source datasets and upstream stage outputs are never modified.

Folder layout:
    Lives alongside Stage 08 in 02-individual-assessment. Reads Stage
    01-07 artifacts from the sibling 01-population-model folder, and
    Stage 08's own applicant_scored_population.csv from this phase's
    outputs folder.
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
ASSESSMENT_DIR = SCRIPT_DIR.parent
PHASE_DIR = ASSESSMENT_DIR.parent

POPULATION_MODEL_FOLDER_NAME = "01-population-model"
POPULATION_MODEL_DIR = PHASE_DIR / POPULATION_MODEL_FOLDER_NAME
POPULATION_OUTPUT_DIR = POPULATION_MODEL_DIR / "outputs"

DATA_DIR = ASSESSMENT_DIR / "data"
OUTPUT_DIR = ASSESSMENT_DIR / "outputs"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

APPLICANT_FILE = DATA_DIR / "sme applicant scoring population.csv"
APPLICANT_SCORED_FILE = OUTPUT_DIR / "applicant_scored_population.csv"

ENGINEERED_FILE = (
    POPULATION_OUTPUT_DIR / "financial_health_panel_engineered.csv"
)
WOE_BINNING_DEFINITIONS_FILE = (
    POPULATION_OUTPUT_DIR / "woe_binning_definitions.json"
)
SCORECARD_METADATA_FILE = (
    POPULATION_OUTPUT_DIR / "scorecard_metadata.json"
)
TRAIN_SCORE_FILE = POPULATION_OUTPUT_DIR / "model_train_scores.csv"
RISK_BAND_DEFINITIONS_FILE = (
    POPULATION_OUTPUT_DIR / "risk_band_definitions.csv"
)

# CONFIGURATION
TARGET = "default_event_12m"
SCORE_COLUMN = "orey_financial_health_score"

ADMIN_COLUMNS = [
    "business_id", "snapshot_date", "bureau_snapshot_date",
    "observation_seq", "outcome_observable", "outcome_window_end",
    "model_split", "default_type", "default_date",
]
OUTCOME_COLUMNS = [TARGET]
TRANSACTION_FEATURE_PREFIX = "fe_transaction_"

RISK_BAND_ORDER = [
    "Very High Risk", "High Risk", "Moderate Risk",
    "Low Risk", "Very Low Risk"
]

REQUIRED_RAW_COLUMNS = [
    "business_id", "snapshot_date", "province", "industry_sector",
    "legal_entity_type", "credit_volatility_90d", "cash_flow_trend_90d",
    "min_balance_90d", "avg_balance_90d", "avg_weekly_credits_90d",
    "fixed_monthly_debits", "total_credits_90d", "total_credits_180d",
    "total_credits_365d", "monthly_expenses",
    "negative_balance_frequency_90d", "negative_balance_days_90d",
    "free_cash_flow", "monthly_revenue", "debt_service_coverage_ratio",
    "total_liabilities", "total_assets", "total_equity", "annual_revenue",
    "existing_debt_exposure", "num_bounced_payments_90d",
    "num_reversed_transactions_90d", "num_debit_orders_90d",
    "total_fees_90d", "num_fees_90d", "default_flag_bureau_history",
    "credit_score_business", "credit_utilization_business",
    "arrears_days_bureau", "judgments_count", "num_credit_facilities",
    "director_credit_score", "director_credit_utilization",
    "director_judgments_count", "business_age_years", "num_directors",
]

N_SCORE_BINS = 10
EPSILON = 1e-4  # floor for zero-population bins to keep PSI/log defined

PSI_MODERATE_THRESHOLD = 0.10
PSI_MATERIAL_THRESHOLD = 0.25

# HEADER
print("=" * 80)
print("OREY ANALYTICS — FINANCIAL HEALTH SCORING")
print("09 — SCORE MONITORING: POPULATION STABILITY & CHARACTERISTIC SHIFT")
print("=" * 80)

# CHECK REQUIRED FILES
print("\nChecking required files...")

if not POPULATION_MODEL_DIR.exists():
    raise FileNotFoundError(
        f"Population model folder not found: {POPULATION_MODEL_DIR}"
    )

required_files = [
    APPLICANT_FILE, APPLICANT_SCORED_FILE, ENGINEERED_FILE,
    WOE_BINNING_DEFINITIONS_FILE, SCORECARD_METADATA_FILE,
    TRAIN_SCORE_FILE, RISK_BAND_DEFINITIONS_FILE,
]

for file in required_files:
    if not file.exists():
        raise FileNotFoundError(f"Required file not found: {file}")

print("Required files confirmed.")

if not APPLICANT_SCORED_FILE.exists():
    raise FileNotFoundError(
        "applicant_scored_population.csv not found. Run Stage 08 first."
    )

# LOAD ARTIFACTS
print("\nLoading saved pipeline artifacts...")

with open(WOE_BINNING_DEFINITIONS_FILE, "r", encoding="utf-8") as file:
    binning_metadata = json.load(file)

with open(SCORECARD_METADATA_FILE, "r", encoding="utf-8") as file:
    scorecard_metadata = json.load(file)

selected_original_features = scorecard_metadata["selected_features"]

risk_band_definitions = pd.read_csv(RISK_BAND_DEFINITIONS_FILE)
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


print(f"Monitoring {len(selected_original_features)} scorecard features.")

# FEATURE ENGINEERING (STAGE 02 CATEGORIES 1-9, REPLAYED)
print("\n" + "=" * 80)
print("REPLAYING FEATURE ENGINEERING")
print("=" * 80)


def safe_divide(numerator, denominator):
    numerator = pd.to_numeric(numerator, errors="coerce")
    denominator = pd.to_numeric(denominator, errors="coerce")
    return numerator.div(denominator.replace(0, np.nan))


def engineer_core_features(df):
    """Reproduce Stage 02's categories 1-9. Formulas unchanged."""

    df = df.copy()

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
    df["fe_operating_margin"] = safe_divide(
        df["monthly_revenue"] - df["monthly_expenses"], df["monthly_revenue"]
    )
    df["fe_expense_to_revenue"] = safe_divide(
        df["monthly_expenses"], df["monthly_revenue"]
    )
    df["fe_free_cash_to_expenses"] = safe_divide(
        df["free_cash_flow"], df["monthly_expenses"]
    )
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
    df["fe_business_credit_score"] = df["credit_score_business"]
    df["fe_business_credit_utilization"] = df["credit_utilization_business"]
    df["fe_business_arrears_days"] = df["arrears_days_bureau"]
    df["fe_business_judgments"] = df["judgments_count"]
    df["fe_business_credit_facilities"] = df["num_credit_facilities"]
    df["fe_bureau_debt_to_revenue"] = safe_divide(
        df["existing_debt_exposure"], df["annual_revenue"]
    )
    df["fe_director_credit_score"] = df["director_credit_score"]
    df["fe_director_credit_utilization"] = df["director_credit_utilization"]
    df["fe_director_judgments"] = df["director_judgments_count"]
    df["fe_business_vs_director_utilization"] = (
        df["credit_utilization_business"] - df["director_credit_utilization"]
    )
    df["fe_business_age"] = df["business_age_years"]
    df["fe_num_directors"] = df["num_directors"]
    df["fe_revenue_per_director"] = safe_divide(
        df["monthly_revenue"], df["num_directors"]
    )

    return df


# LOAD APPLICANT RAW DATA AND STAGE 08 SCORES
applicants_raw = pd.read_csv(APPLICANT_FILE)

missing_raw_columns = [
    column for column in REQUIRED_RAW_COLUMNS
    if column not in applicants_raw.columns
]

if missing_raw_columns:
    raise ValueError(
        f"Applicant population is missing columns: {missing_raw_columns}"
    )

applicants_engineered = engineer_core_features(applicants_raw)

applicant_scored = pd.read_csv(APPLICANT_SCORED_FILE)

if len(applicant_scored) != len(applicants_engineered):
    raise ValueError(
        "Row count mismatch between the raw applicant file "
        f"({len(applicants_engineered)}) and Stage 08's scored output "
        f"({len(applicant_scored)}). These must be the same run."
    )

print(f"Applicants for monitoring: {len(applicant_scored):,}")

# RECONSTRUCT TRAINING RAW FEATURE VALUES
print("\n" + "=" * 80)
print("RECONSTRUCTING TRAINING POPULATION")
print("=" * 80)

print(
    "\nStage 04's bin-level training population shares were computed "
    "internally but not persisted, so they are rebuilt here from the "
    "Stage 02 engineered panel's training split."
)

engineered = pd.read_csv(ENGINEERED_FILE)

train_raw = engineered.loc[
    (engineered["outcome_observable"] == True)
    & (engineered["model_split"] == "train")
].copy()

print(f"Training observations reconstructed: {len(train_raw):,}")

missing_from_train = [
    feature for feature in selected_original_features
    if feature not in train_raw.columns
]

if missing_from_train:
    raise ValueError(
        "Selected scorecard features missing from the engineered "
        f"panel's training split: {missing_from_train}"
    )

# BIN ASSIGNMENT (SHARED LOGIC — TRAINING AND APPLICANT)
print("\n" + "=" * 80)
print("ASSIGNING BINS USING STAGE 04'S SAVED DEFINITIONS")
print("=" * 80)


def assign_bins(values, feature_metadata):
    """
    Assign each value to its Stage 04 bin label. No bins are refit —
    this uses the saved bin edges/type exactly as Stage 04 defined them.
    """

    feature_type = feature_metadata["type"]

    if feature_type == "quantile":
        bin_edges = feature_metadata["bin_edges"]
        bins = pd.cut(values, bins=bin_edges, include_lowest=True)
        bins = bins.astype(object)
        bins[values.isna()] = "MISSING"
        return bins.astype(str)

    return values.where(values.notna(), "MISSING").astype(str)


def bin_population_shares(dataset, feature_list, metadata):
    """Return {feature: {bin_label: population_share}} for a dataset."""

    shares = {}

    for feature in feature_list:

        if feature not in metadata:
            raise ValueError(
                f"No saved WoE binning definition for feature: {feature}"
            )

        bins = assign_bins(dataset[feature], metadata[feature])

        counts = bins.value_counts()
        shares[feature] = (counts / counts.sum()).to_dict()

    return shares


train_bin_shares = bin_population_shares(
    train_raw, selected_original_features, binning_metadata
)

applicant_bin_shares = bin_population_shares(
    applicants_engineered, selected_original_features, binning_metadata
)

print(
    f"Bin population shares computed for "
    f"{len(selected_original_features)} features "
    "(training and applicant)."
)


# PSI CALCULATION
def calculate_psi(expected_shares, actual_shares):
    """
    Standard PSI: sum((actual% - expected%) * ln(actual% / expected%))
    over the union of bins. Zero-population bins are floored at EPSILON
    to keep the log defined — this is the conventional treatment, and
    means PSI for a bin that only appears in one population is bounded
    rather than infinite.
    """

    all_bins = set(expected_shares) | set(actual_shares)

    psi = 0.0
    bin_details = []

    for bin_label in sorted(all_bins, key=str):

        expected_pct = max(expected_shares.get(bin_label, 0.0), EPSILON)
        actual_pct = max(actual_shares.get(bin_label, 0.0), EPSILON)

        bin_psi = (actual_pct - expected_pct) * np.log(
            actual_pct / expected_pct
        )

        psi += bin_psi

        bin_details.append(
            {
                "bin": bin_label,
                "training_pct": expected_shares.get(bin_label, 0.0),
                "applicant_pct": actual_shares.get(bin_label, 0.0),
                "bin_psi_contribution": bin_psi
            }
        )

    return psi, bin_details


def interpret_stability(value):
    if value < PSI_MODERATE_THRESHOLD:
        return "Stable"
    elif value < PSI_MATERIAL_THRESHOLD:
        return "Moderate shift — monitor"
    else:
        return "Material shift — investigate"


# FEATURE-LEVEL CSI
print("\n" + "=" * 80)
print("CHARACTERISTIC STABILITY INDEX (CSI) BY FEATURE")
print("=" * 80)

csi_records = []
csi_bin_detail_records = []

for feature in selected_original_features:

    csi, bin_details = calculate_psi(
        train_bin_shares[feature], applicant_bin_shares[feature]
    )

    csi_records.append(
        {
            "feature": feature,
            "csi": csi,
            "stability": interpret_stability(csi),
            "training_bins": len(train_bin_shares[feature]),
            "applicant_bins": len(applicant_bin_shares[feature])
        }
    )

    for detail in bin_details:
        detail["feature"] = feature
        csi_bin_detail_records.append(detail)

csi_summary = (
    pd.DataFrame(csi_records)
    .sort_values("csi", ascending=False)
    .reset_index(drop=True)
)

csi_bin_detail = pd.DataFrame(csi_bin_detail_records)[
    ["feature", "bin", "training_pct", "applicant_pct",
     "bin_psi_contribution"]
]

print(csi_summary.to_string(index=False))

material_shift_features = csi_summary.loc[
    csi_summary["csi"] >= PSI_MATERIAL_THRESHOLD, "feature"
].tolist()

moderate_shift_features = csi_summary.loc[
    (csi_summary["csi"] >= PSI_MODERATE_THRESHOLD)
    & (csi_summary["csi"] < PSI_MATERIAL_THRESHOLD),
    "feature"
].tolist()

if material_shift_features:
    print(
        f"\nWARNING: {len(material_shift_features)} feature(s) show "
        f"material distributional shift (CSI >= {PSI_MATERIAL_THRESHOLD}): "
        f"{material_shift_features}"
    )

if moderate_shift_features:
    print(
        f"\n{len(moderate_shift_features)} feature(s) show moderate "
        f"shift and are worth monitoring: {moderate_shift_features}"
    )

# SCORE-LEVEL PSI
print("\n" + "=" * 80)
print("SCORE-LEVEL POPULATION STABILITY INDEX (PSI)")
print("=" * 80)

train_scores = pd.read_csv(TRAIN_SCORE_FILE)

if SCORE_COLUMN not in train_scores.columns:
    raise ValueError(
        f"{SCORE_COLUMN} not found in {TRAIN_SCORE_FILE}"
    )

print(
    f"\nBuilding {N_SCORE_BINS} score bins from the training score "
    "distribution (the model's fitted baseline)..."
)

train_score_values = train_scores[SCORE_COLUMN].dropna()

_, score_bin_edges = pd.qcut(
    train_score_values, q=N_SCORE_BINS, retbins=True, duplicates="drop"
)

score_bin_edges = score_bin_edges.copy()
score_bin_edges[0] = -np.inf
score_bin_edges[-1] = np.inf

actual_bin_count = len(score_bin_edges) - 1

if actual_bin_count < N_SCORE_BINS:
    print(
        f"Note: training scores only support {actual_bin_count} distinct "
        f"bins (requested {N_SCORE_BINS}) due to repeated score values."
    )


def score_bin_shares(scores, edges):
    bins = pd.cut(scores, bins=edges, include_lowest=True)
    counts = bins.value_counts()
    return (counts / counts.sum()).to_dict()


train_score_shares = score_bin_shares(train_score_values, score_bin_edges)
applicant_score_shares = score_bin_shares(
    applicant_scored[SCORE_COLUMN], score_bin_edges
)

score_psi, score_bin_details = calculate_psi(
    train_score_shares, applicant_score_shares
)

score_psi_bin_detail = pd.DataFrame(score_bin_details).sort_values(
    "bin", key=lambda col: col.astype(str)
)

print(f"\nOverall score PSI: {score_psi:.4f}")
print(f"Interpretation: {interpret_stability(score_psi)}")
print("\nScore bin detail:")
print(score_psi_bin_detail.to_string(index=False))

# RISK BAND MIX COMPARISON
print("\n" + "=" * 80)
print("RISK BAND MIX — TRAINING VS APPLICANT POPULATION")
print("=" * 80)

train_scores["risk_band"] = train_scores[SCORE_COLUMN].apply(
    assign_risk_band
)

train_band_mix = (
    train_scores["risk_band"].value_counts(normalize=True)
    .reindex(RISK_BAND_ORDER)
    .fillna(0.0)
)

applicant_band_mix = (
    applicant_scored["risk_band"].value_counts(normalize=True)
    .reindex(RISK_BAND_ORDER)
    .fillna(0.0)
)

band_mix_comparison = pd.DataFrame(
    {
        "risk_band": RISK_BAND_ORDER,
        "training_share": train_band_mix.values,
        "applicant_share": applicant_band_mix.values,
    }
)

band_mix_comparison["share_difference"] = (
    band_mix_comparison["applicant_share"]
    - band_mix_comparison["training_share"]
)

print(band_mix_comparison.to_string(index=False))

# SAVE OUTPUTS
print("\n" + "=" * 80)
print("SAVING MONITORING OUTPUTS")
print("=" * 80)

csi_summary.to_csv(
    OUTPUT_DIR / "feature_csi_summary.csv", index=False
)

csi_bin_detail.to_csv(
    OUTPUT_DIR / "feature_csi_bin_detail.csv", index=False
)

score_psi_bin_detail.rename(columns={"bin": "score_bin"}).to_csv(
    OUTPUT_DIR / "score_psi_bin_detail.csv", index=False
)

band_mix_comparison.to_csv(
    OUTPUT_DIR / "risk_band_mix_comparison.csv", index=False
)

monitoring_metadata = {
    "stage": "09_score_monitoring",
    "applicants_monitored": int(len(applicant_scored)),
    "training_population_size": int(len(train_raw)),
    "score_psi": float(score_psi),
    "score_psi_interpretation": interpret_stability(score_psi),
    "score_bin_edges": [
        float(edge) for edge in score_bin_edges
    ],
    "features_monitored": len(selected_original_features),
    "features_material_shift": material_shift_features,
    "features_moderate_shift": moderate_shift_features,
    "psi_thresholds": {
        "stable_below": PSI_MODERATE_THRESHOLD,
        "moderate_below": PSI_MATERIAL_THRESHOLD,
        "material_at_or_above": PSI_MATERIAL_THRESHOLD
    },
    "baseline_population": (
        "Training split only (the population the scorecard's bins and "
        "coefficients were fitted on), not validation or test."
    ),
    "methodology": (
        "PSI/CSI = sum((actual_pct - expected_pct) * "
        "ln(actual_pct / expected_pct)) over Stage 04's saved bins. "
        "No bins, mappings or model parameters were refit."
    ),
    "no_retraining_performed": True
}

with open(
    OUTPUT_DIR / "score_monitoring_metadata.json", "w", encoding="utf-8"
) as file:
    json.dump(monitoring_metadata, file, indent=4, default=str)

# COMPLETION
print("\n" + "=" * 80)
print("SCORE MONITORING COMPLETE")
print("=" * 80)

print(f"\nOverall score PSI: {score_psi:.4f} ({interpret_stability(score_psi)})")
print(f"Features with material shift: {len(material_shift_features)}")
print(f"Features with moderate shift: {len(moderate_shift_features)}")

print("\nOutputs saved to:")
print(OUTPUT_DIR)

print("\nGenerated files:")
print("  - feature_csi_summary.csv")
print("  - feature_csi_bin_detail.csv")
print("  - score_psi_bin_detail.csv")
print("  - risk_band_mix_comparison.csv")
print("  - score_monitoring_metadata.json")

print("\nSource datasets and upstream stage outputs were not modified.")

print("\nNext stage:")
print(
    "10 — Recalibration trigger review: if PSI/CSI breach thresholds "
    "across consecutive monitoring runs, escalate for model review."
)