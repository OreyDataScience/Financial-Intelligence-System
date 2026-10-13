"""
Phase 06 - Data Engineering: Reconciliation & Processing (staging -> processed)
Orey Analytics - Cash Flow Intelligence

Implements DATA_SPECIFICATION.md section 7:
  * duplicates are removed from the analysis layer but logged (never lost)
  * reversal pairs are identified and linked (they already net to zero in cash)
  * paid / partially-paid invoices and supplier bills are matched to bank
    transactions on counterparty, amount (tolerance) and date (window)
  * anything that cannot be matched is flagged `needs_investigation` with a
    reason - never dropped, never silently "fixed" in either direction
  * conflicting business profiles are kept visible and routed to review
  * missing values stay missing (no silent zero / fill)

The pipeline logic never reads the ground-truth issues log. The log is read only
in the final, clearly separated evaluation step (test-only).

Writes to 01-data/03-processed:
    business_profiles_processed.csv, bank_transactions_processed.csv,
    invoices_processed.csv, supplier_bills_processed.csv,
    duplicates-removed.csv, profile-conflicts.csv, investigation-queue.csv,
    data-quality-metrics.csv, data-quality-report.md,
    reconciliation-evaluation.csv, reconciliation-evaluation.md   (test-only)
"""

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd

# This file lives at: 02-data-engineering/03-transformation/reconcile_and_process.py
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_RAWDIR = _PROJECT_ROOT / "01-data" / "01-raw"
_DEFAULT_STAGINGDIR = _PROJECT_ROOT / "01-data" / "02-staging"
_DEFAULT_OUTDIR = _PROJECT_ROOT / "01-data" / "03-processed"

AMOUNT_TOLERANCE_PCT = 0.01      # amounts within 1% (min R1) count as the same payment
AMOUNT_CONFLICT_MAX_PCT = 0.20   # same counterparty + date window, amount off by up to 20% -> conflict
DATE_WINDOW_DAYS = 10            # ledger payment_date vs bank transaction_date
REVERSAL_WINDOW_DAYS = 10

# Bank rows that never have an invoice/bill counterpart (cash sales, payroll, opex).
OPERATIONAL_RE = r"^(?:POS SETTLEMENT|CASH AND CARRY|PAYROLL|OPERATING EXPENSE)"

PROFILE_COMPARE = ["business_name", "industry", "business_start_date", "province", "employee_count",
                   "annual_revenue_standardized", "accounting_basis", "financial_year_end"]


def to_bool(s):
    return s.map({"True": True, "False": False}).fillna(False).astype(bool)


def canon(s):
    return re.sub(r"\s+", " ", str(s).upper().replace("_", " ").replace("-", " ")).strip()


# ---------------------------------------------------------------------------
# Load staging
# ---------------------------------------------------------------------------
def load_staging(d):
    profiles = pd.read_csv(d / "business_profiles_staging.csv", dtype=str)

    bank = pd.read_csv(d / "bank_transactions_staging.csv", dtype=str)
    for c in ["is_duplicate", "is_reversal", "possible_sign_inconsistency", "delayed_posting_flag",
              "missing_transaction_reference", "missing_balance_after_transaction"]:
        bank[c] = to_bool(bank[c])
    bank["net_amount"] = pd.to_numeric(bank["net_amount"], errors="coerce")
    for c in ["transaction_date_std", "posting_date_std"]:
        bank[c] = pd.to_datetime(bank[c])
    bank["description_normalized"] = bank["description_normalized"].fillna("")

    ledgers = {}
    for name in ("invoices", "supplier_bills"):
        df = pd.read_csv(d / f"{name}_staging.csv", dtype=str)
        df["is_duplicate"] = to_bool(df["is_duplicate"])
        df["amount_paid"] = pd.to_numeric(df["amount_paid"], errors="coerce")
        for c in [c for c in df.columns if c.endswith("_date_std")]:
            df[c] = pd.to_datetime(df[c])
        ledgers[name] = df
    return profiles, bank, ledgers["invoices"], ledgers["supplier_bills"]


# ---------------------------------------------------------------------------
# Business profiles - conflicts stay visible
# ---------------------------------------------------------------------------
def _same(a, b):
    if pd.isna(a) and pd.isna(b):
        return True
    return str(a) == str(b)


