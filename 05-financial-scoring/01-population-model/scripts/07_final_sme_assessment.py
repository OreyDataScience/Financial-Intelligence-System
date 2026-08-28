"""
Orey Analytics
Financial Health Scoring — Population Model

Stage 07 — Final Orey Financial Health Score & SME Assessment

Purpose:
Take the Stage 05 scorecard outputs and the Stage 06 validation decision and
turn them into a finished, business-facing product:

    1. Re-attach business identifiers to the train/validation/test scores
       (identifiers were intentionally excluded from the modelling matrices
       in Stage 03 to keep them out of the model, but are required again now
       for reporting and for handing scores back to underwriters).
    2. Apply the empirically-derived risk bands from Stage 06 consistently
       across the full scored population.
    3. Translate risk bands into an indicative lending decision and pricing
       tier — the layer alternative lenders actually act on.
    4. Summarise the scored portfolio (by risk band, province, industry and
       model split) for monitoring and reporting.
    5. Produce one consolidated "Orey Financial Health Assessment" file per
       SME observation, and a model card documenting the full pipeline for
       governance and audit.

Key principles:
    1. No model is retrained here. Stage 05's scorecard and Stage 06's
       validated risk bands are used as-is.
    2. The Stage 06 model_validation_pass decision gates whether this stage's
       outputs are flagged as approved for production decisioning.
    3. Identifiers are re-attached using a position-based join back to the
       Stage 02 engineered panel, filtered and split exactly as Stage 03 did.
       This is verified before use — row counts and target values must match
       between the reconstructed identifiers and the Stage 05 score files,
       or the script stops rather than risk a silent mis-join.
    4. Source datasets and upstream stage outputs are never modified.
    5. The lending decision policy (bands -> decisions -> pricing tiers) is
       an explicit, editable business-rules layer, kept separate from the
       statistical model so it can be revised without retraining.
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

ENGINEERED_FILE = OUTPUT_DIR / "financial_health_panel_engineered.csv"

TRAIN_SCORE_FILE = OUTPUT_DIR / "model_train_scores.csv"
VALIDATION_SCORE_FILE = OUTPUT_DIR / "model_validation_scores.csv"
TEST_SCORE_FILE = OUTPUT_DIR / "model_test_scores.csv"

RISK_BAND_DEFINITIONS_FILE = OUTPUT_DIR / "risk_band_definitions.csv"
VALIDATION_METADATA_FILE = OUTPUT_DIR / "model_validation_metadata.json"
SCORECARD_METADATA_FILE = OUTPUT_DIR / "scorecard_metadata.json"

# CONFIGURATION
TARGET = "default_event_12m"
PROBABILITY_COLUMN = "predicted_default_probability"
SCORE_COLUMN = "orey_financial_health_score"

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

# LENDING DECISION POLICY
# This is a business-rules layer sitting on top of the statistical model.
# Bands and cutoffs come from Stage 06; decisions and pricing tiers are
# Orey Analytics' indicative policy and are intentionally easy to revise
# without touching the model itself.
LENDING_DECISION_POLICY = {
    "Very High Risk": {
        "lending_decision": "Decline",
        "indicative_pricing_tier": "N/A",
        "indicative_monthly_rate": "N/A",
        "facility_limit_guidance": "No facility offered",
        "monitoring_frequency": "N/A",
        "rationale": (
            "Score falls in the lowest empirical band, where observed "
            "default rates are highest and materially above portfolio "
            "average."
        )
    },
    "High Risk": {
        "lending_decision": "Refer for manual underwriting",
        "indicative_pricing_tier": "Tier D",
        "indicative_monthly_rate": "5.5% - 7.0%",
        "facility_limit_guidance": (
            "Reduced limit, short tenor, with additional bureau/"
            "affordability checks"
        ),
        "monitoring_frequency": "Monthly",
        "rationale": (
            "Elevated observed default rate. Suitable for manual review "
            "with compensating controls rather than automatic approval "
            "or decline."
        )
    },
    "Moderate Risk": {
        "lending_decision": "Approve with conditions",
        "indicative_pricing_tier": "Tier C",
        "indicative_monthly_rate": "4.0% - 5.5%",
        "facility_limit_guidance": (
            "Standard limit with tighter covenant (e.g. minimum balance, "
            "revenue-linked repayment)"
        ),
        "monitoring_frequency": "Monthly",
        "rationale": (
            "Around portfolio-average risk. Approvable with standard "
            "affordability-linked conditions."
        )
    },
    "Low Risk": {
        "lending_decision": "Approve",
        "indicative_pricing_tier": "Tier B",
        "indicative_monthly_rate": "2.75% - 4.0%",
        "facility_limit_guidance": "Standard limit, standard tenor",
        "monitoring_frequency": "Quarterly",
        "rationale": (
            "Below-average observed default rate, consistent with "
            "standard-terms lending."
        )
    },
    "Very Low Risk": {
        "lending_decision": "Approve — preferred terms",
        "indicative_pricing_tier": "Tier A",
        "indicative_monthly_rate": "2.0% - 2.75%",
        "facility_limit_guidance": (
            "Higher limit eligible, longer tenor eligible"
        ),
        "monitoring_frequency": "Quarterly",
        "rationale": (
            "Lowest observed default rate band. Eligible for preferred "
            "pricing and larger facility sizes."
        )
    }
}

# HEADER
print("=" * 80)
print("OREY ANALYTICS — FINANCIAL HEALTH SCORING")
print("07 — FINAL OREY FINANCIAL HEALTH SCORE & SME ASSESSMENT")
print("=" * 80)

# CHECK REQUIRED FILES
print("\nChecking required files...")

required_files = [
    ENGINEERED_FILE,
    TRAIN_SCORE_FILE,
    VALIDATION_SCORE_FILE,
    TEST_SCORE_FILE,
    RISK_BAND_DEFINITIONS_FILE,
    VALIDATION_METADATA_FILE,
    SCORECARD_METADATA_FILE
]

for file in required_files:
    if not file.exists():
        raise FileNotFoundError(
            f"Required file not found: {file}"
        )

print("Required files confirmed.")

# LOAD STAGE 06 VALIDATION DECISION
print("\nLoading Stage 06 validation decision...")

with open(VALIDATION_METADATA_FILE, "r", encoding="utf-8") as file:
    validation_metadata = json.load(file)

with open(SCORECARD_METADATA_FILE, "r", encoding="utf-8") as file:
    scorecard_metadata = json.load(file)

model_validation_pass = bool(
    validation_metadata["model_validation_pass"]
)

print(
    f"Model validation status: "
    f"{'PASS' if model_validation_pass else 'REVIEW REQUIRED'}"
)

if not model_validation_pass:
    print(
        "\nWARNING: The model did not pass all Stage 06 validation "
        "criteria. Outputs will still be produced for review, but will "
        "be clearly flagged as NOT APPROVED for automated production "
        "lending decisions."
    )

# LOAD RISK BAND DEFINITIONS
print("\nLoading Stage 06 risk band definitions...")

risk_band_definitions = pd.read_csv(RISK_BAND_DEFINITIONS_FILE)

print(risk_band_definitions.to_string(index=False))

band_bounds = {
    row["risk_band"]: (row["minimum_score"], row["maximum_score"])
    for _, row in risk_band_definitions.iterrows()
}


def assign_risk_band(score):
    """Assign a risk band using Stage 06's validation-derived cutoffs."""

    for band in RISK_BAND_ORDER:
        minimum_score, maximum_score = band_bounds[band]

        if minimum_score <= score <= maximum_score:
            return band

    return "Unclassified"


