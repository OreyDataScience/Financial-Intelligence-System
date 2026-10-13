"""
Phase 06 - Data Engineering: Cleaning & Validation (raw -> staging)
Orey Analytics - Cash Flow Intelligence

Reads 01-data/01-raw, standardizes formats, and detects data-quality issues with
rule-based logic only. The ground-truth issues log is NEVER read while cleaning -
it is used afterwards, in a separate evaluation step, to measure the detectors.

Raw fields are preserved untouched; standardized values and flags are added as
new columns so every staged row stays traceable to its raw source row.

Writes to 01-data/02-staging:
    business_profiles_staging.csv, bank_transactions_staging.csv,
    invoices_staging.csv, supplier_bills_staging.csv,
    detection-evaluation.csv, precision-evaluation.csv,
    detection-evaluation-report.md

Usage:
    python clean_and_validate.py        (paths resolve from this file's location)
"""

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd

# This file lives at: 02-data-engineering/02-cleaning/clean_and_validate.py
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_RAWDIR = _PROJECT_ROOT / "01-data" / "01-raw"
_DEFAULT_STAGINGDIR = _PROJECT_ROOT / "01-data" / "02-staging"

DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%d %b %Y"]
DELAYED_POSTING_THRESHOLD_DAYS = 7

# Descriptions that normally mean money OUT. A row like this recorded as a
# credit is a plausible sign-convention error. Deliberately specific: a generic
# word like "SETTLEMENT" also appears on legitimate inflows (card settlements).
OUTFLOW_KEYWORDS = ["SUPPLIER", "PAYROLL", "SUBCONTRACTOR", "CREDIT SETTLEMENT", "OPERATING EXPENSE"]

STATUS_MAP = {"paid": "paid", "partially paid": "partially_paid", "partially_paid": "partially_paid",
              "unpaid": "unpaid", "overdue": "overdue"}


def parse_date_flexible(value):
    if pd.isna(value) or value == "":
        return pd.NaT
    for fmt in DATE_FORMATS:
        try:
            return pd.to_datetime(value, format=fmt)
        except (ValueError, TypeError):
            continue
    try:
        return pd.to_datetime(value)
    except Exception:
        return pd.NaT


def normalize_description(desc):
    if pd.isna(desc):
        return ""
    return re.sub(r"\s+", " ", str(desc).upper().replace("-", " ").replace("_", " ")).strip()


def standardize_status(s):
    return STATUS_MAP.get(str(s).strip().lower(), str(s).strip().lower().replace(" ", "_"))


def is_blank(series):
    return series.isna() | (series.astype(str).str.strip() == "")


# ---------------------------------------------------------------------------
# business_profiles
# ---------------------------------------------------------------------------
def clean_business_profiles(df):
    df = df.copy()
    df["missing_employee_count"] = is_blank(df["employee_count"])
    df["missing_financial_year_end"] = is_blank(df["financial_year_end"])

    def parse_revenue(v):
        if pd.isna(v):
            return np.nan, False
        v = str(v)
        # Flag only real formatting (currency symbol / commas / letters). Every
        # column is loaded as text, so "arrived as a string" means nothing.
        was_formatted = bool(re.search(r"[A-Za-z,]", v))
        try:
            return float(v.replace("R", "").replace(",", "").strip()), was_formatted
        except ValueError:
            return np.nan, True

    parsed = df["annual_revenue"].apply(parse_revenue)
    df["annual_revenue_standardized"] = parsed.apply(lambda x: x[0])
    df["revenue_format_flagged"] = parsed.apply(lambda x: x[1])
    df["conflicting_profile_version"] = df.groupby("business_id")["business_id"].transform("count") > 1
    return df


# ---------------------------------------------------------------------------
# bank_transactions
# ---------------------------------------------------------------------------
def clean_bank_transactions(df):
    df = df.copy()
    df["transaction_date_std"] = df["transaction_date"].apply(parse_date_flexible)
    df["posting_date_std"] = df["posting_date"].apply(parse_date_flexible)

    df["missing_transaction_reference"] = is_blank(df["transaction_reference"])
    df["missing_balance_after_transaction"] = is_blank(df["balance_after_transaction"])

    # Signed amount: positive = money in, negative = money out.
    debit = pd.to_numeric(df["debit_amount"], errors="coerce").fillna(0)
    credit = pd.to_numeric(df["credit_amount"], errors="coerce").fillna(0)
    df["net_amount"] = credit - debit

    df["posting_delay_days"] = (df["posting_date_std"] - df["transaction_date_std"]).dt.days
    df["delayed_posting_flag"] = df["posting_delay_days"] >= DELAYED_POSTING_THRESHOLD_DAYS

    df["description_normalized"] = df["transaction_description"].apply(normalize_description)
    df["is_reversal"] = df["description_normalized"].str.startswith("REVERSAL")

    # Reversal rows are legitimately credits that carry outflow wording, so they
    # must not be mistaken for sign errors.
    has_outflow_kw = df["description_normalized"].apply(lambda d: any(k in d for k in OUTFLOW_KEYWORDS))
    df["possible_sign_inconsistency"] = has_outflow_kw & (credit > 0) & (debit == 0) & ~df["is_reversal"]

    key = (df["business_id"].astype(str) + "|" + df["transaction_date_std"].astype(str) + "|"
           + df["net_amount"].round(2).astype(str) + "|" + df["description_normalized"])
    dup_counts = key.groupby(key).transform("count")
    df["is_duplicate"] = (dup_counts > 1) & key.duplicated(keep="first")
    df["duplicate_group_size"] = dup_counts
    return df