def process_business_profiles(df):
    kept, conflicts = [], []
    for business_id, g in df.groupby("business_id", sort=True):
        g = g.sort_values("source_record_id")
        canonical = g.iloc[0].copy()
        canonical["profile_status"] = "ok"
        for _, other in g.iloc[1:].iterrows():
            canonical["profile_status"] = "conflict_needs_review"
            diffs = [c for c in PROFILE_COMPARE if not _same(canonical[c], other[c])]
            conflicts.append(dict(
                business_id=business_id,
                canonical_source_record_id=canonical["source_record_id"],
                conflicting_source_record_id=other["source_record_id"],
                differing_fields=";".join(diffs),
                status="needs_review",
                note="Earliest version used as working record; conflicting version preserved in staging/raw. "
                     "A person must confirm which version is correct.",
            ))
        kept.append(canonical)
    return pd.DataFrame(kept).reset_index(drop=True), pd.DataFrame(conflicts)


# ---------------------------------------------------------------------------
# Bank transactions
# ---------------------------------------------------------------------------
def process_bank_transactions(bank):
    removed = bank[bank["is_duplicate"]].copy()
    b = bank[~bank["is_duplicate"]].copy().reset_index(drop=True)
    b["is_operational"] = b["description_normalized"].str.contains(OPERATIONAL_RE, regex=True) & ~b["is_reversal"]

    # Link each reversal to the transaction it reverses (same business, same
    # description, opposite amount, close in time). Cash already nets to zero.
    b["netted_pair_id"] = ""
    used, n_pairs = set(), 0
    for ri in b.index[b["is_reversal"]]:
        rev = b.loc[ri]
        target = re.sub(r"^REVERSAL\s*", "", rev["description_normalized"]).strip()
        cand = b[(b["business_id"] == rev["business_id"]) & ~b["is_reversal"] & ~b.index.isin(used)
                 & (b["description_normalized"] == target)
                 & ((b["net_amount"] + rev["net_amount"]).abs() < 0.005)
                 & ((b["transaction_date_std"] - rev["transaction_date_std"]).abs().dt.days <= REVERSAL_WINDOW_DAYS)]
        if len(cand):
            n_pairs += 1
            b.loc[[ri, cand.index[0]], "netted_pair_id"] = f"NET_{n_pairs:04d}"
            used.add(cand.index[0])
    b["is_netted_pair"] = b["netted_pair_id"] != ""

    # Substantive review reasons vs. informational data-quality notes.
    review = pd.Series("", index=b.index)
    review = review.where(~b["possible_sign_inconsistency"], "possible_sign_inconsistency")
    unpaired = b["is_reversal"] & ~b["is_netted_pair"]
    review = review.where(~unpaired, "unpaired_reversal")
    b["review_reasons"] = review
    notes = []
    for _, r in b[["missing_transaction_reference", "missing_balance_after_transaction", "delayed_posting_flag"]].iterrows():
        n = [lbl for lbl, flag in zip(["missing_reference", "missing_balance", "delayed_posting"], r.tolist()) if flag]
        notes.append(";".join(n))
    b["data_quality_notes"] = notes
    return b, removed


