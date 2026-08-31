"""
Orey Analytics
Financial Health Scoring — Governance

Stage 11 — Recalibration & Governance Trigger Policy

Purpose:
This is the closing stage of the Financial Health Scoring phase. It reads
the outputs of every prior monitoring/validation stage — statistical
validation (Stage 06), population/characteristic stability (Stage 09) and
the fairness screen (Stage 10) — and converts them into a single,
auditable governance decision: does anything need to happen, and if so,
what, by whom, and how urgently.

This stage makes no model changes itself. It is a decision layer that
sits above the model-build phase (01-population-model) and the individual
assessment phase (02-individual-assessment), which is why it lives in its
own sibling folder rather than inside either.

Governance tiers (defined explicitly below, not just implied by code):
    TIER 0 — CRITICAL: statistical validation itself has failed. Nothing
        below this matters until the model passes Stage 06 again.
    TIER 1 — RECALIBRATION RECOMMENDED: score-level population drift is
        material (PSI >= 0.25), or a fairness screen found a material,
        statistically significant disparity. The model's fitted
        assumptions likely no longer match the population it's scoring.
    TIER 2 — ESCALATE FOR REVIEW: moderate score drift, several features
        showing material characteristic shift, or a fairness screen
        found a material disparity that was not statistically
        significant (worth a human look before concluding either way).
    TIER 3 — MONITOR: minor/moderate signals present but nothing above
        threshold. No action required now; re-check next cycle.
    TIER 4 — NO ACTION: nothing flagged anywhere.

This stage appends every run to a persistent decision log
(governance_decision_log.csv) rather than overwriting it, since a
governance trail is only useful if it accumulates history across
monitoring cycles.

Key principles:
    1. No model, threshold or prior-stage output is changed here. This
       stage only reads and decides.
    2. Every governance tier is tied to an explicit, printed policy —
       not a black-box score — so the decision is auditable by someone
       who did not write this code.
    3. If any required upstream artifact is missing, this stage fails
       loudly rather than silently assuming "no issue".
"""

# IMPORTS
from pathlib import Path
from datetime import datetime, timezone
import json
import warnings

import pandas as pd

warnings.filterwarnings("ignore")

# PROJECT PATHS
# This stage reads from BOTH phase folders and writes to its own
# sibling folder. It locates the shared parent by walking up from its
# own location until it finds a directory containing both
# 01-population-model and 02-individual-assessment.

SCRIPT_DIR = Path(__file__).resolve().parent

POPULATION_MODEL_FOLDER_NAME = "01-population-model"
INDIVIDUAL_ASSESSMENT_FOLDER_NAME = "02-individual-assessment"
GOVERNANCE_FOLDER_NAME = "03-governance"

def find_phase_root(start_dir):
    """
    Walk upward from start_dir until a folder containing both phase
    folders is found. Checks up to 4 levels up, which comfortably
    covers this script living in <phase_root>/03-governance/scripts/.
    """

    current = start_dir

    for _ in range(5):
        if (
            (current / POPULATION_MODEL_FOLDER_NAME).is_dir()
            and (current / INDIVIDUAL_ASSESSMENT_FOLDER_NAME).is_dir()
        ):
            return current
        current = current.parent

    raise FileNotFoundError(
        f"Could not locate a folder containing both "
        f"'{POPULATION_MODEL_FOLDER_NAME}' and "
        f"'{INDIVIDUAL_ASSESSMENT_FOLDER_NAME}' by walking up from "
        f"{start_dir}. This stage expects both phase folders as "
        "siblings under one parent."
    )

PHASE_ROOT = find_phase_root(SCRIPT_DIR)

