"""
Orey Analytics
Financial Health Scoring — Population Model

Stage 10 — Fairness & Disparate Impact Review

Purpose:
Check whether the scorecard's lending decisions, scores and calibration
differ meaningfully across business-level segments — province, industry
sector, legal entity type and business maturity — on out-of-sample,
labelled data (validation + test splits from Stage 07's final scored
population).

IMPORTANT SCOPE LIMITATION — READ BEFORE INTERPRETING RESULTS:
    This dataset does not contain demographic attributes of business
    owners/directors (e.g. race, gender, disability), which are the
    actual protected characteristics under South African law (the
    Promotion of Equality and Prevention of Unfair Discrimination Act,
    the Employment Equity Act's underlying principles, and the National
    Credit Act's prohibition on unfair discrimination in credit
    decisions). Province and industry sector are used here as the best
    available PROXIES for a first-pass screen, not as a substitute for a
    proper fairness audit against real demographic data.

    The "four-fifths rule" (80% adverse impact ratio threshold) applied
    here is a US EEOC screening heuristic, borrowed for analytical
    convenience. It is not a South African legal standard and passing it
    is not a compliance determination. Any group flagged below should be
    investigated by, or in consultation with, someone qualified to advise
    on the National Credit Act and PEPUDA — this script identifies where
    to look, not whether the model is lawful.

Purpose of this stage, precisely:
    1. Approval rate parity — does one group get approved at a
       substantially lower rate than others, adjusted for nothing (a raw
       screen; it does not control for the fact that groups may have
       genuinely different risk profiles).
    2. Calibration parity — does the model's predicted probability match
       the group's actual observed default rate, or does it systematically
       over/under-estimate risk for specific groups?
    3. Error-rate parity — among businesses that did NOT default, what
       share were declined/referred anyway (the "false decline rate" —
       the direct harm a credit model can cause to a segment)?

Key principles:
    1. No model is retrained or adjusted here. This is a read-only audit
       of Stage 07's already-produced decisions.
    2. Analysis runs on validation + test splits only (out-of-sample),
       never training, to avoid conflating fit quality with fairness.
    3. Every group-level statistic is reported with its sample size, since
       small groups produce noisy, unreliable ratios that should not be
       over-interpreted.
    4. Source datasets and upstream stage outputs are never modified.
"""

# IMPORTS
from pathlib import Path
import json
import math
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# PROJECT PATHS
# This stage can live in either phase folder — it only reads Stage 07's
# already-produced final_scored_population.csv, so it locates the
# population model's outputs folder explicitly rather than assuming its
# own script location, matching the sibling-folder pattern used in
# Stages 08-09.
#
# Assumed layout (siblings under one parent, e.g. "05-financial-scoring/"):
#   01-population-model/outputs/   <- final_scored_population.csv lives here (read)
#   02-individual-assessment/...   <- this script may live here instead

SCRIPT_DIR = Path(__file__).resolve().parent
PHASE_DIR = SCRIPT_DIR.parent.parent

POPULATION_MODEL_FOLDER_NAME = "01-population-model"

if (SCRIPT_DIR.parent / "outputs" / "final_scored_population.csv").exists():
    # Script is running from inside 01-population-model itself
    OUTPUT_DIR = SCRIPT_DIR.parent / "outputs"
else:
    # Script is running from a sibling phase folder (e.g. 02-individual-assessment)
    POPULATION_MODEL_DIR = PHASE_DIR / POPULATION_MODEL_FOLDER_NAME
    OUTPUT_DIR = POPULATION_MODEL_DIR / "outputs"

FINAL_SCORED_POPULATION_FILE = OUTPUT_DIR / "final_scored_population.csv"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# CONFIGURATION
TARGET = "default_event_12m"
PROBABILITY_COLUMN = "predicted_default_probability"
SCORE_COLUMN = "orey_financial_health_score"

EVALUATION_SPLITS = ["validation", "test"]

APPROVED_DECISIONS = [
    "Approve with conditions", "Approve", "Approve — preferred terms"
]
DECLINED_OR_REFERRED_DECISIONS = [
    "Decline", "Refer for manual underwriting"
]

SEGMENT_COLUMNS = ["province", "industry_sector", "legal_entity_type"]