# ---------------------------------------------------------------------------
# Ledger <-> bank reconciliation
# ---------------------------------------------------------------------------
def reconcile_ledger(ledger, bank, direction, status_col, counterparty_col):
    """Match paid / partially-paid ledger rows to bank rows.
    direction: 'inflow' (invoices <- bank credits) or 'outflow' (bills -> bank debits).

    Matching runs in passes so that the best evidence wins, regardless of row order:
      1. exact amount (within tolerance) + date window, counterparty preferred
      2. amount conflict: same counterparty + date window, amount off by up to 20%,
         assigned globally by best fit among bank rows left over from pass 1
      3. possible sign error: a bank row of the right amount exists but was
         recorded under the wrong sign (explained, never silently matched)
      4. nothing found -> no_bank_record
    """
    sign = 1 if direction == "inflow" else -1
    base = bank[~bank["is_reversal"] & ~bank["is_operational"]].copy()
    pool = base[(base["net_amount"] * sign > 0) & ~base["possible_sign_inconsistency"]].copy()
    pool["abs_amount"] = pool["net_amount"].abs()
    by_biz = {k: v for k, v in pool.groupby("business_id")}

    flipped = base[base["possible_sign_inconsistency"]].copy() if direction == "outflow" else base.iloc[0:0].copy()
    flipped["abs_amount"] = flipped["net_amount"].abs()
    flipped_by_biz = {k: v for k, v in flipped.groupby("business_id")}

    consumed = {}   # bank source_record_id -> (ledger source_record_id, status)
    results = {}

    def counterparty(row):
        v = row[counterparty_col]
        return canon(v) if pd.notna(v) and str(v).strip() else ""

    def window_for(row):
        biz = by_biz.get(row["business_id"])
        if biz is None:
            return pool.iloc[0:0].assign(cp_hit=False, day_gap=0)
        w = biz[((biz["transaction_date_std"] - row["payment_date_std"]).abs().dt.days <= DATE_WINDOW_DAYS)
                & ~biz["source_record_id"].isin(set(consumed))].copy()
        cp = counterparty(row)
        w["cp_hit"] = w["description_normalized"].str.contains(cp, regex=False) if (cp and len(w)) else False
        w["day_gap"] = (w["transaction_date_std"] - row["payment_date_std"]).abs().dt.days
        return w

    eligible = ledger[ledger[status_col].isin(["paid", "partially_paid"]) & (ledger["amount_paid"] > 0)]
    eligible = eligible.sort_values("payment_date_std")

    # ---- pass 1: exact matches. Counterparty-confirmed matches get priority, ----
    # ---- assigned globally by best fit so row order never decides who wins.  ----
    def exact_pairs(rows, require_counterparty):
        pairs = []
        for idx, row in rows.iterrows():
            w = window_for(row)
            if w.empty:
                continue
            amt = row["amount_paid"]
            m = w[(w["abs_amount"] - amt).abs() <= max(amt * AMOUNT_TOLERANCE_PCT, 1.0)]
            if require_counterparty:
                m = m[m["cp_hit"]]
            for _, c in m.iterrows():
                pairs.append((abs(c["abs_amount"] - amt) / amt, c["day_gap"], idx, c["source_record_id"],
                              c["abs_amount"], bool(c["cp_hit"]), bool(c["is_netted_pair"])))
        return pairs

    def assign_exact(pairs):
        for _, _, idx, bank_id, bank_amt, cp_hit, netted in sorted(pairs):
            if idx in results or bank_id in consumed:
                continue
            if netted:
                status, reason = "needs_investigation", "payment_reversed"
            else:
                status, reason = "matched", "matched_amount_date" + ("_counterparty" if cp_hit else "")
            consumed[bank_id] = (eligible.at[idx, "source_record_id"], status)
            results[idx] = (status, reason, bank_id, "high" if cp_hit else "low", bank_amt)

    for idx, row in eligible.iterrows():
        if pd.isna(row["payment_date_std"]):
            results[idx] = ("needs_investigation", "missing_payment_date", "", "", np.nan)
    assign_exact(exact_pairs(eligible[~eligible.index.isin(results)], require_counterparty=True))
    assign_exact(exact_pairs(eligible[~eligible.index.isin(results)], require_counterparty=False))

    # ---- pass 2: amount conflicts, assigned globally by best fit ----
    pairs = []
    for idx, row in eligible.iterrows():
        if idx in results:
            continue
        w = window_for(row)
        if w.empty:
            continue
        near = w[w["cp_hit"] & ((w["abs_amount"] - row["amount_paid"]).abs() <= row["amount_paid"] * AMOUNT_CONFLICT_MAX_PCT)]
        for _, c in near.iterrows():
            pairs.append((abs(c["abs_amount"] - row["amount_paid"]) / row["amount_paid"], c["day_gap"],
                          idx, c["source_record_id"], c["abs_amount"]))
    for _, _, idx, bank_id, bank_amt in sorted(pairs):
        if idx in results or bank_id in consumed:
            continue
        consumed[bank_id] = (eligible.at[idx, "source_record_id"], "needs_investigation")
        results[idx] = ("needs_investigation", "amount_conflict", bank_id, "high", bank_amt)

    # ---- pass 3: explained by a sign-inconsistent bank row (global best fit, ----
    # ---- counterparty first); pass 4: nothing found                          ----
    sign_pairs = []
    for idx, row in eligible.iterrows():
        if idx in results:
            continue
        amt = row["amount_paid"]
        fb = flipped_by_biz.get(row["business_id"])
        if fb is None:
            continue
        cp = counterparty(row)
        fc = fb[((fb["abs_amount"] - amt).abs() <= max(amt * AMOUNT_TOLERANCE_PCT, 1.0))
                & ((fb["transaction_date_std"] - row["payment_date_std"]).abs().dt.days <= DATE_WINDOW_DAYS)
                & ~fb["source_record_id"].isin(set(consumed))]
        for _, c in fc.iterrows():
            cp_hit = bool(cp) and cp in c["description_normalized"]
            sign_pairs.append((0 if cp_hit else 1, abs(c["abs_amount"] - amt) / amt,
                               abs((c["transaction_date_std"] - row["payment_date_std"]).days),
                               idx, c["source_record_id"], c["abs_amount"]))
    for _, _, _, idx, bank_id, bank_amt in sorted(sign_pairs):
        if idx in results or bank_id in consumed:
            continue
        consumed[bank_id] = (eligible.at[idx, "source_record_id"], "needs_investigation")
        results[idx] = ("needs_investigation", "possible_sign_error_in_bank", bank_id, "low", bank_amt)
    for idx in eligible.index:
        if idx not in results:
            results[idx] = ("needs_investigation", "no_bank_record", "", "", np.nan)

    res = pd.DataFrame.from_dict(results, orient="index",
                                 columns=["reconciliation_status", "reconciliation_reason",
                                          "matched_bank_source_record_id", "match_confidence",
                                          "matched_bank_amount"])
    out = ledger.join(res)
    out["reconciliation_status"] = out["reconciliation_status"].fillna("not_applicable")
    out["reconciliation_reason"] = out["reconciliation_reason"].fillna("not_yet_paid")
    for c in ["matched_bank_source_record_id", "match_confidence"]:
        out[c] = out[c].fillna("")
    out["amount_difference"] = out["amount_paid"] - out["matched_bank_amount"]
    return out, consumed


