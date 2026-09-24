"""
Phase 06 Data Engineering: Cleaning & Validation
Orey Analytics Cash Flow Intelligence

Reads 01-data/01-raw, standardizes formats, detects data-quality issues using
rule-based logic (NOT by reading the issues log - that would be cheating),
and writes staging datasets to 01-data/02-staging.

Then, separately, evaluates detection performance against
data-quality-issues-log.csv (ground truth, test-only) and writes a
detection report. This evaluation step is a validation/testing concern,
not part of the pipeline logic itself.

Usage:
    python clean_and_validate.py --rawdir ../../01-data/01-raw --stagingdir ../../01-data/02-staging
"""

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd

DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%d %b %Y"]

# Keywords that strongly imply an outflow; if money shows up as a credit
# on a transaction matching these, it's a plausible sign-convention error.
OUTFLOW_KEYWORDS = ["SUPPLIER", "PAYROLL", "SUBCONTRACTOR", "CREDIT SETTLEMENT", "OPERATING EXPENSE"]

DELAYED_POSTING_THRESHOLD_DAYS = 7

def parse_date_flexible(value):
    if pd.isna(value) or value == "":
        return pd.NaT
    for fmt in DATE_FORMATS:
        try:
            return pd.to_datetime(value, format=fmt)
        except (ValueError, TypeError):
            continue
    # last resort - let pandas guess
    try:
        return pd.to_datetime(value)
    except Exception:
        return pd.NaT

def normalize_description(desc):
    if pd.isna(desc):
        return ""
    return str(desc).upper().replace("-", " ").replace("_", " ").strip()

# ---------------------------------------------------------------------------
# business_profiles
# ---------------------------------------------------------------------------
def clean_business_profiles(df):
    df = df.copy()
    df["missing_employee_count"] = df["employee_count"].isna() | (df["employee_count"] == "")
    df["missing_financial_year_end"] = df["financial_year_end"].isna() | (df["financial_year_end"] == "")

    def parse_revenue(v):
        if pd.isna(v):
            return np.nan, False
        v = str(v)
        # Flag only if the raw string actually contains formatting chars
        # (currency symbol, comma, letters) - not just because it arrived as text,
        # since every column is loaded as str for safety.
        was_formatted = bool(re.search(r"[A-Za-z,]", v))
        cleaned = v.replace("R", "").replace(",", "").strip()
        try:
            return float(cleaned), was_formatted
        except ValueError:
            return np.nan, True

    parsed = df["annual_revenue"].apply(parse_revenue)
    df["annual_revenue_standardized"] = parsed.apply(lambda x: x[0])
    df["revenue_format_flagged"] = parsed.apply(lambda x: x[1])

    # Conflicting duplicate profile versions: more than one row per business_id
    dup_counts = df.groupby("business_id")["business_id"].transform("count")
    df["conflicting_profile_version"] = dup_counts > 1

    return df

# ---------------------------------------------------------------------------
# bank_transactions
# ---------------------------------------------------------------------------
def clean_bank_transactions(df):
    df = df.copy()

    df["transaction_date_std"] = df["transaction_date"].apply(parse_date_flexible)
    df["posting_date_std"] = df["posting_date"].apply(parse_date_flexible)

    df["missing_transaction_reference"] = df["transaction_reference"].isna() | (df["transaction_reference"] == "")
    df["missing_balance_after_transaction"] = df["balance_after_transaction"].isna() | (df["balance_after_transaction"] == "")

    # Net amount: positive = inflow, negative = outflow
    debit = pd.to_numeric(df["debit_amount"], errors="coerce").fillna(0)
    credit = pd.to_numeric(df["credit_amount"], errors="coerce").fillna(0)
    df["net_amount"] = credit - debit

    # Delayed posting
    delay_days = (df["posting_date_std"] - df["transaction_date_std"]).dt.days
    df["posting_delay_days"] = delay_days
    df["delayed_posting_flag"] = delay_days >= DELAYED_POSTING_THRESHOLD_DAYS

    # Sign-inconsistency heuristic: outflow-keyword description but recorded as credit
    df["description_normalized"] = df["transaction_description"].apply(normalize_description)
    has_outflow_kw = df["description_normalized"].apply(
        lambda d: any(kw in d for kw in OUTFLOW_KEYWORDS)
    )
    recorded_as_credit_only = (credit > 0) & (debit == 0)
    df["possible_sign_inconsistency"] = has_outflow_kw & recorded_as_credit_only

    # Reversal detection: explicit "REVERSAL" marker in description
    df["is_reversal"] = df["description_normalized"].str.startswith("REVERSAL")

    # Duplicate detection: same business, date, amount, normalized description
    dup_key = (
        df["business_id"].astype(str) + "|"
        + df["transaction_date_std"].astype(str) + "|"
        + df["net_amount"].round(2).astype(str) + "|"
        + df["description_normalized"]
    )
    df["_dup_key"] = dup_key
    dup_counts = df.groupby("_dup_key")["_dup_key"].transform("count")
    is_first = ~df.duplicated(subset="_dup_key", keep="first")
    df["is_duplicate"] = (dup_counts > 1) & (~is_first)
    df["duplicate_group_size"] = dup_counts
    df = df.drop(columns=["_dup_key"])

    return df