MIN_GROUP_SIZE = 30  # below this, ratios are flagged as unreliable

AIR_MATERIAL_THRESHOLD = 0.70   # four-fifths-rule-derived screening bands
AIR_BORDERLINE_THRESHOLD = 0.80

SIGNIFICANCE_LEVEL = 0.05

# HEADER
print("=" * 80)
print("OREY ANALYTICS — FINANCIAL HEALTH SCORING")
print("10 — FAIRNESS & DISPARATE IMPACT REVIEW")
print("=" * 80)

print(
    "\nNOTE: this analysis uses province/industry/entity-type as proxy "
    "segments, not owner/director demographic data. See the script "
    "docstring for scope limitations before interpreting results."
)

print(f"\nReading Stage 07 outputs from: {OUTPUT_DIR}")
print("Fairness review outputs will be saved to the same location.")

# CHECK REQUIRED FILES
if not FINAL_SCORED_POPULATION_FILE.exists():
    raise FileNotFoundError(
        f"Required file not found: {FINAL_SCORED_POPULATION_FILE}\n"
        "Run Stage 07 first."
    )

# LOAD DATA
print("\nLoading final scored population...")

scored_population = pd.read_csv(FINAL_SCORED_POPULATION_FILE)

required_columns = (
    ["business_id", "model_split", TARGET, PROBABILITY_COLUMN,
     SCORE_COLUMN, "lending_decision", "business_age_years"]
    + SEGMENT_COLUMNS
)

missing_columns = [
    column for column in required_columns
    if column not in scored_population.columns
]

if missing_columns:
    raise ValueError(
        f"final_scored_population.csv is missing columns: {missing_columns}"
    )

evaluation_population = scored_population.loc[
    scored_population["model_split"].isin(EVALUATION_SPLITS)
].copy()

print(
    f"Evaluation population (validation + test, out-of-sample): "
    f"{len(evaluation_population):,}"
)

# BUSINESS MATURITY SEGMENT
evaluation_population["business_maturity"] = pd.cut(
    evaluation_population["business_age_years"],
    bins=[-np.inf, 2, 5, 10, np.inf],
    labels=["0-2 years", "2-5 years", "5-10 years", "10+ years"]
)

SEGMENT_COLUMNS_ALL = SEGMENT_COLUMNS + ["business_maturity"]

evaluation_population["is_approved"] = (
    evaluation_population["lending_decision"].isin(APPROVED_DECISIONS)
)
evaluation_population["is_declined_or_referred"] = (
    evaluation_population["lending_decision"]
    .isin(DECLINED_OR_REFERRED_DECISIONS)
)


# STATISTICAL TESTING (two-proportion z-test, no external dependency)
def normal_cdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def two_proportion_z_test(x1, n1, x2, n2):
    """
    Two-sided two-proportion z-test. Returns (z_stat, p_value).
    Returns (nan, nan) if either group is empty or the pooled proportion
    is degenerate (0 or 1), where the test is undefined.
    """

    if n1 == 0 or n2 == 0:
        return np.nan, np.nan

    p1 = x1 / n1
    p2 = x2 / n2
    p_pool = (x1 + x2) / (n1 + n2)

    if p_pool in (0.0, 1.0):
        return np.nan, np.nan

    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))

    if se == 0:
        return np.nan, np.nan

    z = (p1 - p2) / se
    p_value = 2 * (1 - normal_cdf(abs(z)))

    return z, p_value


def interpret_air(air):
    if pd.isna(air):
        return "Insufficient data"
    elif air < AIR_MATERIAL_THRESHOLD:
        return "Material disparity — investigate"
    elif air < AIR_BORDERLINE_THRESHOLD:
        return "Borderline — monitor"
    else:
        return "No flag"


# GROUP-LEVEL FAIRNESS METRICS
print("\n" + "=" * 80)
print("COMPUTING GROUP-LEVEL FAIRNESS METRICS")
print("=" * 80)

fairness_records = []

total_n = len(evaluation_population)
total_approved = int(evaluation_population["is_approved"].sum())

