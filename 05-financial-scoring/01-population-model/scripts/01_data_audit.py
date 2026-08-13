"""
Orey Analytics
Financial Health Scoring — Population Model

Purpose: Perform an initial data audit of the Financial Health Scoring population, 
applicant population, and transaction sample.

Producing audit outputs for the next stages of the modelling pipeline.
"""

# IMPORTS
from pathlib import Path
import pandas as pd
import numpy as np

# PROJECT PATHS
SCRIPT_DIR = Path(__file__).resolve().parent
MODEL_DIR = SCRIPT_DIR.parent

DATA_DIR = MODEL_DIR / "data"
OUTPUT_DIR = MODEL_DIR / "outputs"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# DATA FILES
PANEL_FILE = DATA_DIR / "sme financial health panel.csv"
APPLICANT_FILE = DATA_DIR / "sme applicant scoring population.csv"
TRANSACTION_FILE = DATA_DIR / "sme transactions sample.csv"

# LOAD DATA
print("=" * 80)
print("OREY ANALYTICS — FINANCIAL HEALTH SCORING")
print("01 — DATA AUDIT")
print("=" * 80)

print("\nLoading datasets...")

panel = pd.read_csv(PANEL_FILE)
applicant = pd.read_csv(APPLICANT_FILE)
transactions = pd.read_csv(TRANSACTION_FILE)

print("Datasets loaded successfully.")