def label_bank_rows(bank, inv_consumed, bill_consumed):
    b = bank.copy()
    b["reconciliation_status"] = "unmatched_needs_investigation"
    b.loc[b["is_operational"], "reconciliation_status"] = "operational_no_ledger_expected"
    b.loc[b["is_reversal"], "reconciliation_status"] = "reversal"
    b["matched_ledger_type"], b["matched_ledger_source_record_id"] = "", ""
    for ledger_type, consumed in (("invoice", inv_consumed), ("supplier_bill", bill_consumed)):
        for bank_id, (ledger_id, status) in consumed.items():
            m = b["source_record_id"] == bank_id
            b.loc[m, "reconciliation_status"] = "matched_ledger" if status == "matched" else "ledger_conflict"
            b.loc[m, "matched_ledger_type"] = ledger_type
            b.loc[m, "matched_ledger_source_record_id"] = ledger_id
    return b


# ---------------------------------------------------------------------------
# Investigation queue + quality metrics (pipeline outputs - no ground truth)
# ---------------------------------------------------------------------------
def build_investigation_queue(profile_conflicts, bank, invoices, bills):
    rows = []
    for _, r in profile_conflicts.iterrows():
        rows.append(dict(dataset="business_profiles", source_record_id=r["conflicting_source_record_id"],
                         business_id=r["business_id"], reason="conflicting_profile_version",
                         detail=f"differs from {r['canonical_source_record_id']} in: {r['differing_fields']}"))
    for name, df in (("invoices", invoices), ("supplier_bills", bills)):
        for _, r in df[df["reconciliation_status"] == "needs_investigation"].iterrows():
            rows.append(dict(dataset=name, source_record_id=r["source_record_id"], business_id=r["business_id"],
                             reason=r["reconciliation_reason"],
                             detail=f"amount_paid={r['amount_paid']}; candidate_bank_row={r['matched_bank_source_record_id'] or 'none'}"))
    for _, r in bank[bank["review_reasons"] != ""].iterrows():
        rows.append(dict(dataset="bank_transactions", source_record_id=r["source_record_id"],
                         business_id=r["business_id"], reason=r["review_reasons"],
                         detail=f"net_amount={r['net_amount']}; {r['transaction_description']}"))
    settlement_unmatched = bank[(bank["reconciliation_status"] == "unmatched_needs_investigation")
                                & (bank["review_reasons"] == "")]
    for _, r in settlement_unmatched.iterrows():
        rows.append(dict(dataset="bank_transactions", source_record_id=r["source_record_id"],
                         business_id=r["business_id"], reason="bank_row_without_ledger_record",
                         detail=f"net_amount={r['net_amount']}; {r['transaction_description']}"))
    return pd.DataFrame(rows)