# ---------------------------------------------------------------------------
# invoices
# ---------------------------------------------------------------------------
STATUS_MAP = {
    "paid": "paid", "PAID": "paid", "Paid": "paid",
    "partially paid": "partially_paid", "Partially Paid": "partially_paid",
    "unpaid": "unpaid", "Unpaid": "unpaid",
    "overdue": "overdue", "Overdue": "overdue",
}

def clean_invoices(df):
    df = df.copy()
    df["invoice_date_std"] = df["invoice_date"].apply(parse_date_flexible)
    df["due_date_std"] = df["due_date"].apply(parse_date_flexible)
    df["payment_date_std"] = df["payment_date"].apply(parse_date_flexible)

    df["missing_due_date"] = df["due_date"].isna() | (df["due_date"] == "")

    df["invoice_status_standardized"] = df["invoice_status"].map(
        lambda s: STATUS_MAP.get(str(s).strip(), str(s).strip().lower().replace(" ", "_"))
    )

    invoice_amount = pd.to_numeric(df["invoice_amount"], errors="coerce")
    amount_paid = pd.to_numeric(df["amount_paid"], errors="coerce")
    is_paid = df["invoice_status_standardized"] == "paid"
    df["paid_amount_mismatch"] = is_paid & ((invoice_amount - amount_paid).abs() > 0.01 * invoice_amount)

    df["payment_before_invoice_flag"] = (
        df["payment_date_std"].notna() & (df["payment_date_std"] < df["invoice_date_std"])
    )

    # Duplicate detection: same business_id + invoice_id appearing more than once
    dup_counts = df.groupby(["business_id", "invoice_id"])["invoice_id"].transform("count")
    is_first = ~df.duplicated(subset=["business_id", "invoice_id"], keep="first")
    df["is_duplicate"] = (dup_counts > 1) & (~is_first)

    return df

# ---------------------------------------------------------------------------
# supplier_bills
# ---------------------------------------------------------------------------
def clean_supplier_bills(df):
    df = df.copy()
    df["bill_date_std"] = df["bill_date"].apply(parse_date_flexible)
    df["due_date_std"] = df["due_date"].apply(parse_date_flexible)
    df["payment_date_std"] = df["payment_date"].apply(parse_date_flexible)

    df["missing_supplier_id"] = df["supplier_id"].isna() | (df["supplier_id"] == "")

    bill_amount = pd.to_numeric(df["bill_amount"], errors="coerce")
    amount_paid = pd.to_numeric(df["amount_paid"], errors="coerce")
    is_paid = df["bill_status"].str.lower() == "paid"
    df["paid_amount_mismatch"] = is_paid & ((bill_amount - amount_paid).abs() > 0.01 * bill_amount)

    dup_counts = df.groupby(["business_id", "bill_id"])["bill_id"].transform("count")
    is_first = ~df.duplicated(subset=["business_id", "bill_id"], keep="first")
    df["is_duplicate"] = (dup_counts > 1) & (~is_first)

    return df