# ---------------------------------------------------------------------------
# invoices / supplier bills
# ---------------------------------------------------------------------------
def clean_invoices(df):
    df = df.copy()
    df["invoice_date_std"] = df["invoice_date"].apply(parse_date_flexible)
    df["due_date_std"] = df["due_date"].apply(parse_date_flexible)
    df["payment_date_std"] = df["payment_date"].apply(parse_date_flexible)
    df["missing_due_date"] = is_blank(df["due_date"])
    df["invoice_status_standardized"] = df["invoice_status"].apply(standardize_status)

    amount = pd.to_numeric(df["invoice_amount"], errors="coerce")
    paid = pd.to_numeric(df["amount_paid"], errors="coerce")
    df["paid_amount_mismatch"] = (df["invoice_status_standardized"] == "paid") & ((amount - paid).abs() > 0.01 * amount)
    df["payment_before_invoice_flag"] = df["payment_date_std"].notna() & (df["payment_date_std"] < df["invoice_date_std"])

    key = df["business_id"] + "|" + df["invoice_id"]
    df["is_duplicate"] = (key.groupby(key).transform("count") > 1) & key.duplicated(keep="first")
    return df


def clean_supplier_bills(df):
    df = df.copy()
    df["bill_date_std"] = df["bill_date"].apply(parse_date_flexible)
    df["due_date_std"] = df["due_date"].apply(parse_date_flexible)
    df["payment_date_std"] = df["payment_date"].apply(parse_date_flexible)
    df["missing_supplier_id"] = is_blank(df["supplier_id"])
    df["bill_status_standardized"] = df["bill_status"].apply(standardize_status)

    amount = pd.to_numeric(df["bill_amount"], errors="coerce")
    paid = pd.to_numeric(df["amount_paid"], errors="coerce")
    df["paid_amount_mismatch"] = (df["bill_status_standardized"] == "paid") & ((amount - paid).abs() > 0.01 * amount)
    df["payment_before_bill_flag"] = df["payment_date_std"].notna() & (df["payment_date_std"] < df["bill_date_std"])

    key = df["business_id"] + "|" + df["bill_id"]
    df["is_duplicate"] = (key.groupby(key).transform("count") > 1) & key.duplicated(keep="first")
    return df


# ---------------------------------------------------------------------------
# Evaluation against the ground-truth issues log (TEST-ONLY)
# ---------------------------------------------------------------------------
# flag column -> ground-truth issue_type(s) it is meant to detect
FLAG_AUDIT = {
    "business_profiles_raw.csv": {
        "missing_employee_count": ["missing_value"],
        "missing_financial_year_end": ["missing_value"],
        "revenue_format_flagged": ["type_inconsistency"],
        "conflicting_profile_version": ["conflicting_record"],
    },
    "bank_transactions_raw.csv": {
        "missing_transaction_reference": ["missing_reference"],
        "missing_balance_after_transaction": ["missing_value"],
        "delayed_posting_flag": ["delayed_posting"],
        "possible_sign_inconsistency": ["sign_inconsistency"],
        "is_reversal": ["reversal"],
        "is_duplicate": ["duplicate"],
    },
    "invoices_raw.csv": {
        "missing_due_date": ["missing_value"],
        "payment_before_invoice_flag": ["payment_before_invoice"],
        "is_duplicate": ["duplicate"],
    },
    "supplier_bills_raw.csv": {
        "missing_supplier_id": ["missing_value"],
        "is_duplicate": ["duplicate"],
    },
}

# Issue types that staging cannot see by design (they need cross-source
# reconciliation) - evaluated later, in the processing stage.
DEFERRED_TO_RECONCILIATION = {"no_bank_receipt", "ledger_bank_amount_conflict"}


def evaluate_recall(issues_log, frames):
    results = []
    for dataset, flags in FLAG_AUDIT.items():
        staged = frames[dataset].drop_duplicates("source_record_id").set_index("source_record_id")
        subset = issues_log[issues_log["dataset"] == dataset]
        for issue_type in sorted(set(t for ts in flags.values() for t in ts)):
            relevant = subset[subset["issue_type"] == issue_type]
            if relevant.empty:
                continue
            cols = [c for c, ts in flags.items() if issue_type in ts]
            hits = 0
            for rec_id in relevant["source_record_id"]:
                if rec_id in staged.index and any(bool(staged.at[rec_id, c]) for c in cols):
                    hits += 1
            results.append(dict(dataset=dataset, issue_type=issue_type, total_injected=len(relevant),
                                detected=hits, detection_rate=round(hits / len(relevant), 3)))
    return pd.DataFrame(results)