POPULATION_OUTPUT_DIR = PHASE_ROOT / POPULATION_MODEL_FOLDER_NAME / "outputs"
ASSESSMENT_OUTPUT_DIR = (
    PHASE_ROOT / INDIVIDUAL_ASSESSMENT_FOLDER_NAME / "outputs"
)
GOVERNANCE_DIR = PHASE_ROOT / GOVERNANCE_FOLDER_NAME
GOVERNANCE_OUTPUT_DIR = GOVERNANCE_DIR / "outputs"
GOVERNANCE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_VALIDATION_METADATA_FILE = (
    POPULATION_OUTPUT_DIR / "model_validation_metadata.json"
)
FAIRNESS_METADATA_FILE = (
    POPULATION_OUTPUT_DIR / "fairness_review_metadata.json"
)
SCORE_MONITORING_METADATA_FILE = (
    ASSESSMENT_OUTPUT_DIR / "score_monitoring_metadata.json"
)

DECISION_LOG_FILE = GOVERNANCE_OUTPUT_DIR / "governance_decision_log.csv"
LATEST_DECISION_FILE = (
    GOVERNANCE_OUTPUT_DIR / "governance_decision_latest.json"
)

# CONFIGURATION — explicit policy thresholds, printed and saved for audit
PSI_MODERATE_THRESHOLD = 0.10
PSI_MATERIAL_THRESHOLD = 0.25

GOVERNANCE_POLICY = {
    "TIER_0_CRITICAL": {
        "label": "CRITICAL — statistical validation failed",
        "action": (
            "Halt automated production decisioning on this scorecard. "
            "Escalate immediately to the model owner. Do not resume "
            "production use until the model passes Stage 06 validation."
        ),
        "owner": "Head of Model Risk",
        "sla_business_days": 1
    },
    "TIER_1_RECALIBRATE": {
        "label": "Recalibration recommended",
        "action": (
            "Score-level population drift or a significant fairness "
            "disparity indicates the model's fitted assumptions no "
            "longer match the current population. Schedule a full "
            "recalibration (re-run Stages 02-07 on refreshed data) and "
            "review whether the affected features/segments need "
            "structural changes, not just refitting."
        ),
        "owner": "Model Risk Committee",
        "sla_business_days": 10
    },
    "TIER_2_ESCALATE": {
        "label": "Escalate for review",
        "action": (
            "Material signals present but not yet conclusive (e.g. a "
            "fairness flag without statistical significance, or several "
            "features drifting without the overall score drifting). "
            "A human review is warranted before deciding whether "
            "recalibration is needed."
        ),
        "owner": "Model Risk Analyst",
        "sla_business_days": 15
    },
    "TIER_3_MONITOR": {
        "label": "Monitor",
        "action": (
            "Minor or moderate signals present, below escalation "
            "thresholds. No action required now. Re-run this review "
            "next monitoring cycle and watch for a worsening trend."
        ),
        "owner": "Model Risk Analyst",
        "sla_business_days": 30
    },
    "TIER_4_NO_ACTION": {
        "label": "No action",
        "action": "No signals flagged. Continue routine monitoring.",
        "owner": "Model Risk Analyst",
        "sla_business_days": None
    }
}

# HEADER
print("=" * 80)
print("OREY ANALYTICS — FINANCIAL HEALTH SCORING")
print("11 — RECALIBRATION & GOVERNANCE TRIGGER POLICY")
print("=" * 80)

print(f"\nPhase root detected: {PHASE_ROOT}")
print(f"Reading population model outputs from: {POPULATION_OUTPUT_DIR}")
print(f"Reading individual assessment outputs from: {ASSESSMENT_OUTPUT_DIR}")
print(f"Writing governance outputs to: {GOVERNANCE_OUTPUT_DIR}")

# CHECK REQUIRED FILES
print("\nChecking required upstream artifacts...")

required_files = {
    "Stage 06 (statistical validation)": MODEL_VALIDATION_METADATA_FILE,
    "Stage 09 (score monitoring)": SCORE_MONITORING_METADATA_FILE,
    "Stage 10 (fairness review)": FAIRNESS_METADATA_FILE,
}

missing = [
    f"{label}: {path}" for label, path in required_files.items()
    if not path.exists()
]