# ---------------------------------------------------------------------------
# Detection evaluation against ground-truth issues log (TEST-ONLY)
# ---------------------------------------------------------------------------
FLAG_MAP = {
    "business_profiles_raw.csv": {
        "missing_value": ["missing_employee_count", "missing_financial_year_end"],
        "type_inconsistency": ["revenue_format_flagged"],
        "conflicting_record": ["conflicting_profile_version"],
    },
    "bank_transactions_raw.csv": {
        "delayed_posting": ["delayed_posting_flag"],
        "duplicate": ["is_duplicate"],
        "missing_reference": ["missing_transaction_reference"],
        "missing_value": ["missing_balance_after_transaction"],
        "reversal": ["is_reversal"],
        "sign_inconsistency": ["possible_sign_inconsistency"],
    },
    "invoices_raw.csv": {
        "duplicate": ["is_duplicate"],
        "missing_value": ["missing_due_date"],
        "amount_mismatch": ["paid_amount_mismatch"],
    },
    "supplier_bills_raw.csv": {
        "duplicate": ["is_duplicate"],
        "missing_value": ["missing_supplier_id"],
    },
}

# Flags to audit for precision, and which ground-truth issue_type(s) they're
# meant to correspond to. A flag with an empty list has no logged issue_type
# to compare against - it's either a genuine finding the generator didn't
# log as an "issue" at all, or a pure heuristic with no ground truth.
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
        "paid_amount_mismatch": ["amount_mismatch"],
        "payment_before_invoice_flag": [],  # not logged by generator - genuine extra finding
        "is_duplicate": ["duplicate"],
    },
    "supplier_bills_raw.csv": {
        "missing_supplier_id": ["missing_value"],
        "paid_amount_mismatch": [],  # generator doesn't log this for bills
        "is_duplicate": ["duplicate"],
    },
}

def evaluate_precision(issues_log, staged_frames):
    results = []
    for dataset, flags in FLAG_AUDIT.items():
        staged_df = staged_frames[dataset]
        for flag_col, issue_types in flags.items():
            if flag_col not in staged_df.columns:
                continue
            flagged = staged_df[staged_df[flag_col] == True]
            total_flagged = len(flagged)
            if total_flagged == 0:
                continue

            if not issue_types:
                results.append(dict(
                    dataset=dataset, flag=flag_col, total_flagged=total_flagged,
                    true_positives="n/a", false_positives="n/a", precision="n/a (no logged issue_type)",
                ))
                continue

            log_ids = set(
                issues_log[
                    (issues_log["dataset"] == dataset) & (issues_log["issue_type"].isin(issue_types))
                ]["source_record_id"]
            )
            tp = flagged["source_record_id"].isin(log_ids).sum()
            fp = total_flagged - tp
            precision = round(tp / total_flagged, 3) if total_flagged else None
            results.append(dict(
                dataset=dataset, flag=flag_col, total_flagged=int(total_flagged),
                true_positives=int(tp), false_positives=int(fp), precision=precision,
            ))
    return pd.DataFrame(results)