# LOAD SCORECARD OUTPUTS
print("\nLoading Stage 05 scorecard outputs...")

train_scores = pd.read_csv(TRAIN_SCORE_FILE)
validation_scores = pd.read_csv(VALIDATION_SCORE_FILE)
test_scores = pd.read_csv(TEST_SCORE_FILE)

print(f"Training scores:   {len(train_scores):,}")
print(f"Validation scores: {len(validation_scores):,}")
print(f"Test scores:       {len(test_scores):,}")

# RE-ATTACH BUSINESS IDENTIFIERS
print("\n" + "=" * 80)
print("RE-ATTACHING BUSINESS IDENTIFIERS")
print("=" * 80)

print(
    "\nStage 03 deliberately excluded business identifiers from the "
    "modelling matrices. Identifiers are reconstructed here from the "
    "Stage 02 engineered panel, applying the identical filter and split "
    "logic Stage 03 used, then verified before being trusted."
)

engineered = pd.read_csv(ENGINEERED_FILE)

engineered_observable = engineered.loc[
    engineered["outcome_observable"] == True
].copy()

split_masks = {
    "train": engineered_observable["model_split"] == "train",
    "validation": engineered_observable["model_split"] == "validation",
    "test": engineered_observable["model_split"] == "test"
}

identifier_frames = {}