for segment_column in SEGMENT_COLUMNS_ALL:

    print(f"\nSegment: {segment_column}")

    groups = evaluation_population.groupby(
        segment_column, observed=True
    )

    group_approval_rates = groups["is_approved"].mean()
    reference_group = group_approval_rates.idxmax()
    reference_rate = group_approval_rates.max()

    for group_value, group_data in groups:

        n = len(group_data)

        if n == 0:
            continue

        approved_n = int(group_data["is_approved"].sum())
        approval_rate = approved_n / n

        air = (
            approval_rate / reference_rate
            if reference_rate > 0 else np.nan
        )

        # Approval-rate significance vs rest of population
        rest_n = total_n - n
        rest_approved = total_approved - approved_n

        z_stat, p_value = two_proportion_z_test(
            approved_n, n, rest_approved, rest_n
        )

        # Calibration
        observed_default_rate = group_data[TARGET].mean()
        mean_predicted_probability = group_data[PROBABILITY_COLUMN].mean()
        calibration_gap = (
            mean_predicted_probability - observed_default_rate
        )

        # False decline rate: among non-defaulters, % declined/referred
        non_defaulters = group_data.loc[group_data[TARGET] == 0]
        false_decline_rate = (
            non_defaulters["is_declined_or_referred"].mean()
            if len(non_defaulters) > 0 else np.nan
        )

        # Approved-defaulter rate: among defaulters, % approved
        defaulters = group_data.loc[group_data[TARGET] == 1]
        approved_defaulter_rate = (
            defaulters["is_approved"].mean()
            if len(defaulters) > 0 else np.nan
        )

        fairness_records.append(
            {
                "segment_type": segment_column,
                "segment_value": str(group_value),
                "n": n,
                "population_share": n / total_n,
                "reliable_sample_size": n >= MIN_GROUP_SIZE,
                "approval_rate": approval_rate,
                "reference_group": reference_group,
                "reference_approval_rate": reference_rate,
                "adverse_impact_ratio": air,
                "air_flag": interpret_air(air) if n >= MIN_GROUP_SIZE
                else "Insufficient data",
                "approval_z_stat": z_stat,
                "approval_p_value": p_value,
                "approval_significant": (
                    p_value < SIGNIFICANCE_LEVEL
                    if not pd.isna(p_value) else False
                ),
                "observed_default_rate": observed_default_rate,
                "mean_predicted_probability": mean_predicted_probability,
                "calibration_gap": calibration_gap,
                "mean_score": group_data[SCORE_COLUMN].mean(),
                "false_decline_rate": false_decline_rate,
                "approved_defaulter_rate": approved_defaulter_rate,
            }
        )

    print(
        groups["is_approved"].agg(["size", "mean"])
        .rename(columns={"size": "n", "mean": "approval_rate"})
        .to_string()
    )

fairness_summary = pd.DataFrame(fairness_records).sort_values(
    ["segment_type", "adverse_impact_ratio"]
).reset_index(drop=True)

# FLAG SUMMARY
print("\n" + "=" * 80)
print("DISPARATE IMPACT SCREEN — FLAGGED GROUPS")
print("=" * 80)

material_flags = fairness_summary.loc[
    fairness_summary["air_flag"] == "Material disparity — investigate"
]

borderline_flags = fairness_summary.loc[
    fairness_summary["air_flag"] == "Borderline — monitor"
]

if len(material_flags) > 0:
    print(
        f"\n{len(material_flags)} group(s) below the "
        f"{AIR_MATERIAL_THRESHOLD} adverse impact ratio threshold "
        f"(reliable sample size only):"
    )
    print(
        material_flags[
            ["segment_type", "segment_value", "n", "approval_rate",
             "adverse_impact_ratio", "approval_significant"]
        ].to_string(index=False)
    )
else:
    print("\nNo groups fell below the material disparity threshold.")

if len(borderline_flags) > 0:
    print(
        f"\n{len(borderline_flags)} group(s) in the borderline "
        f"({AIR_MATERIAL_THRESHOLD}-{AIR_BORDERLINE_THRESHOLD}) range "
        "— worth monitoring over time:"
    )
    print(
        borderline_flags[
            ["segment_type", "segment_value", "n", "approval_rate",
             "adverse_impact_ratio"]
        ].to_string(index=False)
    )

unreliable_groups = fairness_summary.loc[
    ~fairness_summary["reliable_sample_size"]
]