def build_quality_metrics(bank_stg, inv_stg, bill_stg, bank_p, inv_p, bill_p):
    rows = []

    def add(biz, dataset, metric, value):
        rows.append(dict(business_id=biz, dataset=dataset, metric=metric, value=value))

    for biz, g in bank_stg.groupby("business_id"):
        n = len(g)
        add(biz, "bank_transactions", "rows_received", n)
        add(biz, "bank_transactions", "duplicate_rate", round(g["is_duplicate"].mean(), 4))
        add(biz, "bank_transactions", "missing_reference_rate", round(g["missing_transaction_reference"].mean(), 4))
        add(biz, "bank_transactions", "missing_balance_rate", round(g["missing_balance_after_transaction"].mean(), 4))
        add(biz, "bank_transactions", "delayed_posting_rate", round(g["delayed_posting_flag"].mean(), 4))
    for name, stg, proc in (("invoices", inv_stg, inv_p), ("supplier_bills", bill_stg, bill_p)):
        missing_col = "missing_due_date" if name == "invoices" else "missing_supplier_id"
        for biz, g in stg.groupby("business_id"):
            add(biz, name, "rows_received", len(g))
            add(biz, name, "duplicate_rate", round(g["is_duplicate"].mean(), 4))
            add(biz, name, missing_col + "_rate", round(g[missing_col].astype(str).eq("True").mean(), 4))
        for biz, g in proc.groupby("business_id"):
            elig = g[g["reconciliation_status"].isin(["matched", "needs_investigation"])]
            add(biz, name, "paid_records_to_reconcile", len(elig))
            add(biz, name, "match_rate",
                round((elig["reconciliation_status"] == "matched").mean(), 4) if len(elig) else np.nan)
            add(biz, name, "needs_investigation", int((elig["reconciliation_status"] == "needs_investigation").sum()))
    return pd.DataFrame(rows)


def render_quality_report(metrics, dup_removed, n_pairs, conflicts, inv_p, bill_p, bank_p, queue):
    L = ["# Processed Data Quality Report\n\n",
         "Generated by the pipeline from staging data only (no ground truth involved).\n\n",
         "## What the processing stage did\n\n",
         f"- Duplicate rows removed from the analysis layer (kept in `duplicates-removed.csv`): {len(dup_removed)}\n",
         f"- Reversal pairs linked: {n_pairs}\n",
         f"- Business profiles with conflicting versions awaiting review: {len(conflicts)}\n",
         f"- Items in the investigation queue: {len(queue)}\n\n"]

    for title, df in (("Invoices", inv_p), ("Supplier bills", bill_p)):
        L.append(f"## {title} - reconciliation to bank\n\n")
        counts = df["reconciliation_status"].value_counts()
        for status, n in counts.items():
            L.append(f"- {status}: {n} ({n / len(df):.1%})\n")
        reasons = df[df["reconciliation_status"] == "needs_investigation"]["reconciliation_reason"].value_counts()
        if len(reasons):
            L.append("\nNeeds-investigation reasons: " + ", ".join(f"{k} ({v})" for k, v in reasons.items()) + "\n")
        low = int(((df["match_confidence"] == "low") & (df["reconciliation_status"] == "matched")).sum())
        L.append(f"\nMatches made on amount + date only (no counterparty in the bank description): {low}\n\n")

    L.append("## Bank transactions - reconciliation status\n\n")
    for status, n in bank_p["reconciliation_status"].value_counts().items():
        L.append(f"- {status}: {n}\n")

    L.append("\n## Match rate per business (paid / partially-paid records)\n\n"
             "| Business | Dataset | To reconcile | Match rate | Needs investigation |\n|---|---|---|---|---|\n")
    for biz in sorted(metrics["business_id"].unique()):
        for ds in ("invoices", "supplier_bills"):
            m = metrics[(metrics["business_id"] == biz) & (metrics["dataset"] == ds)].set_index("metric")["value"]
            if "match_rate" in m.index:
                L.append(f"| {biz} | {ds} | {int(m['paid_records_to_reconcile'])} | {float(m['match_rate']):.0%} | {int(m['needs_investigation'])} |\n")

    L.append("\n## Data-quality rates per business (bank transactions)\n\n"
             "| Business | Rows received | Duplicate rate | Missing reference | Missing balance | Delayed posting |\n|---|---|---|---|---|---|\n")
    for biz in sorted(metrics["business_id"].unique()):
        m = metrics[(metrics["business_id"] == biz) & (metrics["dataset"] == "bank_transactions")].set_index("metric")["value"]
        L.append(f"| {biz} | {int(m['rows_received'])} | {m['duplicate_rate']:.1%} | {m['missing_reference_rate']:.1%} | "
                 f"{m['missing_balance_rate']:.1%} | {m['delayed_posting_rate']:.1%} |\n")
    return "".join(L)