if missing:
    raise FileNotFoundError(
        "Required upstream artifacts are missing. Run the corresponding "
        "stage first:\n  " + "\n  ".join(missing)
    )

print("All required upstream artifacts found.")

# LOAD UPSTREAM METADATA
print("\nLoading upstream stage outputs...")

with open(MODEL_VALIDATION_METADATA_FILE, "r", encoding="utf-8") as file:
    validation_metadata = json.load(file)

with open(SCORE_MONITORING_METADATA_FILE, "r", encoding="utf-8") as file:
    monitoring_metadata = json.load(file)

with open(FAIRNESS_METADATA_FILE, "r", encoding="utf-8") as file:
    fairness_metadata = json.load(file)

model_validation_pass = bool(
    validation_metadata.get("model_validation_pass", False)
)

score_psi = float(monitoring_metadata.get("score_psi", 0.0))
score_psi_interpretation = monitoring_metadata.get(
    "score_psi_interpretation", "Unknown"
)
features_material_shift = monitoring_metadata.get(
    "features_material_shift", []
)
features_moderate_shift = monitoring_metadata.get(
    "features_moderate_shift", []
)

fairness_material = fairness_metadata.get(
    "groups_material_disparity", []
)
fairness_borderline = fairness_metadata.get("groups_borderline", [])

# Cross-reference material fairness flags against statistical
# significance recorded in the full fairness summary CSV, if available,
# since the metadata file only lists group identity, not significance.
fairness_summary_file = (
    POPULATION_OUTPUT_DIR / "fairness_disparate_impact_summary.csv"
)

fairness_material_significant_count = 0

if fairness_summary_file.exists() and len(fairness_material) > 0:
    fairness_summary = pd.read_csv(fairness_summary_file)

    material_rows = fairness_summary.loc[
        fairness_summary["air_flag"] == "Material disparity — investigate"
    ]

    fairness_material_significant_count = int(
        material_rows["approval_significant"].sum()
    )

print(
    f"\nStatistical validation pass: {model_validation_pass}"
)
print(f"Score PSI: {score_psi:.4f} ({score_psi_interpretation})")
print(f"Features with material CSI shift: {len(features_material_shift)}")
print(f"Features with moderate CSI shift: {len(features_moderate_shift)}")
print(f"Fairness groups with material disparity: {len(fairness_material)}")
print(
    "  of which statistically significant: "
    f"{fairness_material_significant_count}"
)
print(f"Fairness groups borderline: {len(fairness_borderline)}")

# APPLY GOVERNANCE POLICY
print("\n" + "=" * 80)
print("APPLYING GOVERNANCE POLICY")
print("=" * 80)

if not model_validation_pass:
    tier = "TIER_0_CRITICAL"

elif (
    score_psi >= PSI_MATERIAL_THRESHOLD
    or fairness_material_significant_count > 0
):
    tier = "TIER_1_RECALIBRATE"

elif (
    len(fairness_material) > 0
    or len(features_material_shift) >= 3
):
    tier = "TIER_2_ESCALATE"

elif (
    score_psi >= PSI_MODERATE_THRESHOLD
    or len(features_material_shift) > 0
    or len(features_moderate_shift) > 0
    or len(fairness_borderline) > 0
):
    tier = "TIER_3_MONITOR"

else:
    tier = "TIER_4_NO_ACTION"

policy = GOVERNANCE_POLICY[tier]

print(f"\nGovernance tier: {tier}")
print(f"Status: {policy['label']}")
print(f"Required action: {policy['action']}")
print(f"Owner: {policy['owner']}")
print(f"SLA (business days): {policy['sla_business_days']}")

# BUILD DECISION RECORD
run_timestamp = datetime.now(timezone.utc).isoformat()