def evaluate_detection(issues_log, staged_frames):
    results = []
    for dataset, flag_map in FLAG_MAP.items():
        staged_df = staged_frames[dataset]
        staged_df = staged_df.set_index("source_record_id")
        subset = issues_log[issues_log["dataset"] == dataset]

        for issue_type, flag_cols in flag_map.items():
            relevant = subset[subset["issue_type"] == issue_type]
            total = len(relevant)
            if total == 0:
                continue
            hits = 0
            for _, row in relevant.iterrows():
                rec_id = row["source_record_id"]
                if rec_id not in staged_df.index:
                    continue
                staged_row = staged_df.loc[rec_id]
                if isinstance(staged_row, pd.DataFrame):
                    staged_row = staged_row.iloc[0]
                if any(bool(staged_row.get(c, False)) for c in flag_cols):
                    hits += 1
            results.append(dict(dataset=dataset, issue_type=issue_type,
                                 total_injected=total, detected=hits,
                                 detection_rate=round(hits / total, 3)))
    return pd.DataFrame(results)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main(rawdir, stagingdir):
    rawdir = Path(rawdir)
    stagingdir = Path(stagingdir)
    stagingdir.mkdir(parents=True, exist_ok=True)

    print("Loading raw data...")
    profiles_raw = pd.read_csv(rawdir / "business_profiles_raw.csv", dtype=str)
    bank_raw = pd.read_csv(rawdir / "bank_transactions_raw.csv", dtype=str)
    invoices_raw = pd.read_csv(rawdir / "invoices_raw.csv", dtype=str)
    bills_raw = pd.read_csv(rawdir / "supplier_bills_raw.csv", dtype=str)
    issues_log = pd.read_csv(rawdir / "data-quality-issues-log.csv")

    print("Cleaning business_profiles...")
    profiles_staged = clean_business_profiles(profiles_raw)
    print("Cleaning bank_transactions...")
    bank_staged = clean_bank_transactions(bank_raw)
    print("Cleaning invoices...")
    invoices_staged = clean_invoices(invoices_raw)
    print("Cleaning supplier_bills...")
    bills_staged = clean_supplier_bills(bills_raw)

    profiles_staged.to_csv(stagingdir / "business_profiles_staging.csv", index=False)
    bank_staged.to_csv(stagingdir / "bank_transactions_staging.csv", index=False)
    invoices_staged.to_csv(stagingdir / "invoices_staging.csv", index=False)
    bills_staged.to_csv(stagingdir / "supplier_bills_staging.csv", index=False)

    print("Evaluating detection rate against ground-truth issues log (test-only)...")
    staged_frames = {
        "business_profiles_raw.csv": profiles_staged,
        "bank_transactions_raw.csv": bank_staged,
        "invoices_raw.csv": invoices_staged,
        "supplier_bills_raw.csv": bills_staged,
    }
    report = evaluate_detection(issues_log, staged_frames)
    report.to_csv(stagingdir / "detection-evaluation.csv", index=False)

    print("Evaluating precision (false positives) per flag...")
    precision_report = evaluate_precision(issues_log, staged_frames)
    precision_report.to_csv(stagingdir / "precision-evaluation.csv", index=False)

    overall_rate = report["detected"].sum() / report["total_injected"].sum() if len(report) else 0

    summary_lines = ["# Staging: Detection Evaluation Report\n\n",
                      "(Test-only — measures pipeline detection logic against known synthetic ground truth.\n",
                      "This evaluation step, and the ground-truth log it reads, do not exist in the real pipeline.)\n\n",
                      "## Recall — did we catch every injected issue?\n\n",
                      f"**Overall detection (recall) rate: {overall_rate:.1%}**\n\n",
                      "| Dataset | Issue type | Injected | Detected | Rate |\n",
                      "|---|---|---|---|---|\n"]
    for _, r in report.iterrows():
        summary_lines.append(f"| {r['dataset']} | {r['issue_type']} | {r['total_injected']} | {r['detected']} | {r['detection_rate']:.0%} |\n")

    summary_lines.append("\n## Precision — of everything we flagged, how much was a real logged issue?\n\n")
    summary_lines.append("A flag with no logged issue_type isn't necessarily wrong — it may be a genuine finding "
                          "the generator never logged as an 'issue' at all (e.g. a payment recorded before its "
                          "invoice date). Those rows are marked n/a rather than scored as false positives.\n\n")
    summary_lines.append("| Dataset | Flag | Total flagged | True positives | False positives | Precision |\n")
    summary_lines.append("|---|---|---|---|---|---|\n")
    for _, r in precision_report.iterrows():
        prec = f"{r['precision']:.0%}" if isinstance(r["precision"], float) else r["precision"]
        summary_lines.append(f"| {r['dataset']} | {r['flag']} | {r['total_flagged']} | {r['true_positives']} | {r['false_positives']} | {prec} |\n")

    with open(stagingdir / "detection-evaluation-report.md", "w") as f:
        f.writelines(summary_lines)

    print(f"\nDone. Staging files written to: {stagingdir.resolve()}")
    print("".join(summary_lines))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rawdir", default="../../01-data/01-raw")
    parser.add_argument("--stagingdir", default="../../01-data/02-staging")
    args = parser.parse_args()
    main(args.rawdir, args.stagingdir)