# ---------------------------------------------------------------------------
# TEST-ONLY: evaluate reconciliation against the ground-truth issues log
# ---------------------------------------------------------------------------
def evaluate_reconciliation(issues_log, inv_p, bill_p):
    bank_log = issues_log[issues_log["dataset"] == "bank_transactions_raw.csv"]
    sign_ids = set(bank_log[bank_log["issue_type"] == "sign_inconsistency"]["source_record_id"])
    reversed_ids = set(bank_log[bank_log["issue_type"] == "reversal"]["description"]
                       .str.extract(r"Reversal of (BT_\d+)")[0].dropna())

    rows, notes = [], []
    for dataset, df in (("invoices_raw.csv", inv_p), ("supplier_bills_raw.csv", bill_p)):
        log = issues_log[issues_log["dataset"] == dataset]
        injected_ids = {}
        for issue_type, expected_reason in (("no_bank_receipt", "no_bank_record"),
                                            ("ledger_bank_amount_conflict", "amount_conflict")):
            ids = set(log[log["issue_type"] == issue_type]["source_record_id"])
            injected_ids[issue_type] = ids
            sub = df[df["source_record_id"].isin(ids)]
            rows.append(dict(
                dataset=dataset, issue_type=issue_type, injected=len(ids),
                flagged_needs_investigation=int((sub["reconciliation_status"] == "needs_investigation").sum()),
                flagged_with_expected_reason=int((sub["reconciliation_reason"] == expected_reason).sum()),
                wrongly_matched=int((sub["reconciliation_status"] == "matched").sum())))

        flagged = df[df["reconciliation_status"] == "needs_investigation"]
        by_ledger_issue = flagged["source_record_id"].isin(injected_ids["no_bank_receipt"] | injected_ids["ledger_bank_amount_conflict"])
        by_bank_sign = (flagged["reconciliation_reason"] == "possible_sign_error_in_bank") & flagged["matched_bank_source_record_id"].isin(sign_ids)
        by_bank_reversal = (flagged["reconciliation_reason"] == "payment_reversed") & flagged["matched_bank_source_record_id"].isin(reversed_ids)
        unexplained = flagged[~(by_ledger_issue | by_bank_sign | by_bank_reversal)]
        notes.append(dict(dataset=dataset, total=len(flagged), ledger_issue=int(by_ledger_issue.sum()),
                          bank_sign=int(by_bank_sign.sum()), bank_reversal=int(by_bank_reversal.sum()),
                          unexplained=len(unexplained),
                          unexplained_reasons=unexplained["reconciliation_reason"].value_counts().to_dict()))
    return pd.DataFrame(rows), notes