def evaluate_precision(issues_log, frames):
    results = []
    for dataset, flags in FLAG_AUDIT.items():
        staged = frames[dataset]
        for flag_col, issue_types in flags.items():
            flagged = staged[staged[flag_col] == True]  # noqa: E712
            if flagged.empty:
                continue
            log_ids = set(issues_log[(issues_log["dataset"] == dataset)
                                     & (issues_log["issue_type"].isin(issue_types))]["source_record_id"])
            tp = int(flagged["source_record_id"].isin(log_ids).sum())
            results.append(dict(dataset=dataset, flag=flag_col, total_flagged=len(flagged),
                                true_positives=tp, false_positives=len(flagged) - tp,
                                precision=round(tp / len(flagged), 3)))
    return pd.DataFrame(results)


def main(rawdir, stagingdir):
    rawdir, stagingdir = Path(rawdir), Path(stagingdir)
    stagingdir.mkdir(parents=True, exist_ok=True)

    print("Loading raw data ...")
    profiles_raw = pd.read_csv(rawdir / "business_profiles_raw.csv", dtype=str)
    bank_raw = pd.read_csv(rawdir / "bank_transactions_raw.csv", dtype=str)
    invoices_raw = pd.read_csv(rawdir / "invoices_raw.csv", dtype=str)
    bills_raw = pd.read_csv(rawdir / "supplier_bills_raw.csv", dtype=str)

    print("Cleaning and flagging ...")
    profiles = clean_business_profiles(profiles_raw)
    bank = clean_bank_transactions(bank_raw)
    invoices = clean_invoices(invoices_raw)
    bills = clean_supplier_bills(bills_raw)

    profiles.to_csv(stagingdir / "business_profiles_staging.csv", index=False)
    bank.to_csv(stagingdir / "bank_transactions_staging.csv", index=False)
    invoices.to_csv(stagingdir / "invoices_staging.csv", index=False)
    bills.to_csv(stagingdir / "supplier_bills_staging.csv", index=False)

    # ---- test-only evaluation: the ONLY place the issues log is read ----
    issues_log = pd.read_csv(rawdir / "data-quality-issues-log.csv")
    frames = {"business_profiles_raw.csv": profiles, "bank_transactions_raw.csv": bank,
              "invoices_raw.csv": invoices, "supplier_bills_raw.csv": bills}
    recall = evaluate_recall(issues_log, frames)
    precision = evaluate_precision(issues_log, frames)
    recall.to_csv(stagingdir / "detection-evaluation.csv", index=False)
    precision.to_csv(stagingdir / "precision-evaluation.csv", index=False)

    overall = recall["detected"].sum() / recall["total_injected"].sum()
    deferred = issues_log[issues_log["issue_type"].isin(DEFERRED_TO_RECONCILIATION)]
    lines = ["# Staging: Detection Evaluation Report\n\n",
             "Test-only. Measures the staging detection rules against the synthetic ground-truth log. "
             "This evaluation, and the log it reads, do not exist in a real pipeline.\n\n",
             "## Recall - did we catch every injected issue?\n\n",
             f"**Overall recall (issue types staging can see): {overall:.1%}**\n\n",
             "| Dataset | Issue type | Injected | Detected | Rate |\n|---|---|---|---|---|\n"]
    for _, r in recall.iterrows():
        lines.append(f"| {r['dataset']} | {r['issue_type']} | {r['total_injected']} | {r['detected']} | {r['detection_rate']:.0%} |\n")
    lines.append(f"\n{len(deferred)} injected issues of type `no_bank_receipt` / `ledger_bank_amount_conflict` are "
                 "invisible to staging by design (they only appear when a ledger is compared with the bank). "
                 "They are evaluated in `03-processed`.\n\n")
    lines.append("## Precision - of everything flagged, how much was a real logged issue?\n\n"
                 "| Dataset | Flag | Flagged | True positives | False positives | Precision |\n|---|---|---|---|---|---|\n")
    for _, r in precision.iterrows():
        lines.append(f"| {r['dataset']} | {r['flag']} | {r['total_flagged']} | {r['true_positives']} | {r['false_positives']} | {r['precision']:.0%} |\n")
    (stagingdir / "detection-evaluation-report.md").write_text("".join(lines), encoding="utf-8")

    print(f"\nDone. Staging files written to: {stagingdir.resolve()}\n")
    print("".join(lines))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rawdir", default=str(_DEFAULT_RAWDIR))
    parser.add_argument("--stagingdir", default=str(_DEFAULT_STAGINGDIR))
    args = parser.parse_args()
    main(args.rawdir, args.stagingdir)