for split_name, mask in split_masks.items():

    identifiers = (
        engineered_observable
        .loc[mask, IDENTIFIER_COLUMNS + [TARGET]]
        .reset_index(drop=True)
    )

    identifier_frames[split_name] = identifiers

    print(
        f"{split_name.capitalize()} identifiers reconstructed: "
        f"{len(identifiers):,}"
    )


def attach_identifiers(scores, identifiers, split_name):
    """
    Positionally join reconstructed identifiers back onto a Stage 05
    score file, after verifying the two frames are alignable.
    """

    if len(scores) != len(identifiers):
        raise ValueError(
            f"Row count mismatch for {split_name}: "
            f"{len(scores)} scores vs {len(identifiers)} identifiers. "
            "Identifier re-attachment cannot be trusted."
        )

    scores_reset = scores.reset_index(drop=True)
    identifiers_reset = identifiers.reset_index(drop=True)

    target_mismatches = int(
        (
            scores_reset[TARGET].astype(int)
            != identifiers_reset[TARGET].astype(int)
        ).sum()
    )

    if target_mismatches > 0:
        raise ValueError(
            f"{target_mismatches} target mismatches detected while "
            f"re-attaching identifiers for {split_name}. Row order "
            "between Stage 05 scores and the reconstructed identifiers "
            "does not line up — identifier re-attachment aborted."
        )

    combined = pd.concat(
        [
            identifiers_reset.drop(columns=[TARGET]),
            scores_reset
        ],
        axis=1
    )

    combined.insert(0, "model_split", split_name)

    return combined


train_combined = attach_identifiers(
    train_scores,
    identifier_frames["train"],
    "train"
)

validation_combined = attach_identifiers(
    validation_scores,
    identifier_frames["validation"],
    "validation"
)

test_combined = attach_identifiers(
    test_scores,
    identifier_frames["test"],
    "test"
)

print("\nIdentifier re-attachment verified for all three splits.")

# COMBINE FULL SCORED POPULATION
print("\n" + "=" * 80)
print("BUILDING FINAL SCORED POPULATION")
print("=" * 80)

scored_population = pd.concat(
    [train_combined, validation_combined, test_combined],
    ignore_index=True
)

print(f"Total scored observations: {len(scored_population):,}")

duplicate_ids = int(
    scored_population.duplicated(
        subset=["business_id", "snapshot_date"]
    ).sum()
)

print(f"Duplicate business/snapshot rows: {duplicate_ids:,}")

# APPLY FINAL RISK BANDS
print("\nApplying Stage 06 risk bands to the full scored population...")

scored_population["risk_band"] = (
    scored_population[SCORE_COLUMN]
    .apply(assign_risk_band)
)

unclassified = int(
    (scored_population["risk_band"] == "Unclassified").sum()
)

if unclassified > 0:
    print(
        f"\nWARNING: {unclassified} observations fell outside the "
        "defined risk band ranges and were marked 'Unclassified'. "
        "These should be investigated before use."
    )

scored_population["risk_band"] = pd.Categorical(
    scored_population["risk_band"],
    categories=RISK_BAND_ORDER + ["Unclassified"],
    ordered=True
)

# APPLY LENDING DECISION POLICY
print("\nApplying lending decision policy...")

decision_policy_df = pd.DataFrame(
    [
        {"risk_band": band, **policy}
        for band, policy in LENDING_DECISION_POLICY.items()
    ]
)

decision_policy_df["risk_band"] = pd.Categorical(
    decision_policy_df["risk_band"],
    categories=RISK_BAND_ORDER,
    ordered=True
)

decision_policy_df = decision_policy_df.sort_values(
    "risk_band"
).reset_index(drop=True)

scored_population = scored_population.merge(
    decision_policy_df,
    on="risk_band",
    how="left"
)

scored_population["model_approved_for_production"] = (
    model_validation_pass
)