def render_evaluation(eval_df, notes):
    L = ["# Reconciliation Evaluation (test-only)\n\n",
         "Compares reconciliation outcomes with the synthetic ground-truth log. This file and the log it reads "
         "do not exist in a real pipeline.\n\n",
         "## Recall - were the injected ledger/bank problems caught?\n\n",
         "| Dataset | Injected issue | Injected | Sent to investigation | With expected reason | Wrongly matched |\n|---|---|---|---|---|---|\n"]
    for _, r in eval_df.iterrows():
        L.append(f"| {r['dataset']} | {r['issue_type']} | {r['injected']} | {r['flagged_needs_investigation']} | "
                 f"{r['flagged_with_expected_reason']} | {r['wrongly_matched']} |\n")
    L.append("\n## Precision - is everything in the investigation queue there for a real reason?\n\n"
             "| Dataset | In queue | Injected ledger/bank problem | Bank row had wrong sign | Bank payment reversed | Unexplained |\n|---|---|---|---|---|---|\n")
    for n in notes:
        L.append(f"| {n['dataset']} | {n['total']} | {n['ledger_issue']} | {n['bank_sign']} | {n['bank_reversal']} | "
                 f"{n['unexplained']} {n['unexplained_reasons'] or ''} |\n")
    L.append("\n\"Wrongly matched\" counts injected problems that the matcher paired with a different, "
             "near-identical payment. That is an inherent ambiguity when the same counterparty has two payments of "
             "almost the same amount inside one date window and the bank row carries no payment reference.\n")
    return "".join(L)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main(rawdir, stagingdir, outdir):
    rawdir, stagingdir, outdir = Path(rawdir), Path(stagingdir), Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    print("Loading staging data ...")
    profiles, bank_stg, inv_stg, bill_stg = load_staging(stagingdir)

    print("Processing business profiles ...")
    profiles_p, conflicts = process_business_profiles(profiles)

    print("Processing bank transactions (dedupe, link reversals) ...")
    bank_p, bank_dups = process_bank_transactions(bank_stg)
    n_pairs = int(bank_p["netted_pair_id"].replace("", np.nan).nunique())

    inv_dups = inv_stg[inv_stg["is_duplicate"]]
    bill_dups = bill_stg[bill_stg["is_duplicate"]]
    inv_clean = inv_stg[~inv_stg["is_duplicate"]].copy()
    bill_clean = bill_stg[~bill_stg["is_duplicate"]].copy()

    print("Reconciling invoices against bank credits ...")
    inv_p, inv_consumed = reconcile_ledger(inv_clean, bank_p, "inflow", "invoice_status_standardized", "customer_id")
    print("Reconciling supplier bills against bank debits ...")
    bill_p, bill_consumed = reconcile_ledger(bill_clean, bank_p, "outflow", "bill_status_standardized", "supplier_id")
    bank_p = label_bank_rows(bank_p, inv_consumed, bill_consumed)

    dup_log = pd.concat([
        bank_dups.assign(dataset="bank_transactions")[["dataset", "source_record_id", "business_id"]],
        inv_dups.assign(dataset="invoices")[["dataset", "source_record_id", "business_id"]],
        bill_dups.assign(dataset="supplier_bills")[["dataset", "source_record_id", "business_id"]],
    ], ignore_index=True)

    queue = build_investigation_queue(conflicts, bank_p, inv_p, bill_p)
    metrics = build_quality_metrics(bank_stg, inv_stg, bill_stg, bank_p, inv_p, bill_p)
    report = render_quality_report(metrics, dup_log, n_pairs, conflicts, inv_p, bill_p, bank_p, queue)

    profiles_p.to_csv(outdir / "business_profiles_processed.csv", index=False)
    bank_p.to_csv(outdir / "bank_transactions_processed.csv", index=False)
    inv_p.to_csv(outdir / "invoices_processed.csv", index=False)
    bill_p.to_csv(outdir / "supplier_bills_processed.csv", index=False)
    dup_log.to_csv(outdir / "duplicates-removed.csv", index=False)
    conflicts.to_csv(outdir / "profile-conflicts.csv", index=False)
    queue.to_csv(outdir / "investigation-queue.csv", index=False)
    metrics.to_csv(outdir / "data-quality-metrics.csv", index=False)
    (outdir / "data-quality-report.md").write_text(report, encoding="utf-8")

    # ---- test-only evaluation: the ONLY place the issues log is read ----
    issues_log = pd.read_csv(rawdir / "data-quality-issues-log.csv")
    eval_df, notes = evaluate_reconciliation(issues_log, inv_p, bill_p)
    eval_df.to_csv(outdir / "reconciliation-evaluation.csv", index=False)
    eval_md = render_evaluation(eval_df, notes)
    (outdir / "reconciliation-evaluation.md").write_text(eval_md, encoding="utf-8")

    print(f"\nDone. Processed files written to: {outdir.resolve()}\n")
    print(report)
    print(eval_md)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rawdir", default=str(_DEFAULT_RAWDIR))
    parser.add_argument("--stagingdir", default=str(_DEFAULT_STAGINGDIR))
    parser.add_argument("--outdir", default=str(_DEFAULT_OUTDIR))
    args = parser.parse_args()
    main(args.rawdir, args.stagingdir, args.outdir)