# BASIC DATASET INFORMATION
def dataset_summary(name, df):
    """Print basic information about a dataset."""

    print("\n" + "=" * 80)
    print(name)
    print("=" * 80)

    print(f"Rows: {df.shape[0]:,}")
    print(f"Columns: {df.shape[1]:,}")
    print(f"Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

    print("\nColumn names:")
    for column in df.columns:
        print(f"  - {column}")

dataset_summary("CORE FINANCIAL HEALTH PANEL", panel)
dataset_summary("APPLICANT SCORING POPULATION", applicant)
dataset_summary("TRANSACTION SAMPLE", transactions)

# DATA TYPES
def datatype_summary(name, df):
    """Display variable data types."""

    print("\n" + "=" * 80)
    print(f"{name} — DATA TYPES")
    print("=" * 80)

    dtype_table = pd.DataFrame({
        "column": df.columns,
        "dtype": df.dtypes.astype(str).values,
        "unique_values": [
            df[column].nunique(dropna=True)
            for column in df.columns
        ]
    })

    print(dtype_table.to_string(index=False))

    return dtype_table

panel_dtypes = datatype_summary(
    "CORE PANEL",
    panel
)

applicant_dtypes = datatype_summary(
    "APPLICANT POPULATION",
    applicant
)

transaction_dtypes = datatype_summary(
    "TRANSACTIONS",
    transactions
)

# MISSING VALUE ANALYSIS
def missingness_summary(name, df):
    """Calculate missing values and missing percentages."""

    missing = df.isna().sum()
    missing_pct = (missing / len(df)) * 100

    result = pd.DataFrame({
        "column": df.columns,
        "missing_count": missing.values,
        "missing_pct": missing_pct.values
    })

    result = result.sort_values(
        "missing_pct",
        ascending=False
    )

    print("\n" + "=" * 80)
    print(f"{name} — MISSINGNESS")
    print("=" * 80)

    print(
        result[result["missing_count"] > 0]
        .to_string(index=False)
    )

    return result

panel_missing = missingness_summary(
    "CORE PANEL",
    panel
)

applicant_missing = missingness_summary(
    "APPLICANT POPULATION",
    applicant
)

transaction_missing = missingness_summary(
    "TRANSACTIONS",
    transactions
)

# DUPLICATE ANALYSIS
def duplicate_summary(name, df):
    """Check for duplicate rows."""

    duplicate_count = df.duplicated().sum()

    print("\n" + "=" * 80)
    print(f"{name} — DUPLICATES")
    print("=" * 80)

    print(f"Duplicate rows: {duplicate_count:,}")

    return duplicate_count

panel_duplicates = duplicate_summary(
    "CORE PANEL",
    panel
)

applicant_duplicates = duplicate_summary(
    "APPLICANT POPULATION",
    applicant
)

transaction_duplicates = duplicate_summary(
    "TRANSACTIONS",
    transactions
)

# SME/BUSINESS COUNTS
print("\n" + "=" * 80)
print("BUSINESS COUNTS")
print("=" * 80)

if "business_id" in panel.columns:
    print(
        "Unique businesses in core panel:",
        f"{panel['business_id'].nunique():,}"
    )

if "business_id" in applicant.columns:
    print(
        "Unique businesses in applicant population:",
        f"{applicant['business_id'].nunique():,}"
    )

if "business_id" in transactions.columns:
    print(
        "Unique businesses in transaction sample:",
        f"{transactions['business_id'].nunique():,}"
    )

# SNAPSHOT STRUCTURE
if "business_id" in panel.columns and "snapshot_date" in panel.columns:

    print("\n" + "=" * 80)
    print("CORE PANEL — OBSERVATIONS PER BUSINESS")
    print("=" * 80)

    observations_per_business = (
        panel
        .groupby("business_id")
        .size()
        .describe()
    )

    print(observations_per_business)

# DATE RANGES
def date_range_summary(name, df, date_columns):
    """Display date ranges for available date columns."""

    print("\n" + "=" * 80)
    print(f"{name} — DATE RANGES")
    print("=" * 80)

    for column in date_columns:

        if column not in df.columns:
            continue

        dates = pd.to_datetime(
            df[column],
            errors="coerce"
        )

        print(f"\n{column}")

        print(
            f"  Minimum: {dates.min()}"
        )

        print(
            f"  Maximum: {dates.max()}"
        )

        print(
            f"  Invalid/missing dates: {dates.isna().sum():,}"
        )

date_range_summary(
    "CORE PANEL",
    panel,
    [
        "snapshot_date",
        "outcome_window_end"
    ]
)

date_range_summary(
    "APPLICANT POPULATION",
    applicant,
    [
        "snapshot_date"
    ]
)

date_range_summary(
    "TRANSACTIONS",
    transactions,
    [
        "transaction_date"
    ]
)

# TARGET ANALYSIS
if "default_event_12m" in panel.columns:

    print("\n" + "=" * 80)
    print("DEFAULT TARGET ANALYSIS")
    print("=" * 80)

    target_counts = (
        panel["default_event_12m"]
        .value_counts(dropna=False)
        .sort_index()
    )

    print("\nTarget counts:")
    print(target_counts)

    target_pct = (
        panel["default_event_12m"]
        .value_counts(normalize=True, dropna=False)
        .sort_index()
        * 100
    )

    print("\nTarget percentages:")
    print(target_pct)

# OUTCOME OBSERVABILITY
if "outcome_observable" in panel.columns:

    print("\n" + "=" * 80)
    print("OUTCOME OBSERVABILITY")
    print("=" * 80)

    print(
        panel["outcome_observable"]
        .value_counts(dropna=False)
    )

# MODEL SPLIT
if "model_split" in panel.columns:

    print("\n" + "=" * 80)
    print("MODEL SPLIT")
    print("=" * 80)

    split_counts = (
        panel["model_split"]
        .value_counts(dropna=False)
    )

    print(split_counts)

    split_pct = (
        panel["model_split"]
        .value_counts(normalize=True, dropna=False)
        * 100
    )

    print("\nPercentage:")
    print(split_pct)

# CATEGORICAL VARIABLE SUMMARY
print("\n" + "=" * 80)
print("CATEGORICAL VARIABLES — CORE PANEL")
print("=" * 80)

categorical_columns = panel.select_dtypes(
    include=["object", "category", "bool"]
).columns

for column in categorical_columns:

    print(f"\n{column}")

    print(
        panel[column]
        .value_counts(dropna=False)
        .head(20)
        .to_string()
    )

# NUMERICAL SUMMARY
print("\n" + "=" * 80)
print("NUMERICAL VARIABLE SUMMARY")
print("=" * 80)

numeric_columns = panel.select_dtypes(
    include=np.number
).columns

numeric_summary = (
    panel[numeric_columns]
    .describe()
    .T
)

print(numeric_summary.to_string())

# TRANSACTION TYPE ANALYSIS
if "transaction_type" in transactions.columns:

    print("\n" + "=" * 80)
    print("TRANSACTION TYPES")
    print("=" * 80)

    print(
        transactions["transaction_type"]
        .value_counts(dropna=False)
        .to_string()
    )

# TRANSACTION STATUS ANALYSIS
if "transaction_status" in transactions.columns:

    print("\n" + "=" * 80)
    print("TRANSACTION STATUSES")
    print("=" * 80)

    print(
        transactions["transaction_status"]
        .value_counts(dropna=False)
        .to_string()
    )

# POTENTIAL LEAKAGE VARIABLES
print("\n" + "=" * 80)
print("POTENTIAL TARGET / LEAKAGE VARIABLES")
print("=" * 80)

leakage_keywords = [
    "default",
    "outcome",
    "writeoff",
    "write_off",
    "restructur",
    "past_due",
    "judgment",
    "judgement"
]

potential_leakage = []

for column in panel.columns:

    column_lower = column.lower()

    if any(
        keyword in column_lower
        for keyword in leakage_keywords
    ):
        potential_leakage.append(column)

for column in potential_leakage:
    print(f"  - {column}")

# SAVE AUDIT OUTPUTS
print("\n" + "=" * 80)
print("SAVING AUDIT OUTPUTS")
print("=" * 80)


panel_dtypes.to_csv(
    OUTPUT_DIR / "panel_data_types.csv",
    index=False
)

applicant_dtypes.to_csv(
    OUTPUT_DIR / "applicant_data_types.csv",
    index=False
)

transaction_dtypes.to_csv(
    OUTPUT_DIR / "transaction_data_types.csv",
    index=False
)

panel_missing.to_csv(
    OUTPUT_DIR / "panel_missingness.csv",
    index=False
)

applicant_missing.to_csv(
    OUTPUT_DIR / "applicant_missingness.csv",
    index=False
)

transaction_missing.to_csv(
    OUTPUT_DIR / "transaction_missingness.csv",
    index=False
)

numeric_summary.to_csv(
    OUTPUT_DIR / "panel_numeric_summary.csv"
)

# COMPLETION
print("\n" + "=" * 80)
print("DATA AUDIT COMPLETE")
print("=" * 80)

print(f"\nAudit outputs saved to:")
print(OUTPUT_DIR)

print("\nNo source datasets were modified.")