# COLUMN ORDER
final_columns = [
    "business_id",
    "snapshot_date",
    "model_split",
    "province",
    "industry_sector",
    "legal_entity_type",
    "business_age_years",
    "annual_revenue",
    TARGET,
    PROBABILITY_COLUMN,
    SCORE_COLUMN,
    "risk_band",
    "lending_decision",
    "indicative_pricing_tier",
    "indicative_monthly_rate",
    "facility_limit_guidance",
    "monitoring_frequency",
    "model_approved_for_production"
]

scored_population = scored_population[final_columns]

# PORTFOLIO RISK SUMMARY
print("\n" + "=" * 80)
print("PORTFOLIO RISK SUMMARY")
print("=" * 80)


def summarise_by_band(dataset, dataset_name):

    summary = (
        dataset
        .groupby("risk_band", observed=False)
        .agg(
            observations=(TARGET, "size"),
            defaults=(TARGET, "sum"),
            observed_default_rate=(TARGET, "mean"),
            mean_score=(SCORE_COLUMN, "mean")
        )
        .reindex(RISK_BAND_ORDER)
        .reset_index()
    )

    summary["population_share"] = (
        summary["observations"] / len(dataset)
    )

    summary.insert(0, "population", dataset_name)

    return summary


portfolio_summary_overall = summarise_by_band(
    scored_population,
    "full_scored_population"
)

portfolio_summary_by_split = pd.concat(
    [
        summarise_by_band(
            scored_population.loc[
                scored_population["model_split"] == split
            ],
            split
        )
        for split in ["train", "validation", "test"]
    ],
    ignore_index=True
)

portfolio_risk_summary = pd.concat(
    [portfolio_summary_overall, portfolio_summary_by_split],
    ignore_index=True
)

print(portfolio_risk_summary.to_string(index=False))

# LENDING DECISION SUMMARY
print("\n" + "=" * 80)
print("LENDING DECISION SUMMARY")
print("=" * 80)

decision_summary = (
    scored_population
    .groupby("lending_decision", observed=False)
    .agg(
        observations=(TARGET, "size"),
        observed_default_rate=(TARGET, "mean")
    )
    .reset_index()
)

decision_summary["population_share"] = (
    decision_summary["observations"] / len(scored_population)
)

print(decision_summary.to_string(index=False))

# PORTFOLIO SEGMENT SUMMARY (PROVINCE / INDUSTRY)
print("\n" + "=" * 80)
print("PORTFOLIO SEGMENT SUMMARY")
print("=" * 80)


def summarise_by_segment(dataset, segment_column):

    summary = (
        dataset
        .groupby(segment_column, observed=True)
        .agg(
            observations=(TARGET, "size"),
            observed_default_rate=(TARGET, "mean"),
            mean_score=(SCORE_COLUMN, "mean")
        )
        .reset_index()
        .rename(columns={segment_column: "segment_value"})
    )

    summary.insert(0, "segment_type", segment_column)

    summary = summary.sort_values(
        "observations",
        ascending=False
    )

    return summary


segment_summary = pd.concat(
    [
        summarise_by_segment(scored_population, "province"),
        summarise_by_segment(scored_population, "industry_sector"),
        summarise_by_segment(scored_population, "legal_entity_type")
    ],
    ignore_index=True
)

print(
    segment_summary
    .groupby("segment_type")
    .head(5)
    .to_string(index=False)
)

# SAVE OUTPUTS
print("\n" + "=" * 80)
print("SAVING FINAL OUTPUTS")
print("=" * 80)

scored_population.to_csv(
    OUTPUT_DIR / "final_scored_population.csv",
    index=False
)

scored_population.to_csv(
    OUTPUT_DIR / "sme_financial_health_assessment.csv",
    index=False
)

decision_policy_df.to_csv(
    OUTPUT_DIR / "lending_decision_policy.csv",
    index=False
)

portfolio_risk_summary.to_csv(
    OUTPUT_DIR / "portfolio_risk_summary.csv",
    index=False
)

decision_summary.to_csv(
    OUTPUT_DIR / "lending_decision_summary.csv",
    index=False
)

segment_summary.to_csv(
    OUTPUT_DIR / "portfolio_segment_summary.csv",
    index=False
)

# MODEL CARD
print("\nBuilding model card...")

