"""
Orey Analytics
Financial Health Scoring — Population Model

Stage 07 — Final Orey Financial Health Score & SME Assessment

Purpose:
Take the Stage 05 scorecard outputs and the Stage 06 validation decision and
turn them into a finished, business-facing product:

    1. Re-attach business identifiers to the train/validation/test scores.
    2. Apply the empirically-derived risk bands from Stage 06 consistently.
    3. Translate risk bands into an indicative lending decision and policy tier.
    4. Summarise the scored portfolio by risk band, province, industry,
       legal entity type and model split.
    5. Produce a consolidated "Orey Financial Health Assessment" file per
       outcome-observable SME observation.
    6. Produce a model card documenting the full pipeline for governance
       and audit.
    7. Perform final integrity checks before outputs are accepted.

Key principles:
    1. No model is retrained here. Stage 05's scorecard and Stage 06's
       validated risk bands are used as-is.
    2. Stage 06's model_validation_pass decision gates the statistical
       validation status of this stage's outputs.
    3. Identifiers are re-attached using the established positional
       relationship to the Stage 02 engineered panel, with row count,
       target, identifier and duplicate checks before use.
    4. Source datasets and upstream stage outputs are never modified.
    5. The lending decision policy is an explicit, editable business-rules
       layer kept separate from the statistical model.
    6. Pricing ranges are illustrative Orey Analytics policy assumptions
       and are not model-derived interest rates or live lending offers.
    7. Statistical validation passing does not by itself constitute formal
       production approval; governance review remains a separate control.
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

MODEL_SPLITS = [
    "train",
    "validation",
    "test"
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
# Risk-band boundaries come from Stage 06.
# Lending decisions, pricing ranges and facility guidance are illustrative
# Orey Analytics policy assumptions and can be revised without retraining.

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

with open(
    VALIDATION_METADATA_FILE,
    "r",
    encoding="utf-8"
) as file:
    validation_metadata = json.load(file)

with open(
    SCORECARD_METADATA_FILE,
    "r",
    encoding="utf-8"
) as file:
    scorecard_metadata = json.load(file)

model_validation_pass = bool(
    validation_metadata["model_validation_pass"]
)

print(
    f"Model statistical validation status: "
    f"{'PASS' if model_validation_pass else 'REVIEW REQUIRED'}"
)

if not model_validation_pass:
    print(
        "\nWARNING: The model did not pass all Stage 06 validation "
        "criteria. Outputs will still be produced for review, but "
        "they are NOT approved for automated production decisioning."
    )

# LOAD RISK BAND DEFINITIONS
print("\nLoading Stage 06 risk band definitions...")

risk_band_definitions = pd.read_csv(
    RISK_BAND_DEFINITIONS_FILE
)

print(
    risk_band_definitions.to_string(index=False)
)

# VALIDATE RISK BAND DEFINITIONS
print("\nValidating risk-band definitions...")

required_band_columns = {
    "risk_band",
    "minimum_score",
    "maximum_score"
}

missing_band_columns = (
    required_band_columns
    - set(risk_band_definitions.columns)
)

if missing_band_columns:
    raise ValueError(
        "Risk-band definitions are missing required columns: "
        f"{sorted(missing_band_columns)}"
    )

missing_bands = (
    set(RISK_BAND_ORDER)
    - set(risk_band_definitions["risk_band"])
)

if missing_bands:
    raise ValueError(
        "Risk-band definitions are missing required bands: "
        f"{sorted(missing_bands)}"
    )

if risk_band_definitions["risk_band"].duplicated().any():
    raise ValueError(
        "Duplicate risk-band definitions detected."
    )

if (
    risk_band_definitions["minimum_score"]
    > risk_band_definitions["maximum_score"]
).any():
    raise ValueError(
        "One or more risk bands have minimum_score greater "
        "than maximum_score."
    )

band_bounds = {
    row["risk_band"]: (
        row["minimum_score"],
        row["maximum_score"]
    )
    for _, row in risk_band_definitions.iterrows()
}

print("Risk-band definitions validated.")

# RISK BAND ASSIGNMENT
def assign_risk_band(score):
    """Assign a risk band using Stage 06 validation-derived cutoffs."""

    if pd.isna(score):
        return "Unclassified"

    for band in RISK_BAND_ORDER:
        minimum_score, maximum_score = band_bounds[band]

        if minimum_score <= score <= maximum_score:
            return band

    return "Unclassified"

# LOAD STAGE 05 SCORECARD OUTPUTS
print("\nLoading Stage 05 scorecard outputs...")

train_scores = pd.read_csv(TRAIN_SCORE_FILE)
validation_scores = pd.read_csv(VALIDATION_SCORE_FILE)
test_scores = pd.read_csv(TEST_SCORE_FILE)

print(f"Training scores:   {len(train_scores):,}")
print(f"Validation scores: {len(validation_scores):,}")
print(f"Test scores:       {len(test_scores):,}")

# VALIDATE SCORECARD OUTPUT STRUCTURE
print("\nValidating Stage 05 score outputs...")

required_score_columns = {
    TARGET,
    PROBABILITY_COLUMN,
    SCORE_COLUMN
}

for split_name, scores in {
    "train": train_scores,
    "validation": validation_scores,
    "test": test_scores
}.items():

    missing_columns = (
        required_score_columns
        - set(scores.columns)
    )

    if missing_columns:
        raise ValueError(
            f"{split_name} score file is missing required columns: "
            f"{sorted(missing_columns)}"
        )

print("Stage 05 score outputs validated.")

# RE-ATTACH BUSINESS IDENTIFIERS
print("\nRe-attaching business identifiers...")

engineered = pd.read_csv(
    ENGINEERED_FILE
)

required_engineered_columns = set(
    IDENTIFIER_COLUMNS
    + [
        TARGET,
        "outcome_observable",
        "model_split"
    ]
)

missing_engineered_columns = (
    required_engineered_columns
    - set(engineered.columns)
)

if missing_engineered_columns:
    raise ValueError(
        "Engineered panel is missing required columns: "
        f"{sorted(missing_engineered_columns)}"
    )

engineered_observable = engineered.loc[
    engineered["outcome_observable"] == True
].copy()

print(
    f"Outcome-observable observations available: "
    f"{len(engineered_observable):,}"
)

identifier_frames = {}

for split_name in MODEL_SPLITS:

    identifiers = (
        engineered_observable.loc[
            engineered_observable["model_split"] == split_name,
            IDENTIFIER_COLUMNS + [TARGET]
        ]
        .reset_index(drop=True)
    )

    identifier_frames[split_name] = identifiers

    print(
        f"{split_name.capitalize()} identifiers reconstructed: "
        f"{len(identifiers):,}"
    )

# IDENTIFIER RE-ATTACHMENT
def attach_identifiers(scores, identifiers, split_name):
    """
    Re-attach identifiers to Stage 05 scores using the established
    positional relationship between the Stage 05 score files and the
    reconstructed Stage 02 population.
    """

    if len(scores) != len(identifiers):
        raise ValueError(
            f"Row count mismatch for {split_name}: "
            f"{len(scores)} scores vs {len(identifiers)} identifiers. "
            "Identifier re-attachment aborted."
        )

    scores_reset = (
        scores
        .reset_index(drop=True)
        .copy()
    )

    identifiers_reset = (
        identifiers
        .reset_index(drop=True)
        .copy()
    )

    score_targets = pd.to_numeric(
        scores_reset[TARGET],
        errors="coerce"
    )

    identifier_targets = pd.to_numeric(
        identifiers_reset[TARGET],
        errors="coerce"
    )

    target_mismatches = int(
        (
            score_targets != identifier_targets
        )
        .fillna(
            score_targets.isna()
            != identifier_targets.isna()
        )
        .sum()
    )

    if target_mismatches > 0:
        raise ValueError(
            f"{target_mismatches} target mismatches detected while "
            f"re-attaching identifiers for {split_name}. "
            "Row order between Stage 05 scores and reconstructed "
            "identifiers does not line up."
        )

    if identifiers_reset["business_id"].isna().any():
        raise ValueError(
            f"Missing business_id values detected in the "
            f"{split_name} identifier frame."
        )

    if identifiers_reset["snapshot_date"].isna().any():
        raise ValueError(
            f"Missing snapshot_date values detected in the "
            f"{split_name} identifier frame."
        )

    duplicate_count = int(
        identifiers_reset.duplicated(
            subset=[
                "business_id",
                "snapshot_date"
            ]
        ).sum()
    )

    if duplicate_count > 0:
        raise ValueError(
            f"{duplicate_count} duplicate business/snapshot observations "
            f"detected in the {split_name} identifier frame."
        )

    combined = pd.concat(
        [
            identifiers_reset.drop(columns=[TARGET]),
            scores_reset
        ],
        axis=1
    )

    combined.insert(
        0,
        "model_split",
        split_name
    )

    print(
        f"{split_name.capitalize()} identifier alignment verified."
    )

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

# BUILD FINAL OBSERVABLE SCORED POPULATION
print("\nBuilding final observable scored population...")

scored_population = pd.concat(
    [
        train_combined,
        validation_combined,
        test_combined
    ],
    ignore_index=True
)

print(
    f"Total outcome-observable scored observations: "
    f"{len(scored_population):,}"
)

# FINAL SCORE AND PROBABILITY INTEGRITY CHECKS
print("\nValidating score and probability ranges...")

probability_numeric = pd.to_numeric(
    scored_population[PROBABILITY_COLUMN],
    errors="coerce"
)

score_numeric = pd.to_numeric(
    scored_population[SCORE_COLUMN],
    errors="coerce"
)

missing_probabilities = int(
    probability_numeric.isna().sum()
)

missing_scores = int(
    score_numeric.isna().sum()
)

if missing_probabilities > 0:
    raise ValueError(
        f"{missing_probabilities:,} missing or non-numeric "
        "predicted default probabilities detected."
    )

if missing_scores > 0:
    raise ValueError(
        f"{missing_scores:,} missing or non-numeric "
        "Orey Financial Health scores detected."
    )

probability_out_of_range = int(
    (
        (probability_numeric < 0)
        |
        (probability_numeric > 1)
    ).sum()
)

if probability_out_of_range > 0:
    raise ValueError(
        f"{probability_out_of_range:,} predicted default "
        "probabilities fall outside [0, 1]."
    )

score_minimum = scorecard_metadata.get(
    "score_minimum"
)

score_maximum = scorecard_metadata.get(
    "score_maximum"
)

if score_minimum is not None:
    score_below_minimum = int(
        (score_numeric < float(score_minimum)).sum()
    )
else:
    score_below_minimum = 0

if score_maximum is not None:
    score_above_maximum = int(
        (score_numeric > float(score_maximum)).sum()
    )
else:
    score_above_maximum = 0

if score_below_minimum > 0:
    raise ValueError(
        f"{score_below_minimum:,} scores fall below the "
        "Stage 05 documented score minimum."
    )

if score_above_maximum > 0:
    raise ValueError(
        f"{score_above_maximum:,} scores exceed the "
        "Stage 05 documented score maximum."
    )

print("Score and probability ranges validated.")

# CHECK DUPLICATE SME OBSERVATIONS
duplicate_ids = int(
    scored_population.duplicated(
        subset=[
            "business_id",
            "snapshot_date"
        ]
    ).sum()
)

print(
    f"Duplicate business/snapshot rows: {duplicate_ids:,}"
)

if duplicate_ids > 0:
    raise ValueError(
        "Duplicate business/snapshot observations detected "
        "in the final scored population."
    )

# APPLY FINAL RISK BANDS
print(
    "\nApplying Stage 06 risk bands to the full "
    "outcome-observable scored population..."
)

scored_population["risk_band"] = (
    scored_population[SCORE_COLUMN]
    .apply(assign_risk_band)
)

unclassified = int(
    (
        scored_population["risk_band"]
        == "Unclassified"
    ).sum()
)

if unclassified > 0:
    raise ValueError(
        f"{unclassified:,} observations fell outside the "
        "Stage 06 defined risk-band ranges. "
        "Risk-band assignment cannot be accepted."
    )

scored_population["risk_band"] = pd.Categorical(
    scored_population["risk_band"],
    categories=RISK_BAND_ORDER,
    ordered=True
)

print("Risk-band assignment completed successfully.")

# VALIDATE LENDING POLICY COVERAGE
print("\nValidating lending decision policy...")

missing_policy_bands = (
    set(RISK_BAND_ORDER)
    - set(LENDING_DECISION_POLICY.keys())
)

if missing_policy_bands:
    raise ValueError(
        "Lending decision policy does not define all risk bands: "
        f"{sorted(missing_policy_bands)}"
    )

print("All five risk bands have corresponding policy definitions.")

# APPLY LENDING DECISION POLICY
print("\nApplying lending decision policy...")

decision_policy_df = pd.DataFrame(
    [
        {
            "risk_band": band,
            **policy
        }
        for band, policy in LENDING_DECISION_POLICY.items()
    ]
)

decision_policy_df["risk_band"] = pd.Categorical(
    decision_policy_df["risk_band"],
    categories=RISK_BAND_ORDER,
    ordered=True
)

decision_policy_df = (
    decision_policy_df
    .sort_values("risk_band")
    .reset_index(drop=True)
)

scored_population = scored_population.merge(
    decision_policy_df,
    on="risk_band",
    how="left",
    validate="many_to_one"
)

# STATISTICAL VALIDATION AND GOVERNANCE STATUS
scored_population[
    "statistical_validation_pass"
] = model_validation_pass

scored_population[
    "production_governance_status"
] = (
    "Statistical validation passed — governance review required"
    if model_validation_pass
    else
    "Not approved — statistical validation review required"
)

# FINAL COLUMN ORDER
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
    "statistical_validation_pass",
    "production_governance_status"
]

scored_population = scored_population[
    final_columns
]

# PORTFOLIO RISK SUMMARY
print("\nGenerating portfolio risk summary...")

def summarise_by_band(dataset, dataset_name):

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
            mean_score=(SCORE_COLUMN, "mean")
        )
        .reindex(RISK_BAND_ORDER)
        .reset_index()
    )

    summary["population_share"] = (
        summary["observations"]
        / len(dataset)
    )

    summary.insert(
        0,
        "population",
        dataset_name
    )

    return summary

portfolio_summary_overall = summarise_by_band(
    scored_population,
    "outcome_observable_scored_population"
)

portfolio_summary_by_split = pd.concat(
    [
        summarise_by_band(
            scored_population.loc[
                scored_population["model_split"] == split
            ],
            split
        )
        for split in MODEL_SPLITS
    ],
    ignore_index=True
)

portfolio_risk_summary = pd.concat(
    [
        portfolio_summary_overall,
        portfolio_summary_by_split
    ],
    ignore_index=True
)

print(
    portfolio_risk_summary.to_string(
        index=False
    )
)

# POPULATION SHARE INTEGRITY CHECK
overall_population_share = (
    portfolio_summary_overall[
        "population_share"
    ].sum()
)

if not np.isclose(
    overall_population_share,
    1.0,
    atol=1e-9
):
    raise ValueError(
        "Overall risk-band population shares do not sum to 100%."
    )

print("Overall risk-band population shares sum to 100%.")

# RISK-BAND DEFAULT-RATE ORDER CHECK
print("\nChecking empirical risk-band ordering...")

band_default_rates = (
    portfolio_summary_overall[
        [
            "risk_band",
            "observed_default_rate"
        ]
    ]
    .dropna()
)

if len(band_default_rates) >= 2:

    default_rates = (
        band_default_rates[
            "observed_default_rate"
        ].to_numpy()
    )

    decreasing_sequence = np.all(
        np.diff(default_rates) <= 1e-12
    )

    if not decreasing_sequence:
        print(
            "WARNING: Observed default rates are not monotonic "
            "across all risk bands. This does not automatically "
            "invalidate the model, but should be reviewed as part "
            "of model monitoring."
        )
    else:
        print(
            "Risk-band empirical default-rate ordering is monotonic."
        )

# LENDING DECISION SUMMARY
print("\nGenerating lending decision summary...")

decision_summary = (
    scored_population
    .groupby(
        "lending_decision",
        observed=False
    )
    .agg(
        observations=(TARGET, "size"),
        observed_default_rate=(TARGET, "mean")
    )
    .reset_index()
)

decision_summary["population_share"] = (
    decision_summary["observations"]
    / len(scored_population)
)

print(
    decision_summary.to_string(
        index=False
    )
)

# PORTFOLIO SEGMENT SUMMARY
print("\nGenerating portfolio segment summary...")

def summarise_by_segment(dataset, segment_column):

    summary = (
        dataset
        .groupby(
            segment_column,
            observed=True
        )
        .agg(
            observations=(TARGET, "size"),
            observed_default_rate=(TARGET, "mean"),
            mean_score=(SCORE_COLUMN, "mean")
        )
        .reset_index()
        .rename(
            columns={
                segment_column: "segment_value"
            }
        )
    )

    summary.insert(
        0,
        "segment_type",
        segment_column
    )

    return summary.sort_values(
        "observations",
        ascending=False
    )

segment_summary = pd.concat(
    [
        summarise_by_segment(
            scored_population,
            "province"
        ),
        summarise_by_segment(
            scored_population,
            "industry_sector"
        ),
        summarise_by_segment(
            scored_population,
            "legal_entity_type"
        )
    ],
    ignore_index=True
)

print(
    segment_summary
    .groupby("segment_type")
    .head(5)
    .to_string(index=False)
)

# POLICY GOVERNANCE NOTE
policy_governance_note = (
    "Indicative pricing ranges, facility guidance, monitoring frequency "
    "and lending decisions are illustrative Orey Analytics business-policy "
    "assumptions. They are not estimated by the statistical scorecard and "
    "do not constitute live lending offers, regulated credit pricing or "
    "formal credit policy."
)

# SAVE OUTPUTS
print("\nSaving final outputs...")

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
        "total_observable_scored_rows": int(
            len(scored_population)
        )
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
    "risk_bands": risk_band_definitions.to_dict(
        orient="records"
    ),
    "lending_decision_policy": LENDING_DECISION_POLICY,
    "policy_governance_note": policy_governance_note,
    "validation_criteria": validation_metadata.get(
        "validation_criteria"
    ),
    "statistical_validation_pass": model_validation_pass,
    "production_governance_status": (
        "Statistical validation passed — "
        "governance review required"
        if model_validation_pass
        else
        "Not approved — statistical validation review required"
    ),
    "governance_notes": (
        "Identifiers were excluded from model training and re-attached "
        "post-hoc for reporting only, using a verified positional "
        "relationship back to the Stage 02 engineered panel. "
        "The lending decision policy is a separate editable business-"
        "rules layer and is not part of the statistical model. "
        "Risk-band cutoffs were derived on the validation set only "
        "(Stage 06) and applied unchanged here. "
        "Passing statistical validation does not by itself constitute "
        "formal production approval."
    ),
    "integrity_checks": {
        "duplicate_business_snapshot_rows": duplicate_ids,
        "unclassified_risk_band_rows": unclassified,
        "missing_probability_rows": missing_probabilities,
        "missing_score_rows": missing_scores,
        "probability_out_of_range_rows": probability_out_of_range,
        "score_below_documented_minimum": score_below_minimum,
        "score_above_documented_maximum": score_above_maximum,
        "overall_population_share": float(
            overall_population_share
        )
    },
    "pipeline_stages": [
        "01 - Data audit",
        "02 - Feature engineering",
        "03 - Preprocessing and leakage control",
        "04 - WoE binning and Information Value",
        "05 - Feature selection and scorecard modelling",
        "06 - Model validation, calibration and risk bands",
        "07 - Final score, SME assessment and lending policy"
    ],
    "next_stage": (
        "08 - Score new/unscored applicants from the applicant scoring "
        "population and generate individual SME assessments and "
        "reason codes using scorecard_feature_points.csv."
    )
}

with open(
    OUTPUT_DIR / "orey_financial_health_model_card.json",
    "w",
    encoding="utf-8"
) as file:
    json.dump(
        model_card,
        file,
        indent=4,
        default=str
    )

# COMPLETION
print("\n" + "=" * 80)
print("FINAL SCORING & SME ASSESSMENT COMPLETE")
print("=" * 80)

print(
    "\nStatistical validation status: "
    f"{'PASS' if model_validation_pass else 'NOT PASSED — REVIEW REQUIRED'}"
)

print("\nProduction governance status:")

print(
    "  Statistical validation passed — governance review required"
    if model_validation_pass
    else
    "  Not approved — statistical validation review required"
)

print(
    f"\nTotal outcome-observable SME observations scored: "
    f"{len(scored_population):,}"
)

print("\nRisk band distribution:")

print(
    portfolio_summary_overall[
        [
            "risk_band",
            "observations",
            "population_share",
            "observed_default_rate"
        ]
    ].to_string(index=False)
)

print("\nFinal integrity checks:")

print(
    f"  Duplicate business/snapshot rows: "
    f"{duplicate_ids:,}"
)

print(
    f"  Unclassified risk-band rows: "
    f"{unclassified:,}"
)

print(
    f"  Missing probabilities: "
    f"{missing_probabilities:,}"
)

print(
    f"  Missing scores: "
    f"{missing_scores:,}"
)

print(
    f"  Probability out-of-range rows: "
    f"{probability_out_of_range:,}"
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

print(
    "\nSource datasets and upstream stage outputs were not modified."
)

print("\nNext stage:")

print(
    "08 — Score new applicants and generate per-SME reason codes "
    "from scorecard_feature_points.csv"
)