if len(unreliable_groups) > 0:
    print(
        f"\n{len(unreliable_groups)} group(s) had fewer than "
        f"{MIN_GROUP_SIZE} observations and were excluded from AIR "
        "flagging as statistically unreliable (still reported, but "
        "treat with caution):"
    )
    print(
        unreliable_groups[["segment_type", "segment_value", "n"]]
        .to_string(index=False)
    )

# CALIBRATION GAP REVIEW
print("\n" + "=" * 80)
print("CALIBRATION GAP REVIEW (predicted probability vs observed default)")
print("=" * 80)

print(
    "\nA positive calibration gap means the model over-predicts risk "
    "for that group relative to what actually happened (potentially "
    "disadvantaging them); a negative gap means it under-predicts risk."
)

calibration_review = (
    fairness_summary.loc[fairness_summary["reliable_sample_size"]]
    .sort_values("calibration_gap", key=lambda col: col.abs(), ascending=False)
    [["segment_type", "segment_value", "n", "observed_default_rate",
      "mean_predicted_probability", "calibration_gap"]]
    .head(10)
)

print(calibration_review.to_string(index=False))

# SAVE OUTPUTS
print("\n" + "=" * 80)
print("SAVING FAIRNESS REVIEW OUTPUTS")
print("=" * 80)

fairness_summary.to_csv(
    OUTPUT_DIR / "fairness_disparate_impact_summary.csv", index=False
)

fairness_metadata = {
    "stage": "10_fairness_disparate_impact_review",
    "evaluation_population": "validation + test splits (out-of-sample)",
    "evaluation_population_size": int(total_n),
    "segments_reviewed": SEGMENT_COLUMNS_ALL,
    "min_reliable_group_size": MIN_GROUP_SIZE,
    "adverse_impact_ratio_thresholds": {
        "material_below": AIR_MATERIAL_THRESHOLD,
        "borderline_below": AIR_BORDERLINE_THRESHOLD,
        "methodology_note": (
            "The 80%/four-fifths rule is a US EEOC screening heuristic "
            "applied here for analytical convenience. It is not a South "
            "African legal standard. See PEPUDA and the National Credit "
            "Act for the applicable South African framework, and consult "
            "qualified legal counsel for any compliance determination."
        )
    },
    "groups_material_disparity": (
        material_flags[["segment_type", "segment_value"]]
        .to_dict(orient="records")
    ),
    "groups_borderline": (
        borderline_flags[["segment_type", "segment_value"]]
        .to_dict(orient="records")
    ),
    "scope_limitation": (
        "This dataset contains no owner/director demographic attributes "
        "(race, gender, disability, etc.), which are the actual "
        "protected characteristics under South African anti-"
        "discrimination and credit law. Province, industry sector and "
        "legal entity type were used as the best available proxies for "
        "a first-pass screen. This is not a substitute for a fairness "
        "audit against real demographic data, and passing this screen "
        "is not a compliance determination."
    ),
    "no_model_changes_made": True
}

with open(
    OUTPUT_DIR / "fairness_review_metadata.json", "w", encoding="utf-8"
) as file:
    json.dump(fairness_metadata, file, indent=4, default=str)

# COMPLETION
print("\n" + "=" * 80)
print("FAIRNESS & DISPARATE IMPACT REVIEW COMPLETE")
print("=" * 80)

print(f"\nGroups reviewed: {len(fairness_summary):,}")
print(f"Material disparity flags: {len(material_flags):,}")
print(f"Borderline flags: {len(borderline_flags):,}")
print(f"Groups with unreliable sample size: {len(unreliable_groups):,}")

print("\nOutputs saved to:")
print(OUTPUT_DIR)

print("\nGenerated files:")
print("  - fairness_disparate_impact_summary.csv")
print("  - fairness_review_metadata.json")

print(
    "\nReminder: this is a proxy-based screening tool, not a legal "
    "compliance determination. Flagged groups should be reviewed with "
    "someone qualified to advise on the National Credit Act and PEPUDA."
)

print("\nSource datasets and upstream stage outputs were not modified.")

print("\nNext stage:")
print(
    "11 — Recalibration trigger policy: formalize the PSI/CSI thresholds "
    "from Stage 09 and the fairness flags from Stage 10 into a single "
    "governance escalation process. Continuing on 03-governance."
)