model_card = {
    "model_name": "Orey Financial Health Scorecard",
    "developer": "Orey Analytics",
    "model_purpose": (
        "Predicts 12-month SME default risk from bank-transaction "
        "cash-flow behaviour, business bureau data and director bureau "
        "data, and translates the resulting score into risk bands and "
        "indicative lending decisions for alternative lenders."
    ),
    "model_type": scorecard_metadata.get("model_type"),
    "target": TARGET,
    "score_range": {
        "minimum": scorecard_metadata.get("score_minimum"),
        "maximum": scorecard_metadata.get("score_maximum")
    },
    "final_features": scorecard_metadata.get("selected_features"),
    "number_of_features": scorecard_metadata.get("final_features"),
    "population": {
        "training_rows": int(len(train_combined)),
        "validation_rows": int(len(validation_combined)),
        "test_rows": int(len(test_combined)),
        "total_scored_rows": int(len(scored_population))
    },
    "performance": {
        "train_auc": validation_metadata.get("train_auc"),
        "validation_auc": validation_metadata.get("validation_auc"),
        "test_auc": validation_metadata.get("test_auc"),
        "train_gini": validation_metadata.get("train_gini"),
        "validation_gini": validation_metadata.get("validation_gini"),
        "test_gini": validation_metadata.get("test_gini"),
        "train_ks": validation_metadata.get("train_ks"),
        "validation_ks": validation_metadata.get("validation_ks"),
        "test_ks": validation_metadata.get("test_ks"),
        "validation_calibration_error": validation_metadata.get(
            "validation_calibration_error"
        ),
        "test_calibration_error": validation_metadata.get(
            "test_calibration_error"
        )
    },
    "risk_bands": risk_band_definitions.to_dict(orient="records"),
    "lending_decision_policy": LENDING_DECISION_POLICY,
    "validation_criteria": validation_metadata.get(
        "validation_criteria"
    ),
    "model_validation_pass": model_validation_pass,
    "approved_for_production": model_validation_pass,
    "governance_notes": (
        "Identifiers were excluded from model training and re-attached "
        "post-hoc for reporting only, using a verified positional join "
        "back to the Stage 02 engineered panel. The lending decision "
        "policy is a separate, editable business-rules layer and is not "
        "part of the statistical model. Risk-band cutoffs were derived "
        "on the validation set only (Stage 06) and applied unchanged "
        "here."
    ),
    "pipeline_stages": [
        "01 - Data audit",
        "02 - Feature engineering",
        "03 - Preprocessing and leakage control",
        "04 - WoE binning and Information Value",
        "05 - Feature selection and scorecard modelling",
        "06 - Model validation, calibration and risk bands",
        "07 - Final score, SME assessment and lending decisions"
    ],
    "next_stage": (
        "08 - Score new/unscored applicants from the applicant scoring "
        "population and reason-code individual assessments using "
        "scorecard_feature_points.csv."
    )
}

with open(
    OUTPUT_DIR / "orey_financial_health_model_card.json",
    "w",
    encoding="utf-8"
) as file:
    json.dump(model_card, file, indent=4, default=str)

# COMPLETION
print("\n" + "=" * 80)
print("FINAL SCORING & SME ASSESSMENT COMPLETE")
print("=" * 80)

print(
    f"\nProduction approval status: "
    f"{'APPROVED' if model_validation_pass else 'NOT APPROVED — REVIEW REQUIRED'}"
)

print(f"\nTotal SME observations scored: {len(scored_population):,}")

print("\nRisk band distribution (full scored population):")
print(
    portfolio_summary_overall[
        ["risk_band", "observations", "population_share", "observed_default_rate"]
    ].to_string(index=False)
)

print("\nOutputs saved to:")
print(OUTPUT_DIR)

print("\nGenerated files:")
print("  - final_scored_population.csv")
print("  - sme_financial_health_assessment.csv")
print("  - lending_decision_policy.csv")
print("  - portfolio_risk_summary.csv")
print("  - lending_decision_summary.csv")
print("  - portfolio_segment_summary.csv")
print("  - orey_financial_health_model_card.json")

print("\nSource datasets and upstream stage outputs were not modified.")

print("\nNext stage:")
print(
    "08 — Score new applicants and generate per-SME reason codes "
    "from scorecard_feature_points.csv"
)