decision_record = {
    "run_timestamp_utc": run_timestamp,
    "model_validation_pass": model_validation_pass,
    "score_psi": score_psi,
    "score_psi_interpretation": score_psi_interpretation,
    "features_material_shift_count": len(features_material_shift),
    "features_material_shift": features_material_shift,
    "features_moderate_shift_count": len(features_moderate_shift),
    "fairness_material_count": len(fairness_material),
    "fairness_material_significant_count": (
        fairness_material_significant_count
    ),
    "fairness_borderline_count": len(fairness_borderline),
    "governance_tier": tier,
    "governance_status": policy["label"],
    "required_action": policy["action"],
    "owner": policy["owner"],
    "sla_business_days": policy["sla_business_days"],
}

# APPEND TO PERSISTENT DECISION LOG
print("\n" + "=" * 80)
print("UPDATING GOVERNANCE DECISION LOG")
print("=" * 80)

decision_record_flat = decision_record.copy()
decision_record_flat["features_material_shift"] = "; ".join(
    features_material_shift
)

new_row = pd.DataFrame([decision_record_flat])

if DECISION_LOG_FILE.exists():
    existing_log = pd.read_csv(DECISION_LOG_FILE)
    updated_log = pd.concat([existing_log, new_row], ignore_index=True)
    print(
        f"Appending to existing decision log "
        f"({len(existing_log)} prior run(s))."
    )
else:
    updated_log = new_row
    print("Creating new decision log (first run).")

updated_log.to_csv(DECISION_LOG_FILE, index=False)

# TREND CHECK — has the tier worsened across recent runs?
if len(updated_log) >= 2:

    tier_severity = {
        "TIER_4_NO_ACTION": 0, "TIER_3_MONITOR": 1,
        "TIER_2_ESCALATE": 2, "TIER_1_RECALIBRATE": 3,
        "TIER_0_CRITICAL": 4
    }

    recent_tiers = updated_log["governance_tier"].tail(3).map(
        tier_severity
    )

    if recent_tiers.is_monotonic_increasing and recent_tiers.iloc[-1] > (
        recent_tiers.iloc[0]
    ):
        print(
            "\nTREND WARNING: governance severity has increased over "
            "the last "
            f"{len(recent_tiers)} runs. Even if the current tier alone "
            "doesn't require escalation, a worsening trend does."
        )

# SAVE LATEST DECISION SNAPSHOT
with open(LATEST_DECISION_FILE, "w", encoding="utf-8") as file:
    json.dump(decision_record, file, indent=4, default=str)

with open(
    GOVERNANCE_OUTPUT_DIR / "governance_policy_definition.json",
    "w",
    encoding="utf-8"
) as file:
    json.dump(
        {
            "psi_thresholds": {
                "moderate": PSI_MODERATE_THRESHOLD,
                "material": PSI_MATERIAL_THRESHOLD
            },
            "tiers": GOVERNANCE_POLICY
        },
        file,
        indent=4,
        default=str
    )

# COMPLETION
print("\n" + "=" * 80)
print("GOVERNANCE REVIEW COMPLETE")
print("=" * 80)

print(f"\nCurrent governance tier: {tier} — {policy['label']}")
print(f"Total runs in decision log: {len(updated_log)}")

print("\nOutputs saved to:")
print(GOVERNANCE_OUTPUT_DIR)

print("\nGenerated/updated files:")
print("  - governance_decision_log.csv   (append-only history)")
print("  - governance_decision_latest.json")
print("  - governance_policy_definition.json")

print(
    "\nThis is the closing stage of the Financial Health Scoring phase:"
)
print("  01-07  Population model build and statistical validation")
print("  08     Individual applicant scoring and reason codes")
print("  09     Score monitoring — population/characteristic stability")
print("  10     Fairness and disparate impact review")
print("  11     Recalibration and governance trigger policy (this stage)")

print(
    "\nOngoing operation of this system — running Stages 08-11 on each "
    "new applicant batch/monitoring cycle — is a recurring process from "
    "here, not a further build stage."
)

print("\nSource datasets and upstream stage outputs were not modified.")