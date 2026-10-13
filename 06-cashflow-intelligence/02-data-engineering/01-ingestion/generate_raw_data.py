"""
Phase 06 - Synthetic SME Raw Data Generator
Orey Analytics - Cash Flow Intelligence

Implements DATA_SPECIFICATION.md. Generates deliberately messy raw datasets
for 5 South African SMEs across a 24-month history (2024-01-01 to 2025-12-31).

Generation order matters:
  1. Invoices and supplier bills are generated FIRST as the underlying
     economic events.
  2. A controlled majority of their paid / partially-paid records are used to
     derive REAL matching bank transactions (credits for invoices, debits for
     bills).
  3. A deliberate minority (HOLD_BACK_RATE) is held back with no bank
     transaction at all  -> "recorded as paid, no bank receipt found".
  4. A smaller set has a bank amount that differs from the ledger amount
     -> "ledger and bank disagree".
  5. Independent operational noise (POS sales, payroll, cash-and-carry orders,
     operating expenses) is added, then bank-export messiness is applied.

Raw data is treated as immutable: the script refuses to overwrite existing raw
files unless --force is passed.

Usage:
    python generate_raw_data.py                # writes to 01-data/01-raw (resolved from this file's location)
    python generate_raw_data.py --force        # regenerate and overwrite
    python generate_raw_data.py --outdir PATH  # custom output folder

Reproducible via fixed SEED.
"""

import argparse
import random
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from faker import Faker

# This file lives at: 02-data-engineering/01-ingestion/generate_raw_data.py
_SCRIPT_DIR = Path(__file__).resolve().parent
_DEFAULT_OUTDIR = _SCRIPT_DIR.parent.parent / "01-data" / "01-raw"

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
fake = Faker()
Faker.seed(SEED)

START_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2025, 12, 31)

BANKS = ["FNB", "Standard Bank", "Absa", "Nedbank", "Capitec"]

# Share of paid / partially-paid ledger records that get NO bank transaction.
HOLD_BACK_RATE = 0.12
# Share of fully-paid ledger records where the bank amount differs from the ledger.
LEDGER_BANK_CONFLICT_RATE = 0.03

SMES = [
    dict(business_id="SME_001", name="Karabo Retail Traders", industry="Retail",
         industry_alt=["Retail", "retail trade", "Retail Trade"],
         start=datetime(2018, 3, 1), province="Gauteng", employees=8,
         annual_revenue=3_500_000, basis="Cash", fy_end="February",
         txn_pattern="retail"),
    dict(business_id="SME_002", name="Nkosi & Associates Consulting", industry="Consulting",
         industry_alt=["Consulting", "Professional Consulting", "consulting services"],
         start=datetime(2016, 6, 15), province="Western Cape", employees=5,
         annual_revenue=2_100_000, basis="Accrual", fy_end="February",
         txn_pattern="consulting"),
    dict(business_id="SME_003", name="Delta Build Construction", industry="Construction",
         industry_alt=["Construction", "Building & Construction", "construction"],
         start=datetime(2012, 1, 10), province="KwaZulu-Natal", employees=15,
         annual_revenue=8_000_000, basis="Accrual", fy_end="December",
         txn_pattern="construction"),
    dict(business_id="SME_004", name="Vuka Wholesale Distributors", industry="Wholesale",
         industry_alt=["Wholesale", "Wholesale Trade", "wholesale distribution"],
         start=datetime(2014, 9, 1), province="Gauteng", employees=20,
         annual_revenue=12_000_000, basis="Accrual", fy_end="February",
         txn_pattern="wholesale"),
    dict(business_id="SME_005", name="Thandiwe Professional Services", industry="Professional Services",
         industry_alt=["Professional Services", "professional services", "Prof. Services"],
         start=datetime(2019, 4, 20), province="Eastern Cape", employees=4,
         annual_revenue=1_800_000, basis="Cash", fy_end="February",
         txn_pattern="professional"),
]

STATUS_CHOICES_PAID = ["Paid", "paid", "PAID"]

issues_log = []
_issue_counter = 0


def log_issue(dataset, source_record_id, business_id, issue_type, description):
    global _issue_counter
    _issue_counter += 1
    issues_log.append(dict(
        issue_id=f"ISSUE_{_issue_counter:06d}",
        dataset=dataset,
        source_record_id=source_record_id,
        business_id=business_id,
        issue_type=issue_type,
        description=description,
    ))


def random_date_format(d):
    """Return a date string in one of several inconsistent real-world formats.
    Accepts a datetime or NaT/None; returns '' for missing."""
    if d is None or pd.isna(d):
        return ""
    fmt = random.choice(["iso", "slash", "text"])
    if fmt == "iso":
        return d.strftime("%Y-%m-%d")
    if fmt == "slash":
        return d.strftime("%d/%m/%Y")
    return d.strftime("%d %b %Y")


def vary_description(base: str) -> str:
    variant = random.choice(["exact", "abbrev", "hyphen", "upper"])
    if variant == "exact":
        return base
    if variant == "abbrev":
        return base.replace(" SUPPLIERS", " SUPP").replace(" TRADERS", " TRD")
    if variant == "hyphen":
        return base.replace(" ", "-")
    return base.upper()


def clip_to_range(d):
    return min(max(d, START_DATE), END_DATE)


# ---------------------------------------------------------------------------
# 1. business_profiles_raw.csv
# ---------------------------------------------------------------------------
def generate_business_profiles():
    rows = []
    sid = 0
    for sme in SMES:
        sid += 1
        rows.append(dict(
            source_record_id=f"BP_{sid:04d}",
            business_id=sme["business_id"],
            business_name=sme["name"],
            industry=random.choice(sme["industry_alt"]),
            business_start_date=sme["start"].strftime("%Y-%m-%d"),
            province=sme["province"],
            employee_count=sme["employees"],
            annual_revenue=sme["annual_revenue"],
            accounting_basis=sme["basis"],
            financial_year_end=sme["fy_end"],
            source_file="business_profiles_export_2026.csv",
        ))

    df = pd.DataFrame(rows)
    for col in ["employee_count", "annual_revenue", "financial_year_end"]:
        df[col] = df[col].astype(object)

    i = df.sample(1, random_state=SEED).index[0]
    df.at[i, "employee_count"] = np.nan
    log_issue("business_profiles_raw.csv", df.at[i, "source_record_id"], df.at[i, "business_id"],
              "missing_value", "employee_count missing")

    i = df.sample(1, random_state=SEED + 1).index[0]
    df.at[i, "annual_revenue"] = f"R {df.at[i, 'annual_revenue']:,}"
    log_issue("business_profiles_raw.csv", df.at[i, "source_record_id"], df.at[i, "business_id"],
              "type_inconsistency", "annual_revenue stored as formatted text, not numeric")

    i = df.sample(1, random_state=SEED + 2).index[0]
    df.at[i, "financial_year_end"] = np.nan
    log_issue("business_profiles_raw.csv", df.at[i, "source_record_id"], df.at[i, "business_id"],
              "missing_value", "financial_year_end missing")

    conflict_sme = SMES[0]
    sid += 1
    dup_row = dict(
        source_record_id=f"BP_{sid:04d}",
        business_id=conflict_sme["business_id"],
        business_name=conflict_sme["name"],
        industry=conflict_sme["industry"],
        business_start_date=conflict_sme["start"].strftime("%Y-%m-%d"),
        province=conflict_sme["province"],
        employee_count=conflict_sme["employees"] - 3,
        annual_revenue=conflict_sme["annual_revenue"] * 0.8,
        accounting_basis=conflict_sme["basis"],
        financial_year_end=conflict_sme["fy_end"],
        source_file="business_profiles_export_2025_stale.csv",
    )
    df = pd.concat([df, pd.DataFrame([dup_row])], ignore_index=True)
    log_issue("business_profiles_raw.csv", dup_row["source_record_id"], conflict_sme["business_id"],
              "conflicting_record", "Duplicate profile version with stale employee_count and annual_revenue")
    return df


# ---------------------------------------------------------------------------
# 2. invoices (generated BEFORE bank transactions; dates kept as datetime)
# ---------------------------------------------------------------------------
def generate_invoices():
    rows = []
    sid = 1
    for sme in SMES:
        business_id = sme["business_id"]
        n_invoices = {"retail": 40, "consulting": 60, "construction": 30,
                      "wholesale": 250, "professional": 90}[sme["txn_pattern"]]
        customers = [f"CUST_{business_id}_{i:03d}" for i in range(1, 16)]

        for _ in range(n_invoices):
            rec_id = f"INV_{sid:06d}"
            invoice_date = START_DATE + timedelta(days=random.randint(0, (END_DATE - START_DATE).days))
            terms = random.choice([15, 30, 45, 60])
            due_date = invoice_date + timedelta(days=terms)
            amount = round(np.random.uniform(3_000, 400_000) if sme["txn_pattern"] == "construction"
                           else np.random.uniform(1_000, 60_000), 2)

            roll = random.random()
            if roll < 0.65:
                status = random.choice(STATUS_CHOICES_PAID)
                paid_amt = amount
                pay_delay = random.randint(-2, terms + 30)
                payment_date = invoice_date + timedelta(days=pay_delay)
                if pay_delay < 0:
                    log_issue("invoices_raw.csv", rec_id, business_id, "payment_before_invoice",
                              "Recorded payment_date is earlier than invoice_date")
            elif roll < 0.85:
                status = "Partially Paid"
                paid_amt = round(amount * random.uniform(0.2, 0.8), 2)
                payment_date = invoice_date + timedelta(days=random.randint(5, terms + 20))
            else:
                status = random.choice(["Unpaid", "Overdue"])
                paid_amt = 0
                payment_date = pd.NaT

            # As of the data cut-off, a payment dated after END_DATE has not happened yet.
            if pd.notna(payment_date) and payment_date > END_DATE:
                status = random.choice(["Unpaid", "Overdue"])
                paid_amt = 0
                payment_date = pd.NaT

            # Hidden (never exported) amount the bank actually saw.
            bank_amount = paid_amt
            if status in STATUS_CHOICES_PAID and random.random() < LEDGER_BANK_CONFLICT_RATE:
                bank_amount = round(paid_amt * random.uniform(0.85, 0.97), 2)

            keep_due_date = random.random() > 0.05
            if not keep_due_date:
                log_issue("invoices_raw.csv", rec_id, business_id, "missing_value", "due_date missing")

            rows.append(dict(
                source_record_id=rec_id,
                business_id=business_id,
                invoice_id=f"{business_id}-INV-{sid:05d}",
                customer_id=random.choice(customers),
                invoice_date_dt=invoice_date,
                due_date_dt=due_date if keep_due_date else pd.NaT,
                invoice_amount=amount,
                amount_paid=paid_amt,
                invoice_status=status,
                payment_date_dt=payment_date,
                currency="ZAR",
                source_file=f"{business_id.lower()}_accounting_export.csv",
                _bank_amount=bank_amount,
            ))
            sid += 1
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 3. supplier_bills (generated BEFORE bank transactions; dates as datetime)
# ---------------------------------------------------------------------------
def generate_supplier_bills():
    rows = []
    sid = 1
    for sme in SMES:
        business_id = sme["business_id"]
        n_bills = {"retail": 50, "consulting": 20, "construction": 70,
                   "wholesale": 200, "professional": 15}[sme["txn_pattern"]]
        suppliers = [f"SUPP_{business_id}_{i:03d}" for i in range(1, 11)]

        for _ in range(n_bills):
            rec_id = f"BILL_{sid:06d}"
            bill_date = START_DATE + timedelta(days=random.randint(0, (END_DATE - START_DATE).days))
            terms = random.choice([15, 30, 45, 60])
            due_date = bill_date + timedelta(days=terms)
            amount = round(np.random.uniform(2_000, 250_000) if sme["txn_pattern"] == "construction"
                           else np.random.uniform(500, 40_000), 2)

            roll = random.random()
            if roll < 0.7:
                status = "Paid"
                paid_amt = amount
                payment_date = bill_date + timedelta(days=random.randint(1, terms + 15))
            elif roll < 0.88:
                status = "Partially Paid"
                paid_amt = round(amount * random.uniform(0.3, 0.75), 2)
                payment_date = bill_date + timedelta(days=random.randint(5, terms + 20))
            else:
                status = random.choice(["Unpaid", "Overdue"])
                paid_amt = 0
                payment_date = pd.NaT

            # As of the data cut-off, a payment dated after END_DATE has not happened yet.
            if pd.notna(payment_date) and payment_date > END_DATE:
                status = random.choice(["Unpaid", "Overdue"])
                paid_amt = 0
                payment_date = pd.NaT

            bank_amount = paid_amt
            if status == "Paid" and random.random() < LEDGER_BANK_CONFLICT_RATE:
                bank_amount = round(paid_amt * random.uniform(0.85, 0.97), 2)

            missing_supplier = random.random() < 0.03
            if missing_supplier:
                log_issue("supplier_bills_raw.csv", rec_id, business_id, "missing_value", "supplier_id missing")

            rows.append(dict(
                source_record_id=rec_id,
                business_id=business_id,
                bill_id=f"{business_id}-BILL-{sid:05d}",
                supplier_id="" if missing_supplier else random.choice(suppliers),
                bill_date_dt=bill_date,
                due_date_dt=due_date,
                bill_amount=amount,
                amount_paid=paid_amt,
                bill_status=status,
                payment_date_dt=payment_date,
                currency="ZAR",
                source_file=f"{business_id.lower()}_accounting_export.csv",
                _bank_amount=bank_amount,
            ))
            sid += 1
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 4. bank_transactions - operational noise + invoice/bill-derived settlements
# ---------------------------------------------------------------------------
def _txn_row(sid, business_id, bank, account_id, txn_date, description, amount, credit, balance):
    return dict(
        source_record_id=f"BT_{sid:07d}",
        business_id=business_id,
        bank_name=bank,
        account_id=account_id,
        transaction_date=txn_date,
        posting_date=txn_date,
        transaction_description=description,
        transaction_reference=f"REF{fake.random_number(digits=9, fix_len=True)}",
        debit_amount="" if credit else amount,
        credit_amount=amount if credit else "",
        balance_after_transaction=round(balance, 2),
        currency="ZAR",
        source_file=f"{bank.replace(' ', '_').lower()}_statement_export.csv",
    )


def generate_settlement_rows(ledger_df, business_id, bank, account_id, start_sid, start_balance,
                             status_field, paid_values, description_prefix, counterparty_field,
                             direction):
    """Derive real bank transactions from paid / partially-paid ledger records
    (invoices -> credits, bills -> debits), holding back HOLD_BACK_RATE on purpose."""
    dataset = "invoices_raw.csv" if direction == "inflow" else "supplier_bills_raw.csv"
    rows, sid, balance = [], start_sid, start_balance
    subset = ledger_df[(ledger_df["business_id"] == business_id)
                       & (ledger_df[status_field].isin(paid_values))]

    for _, rec in subset.iterrows():
        if random.random() < HOLD_BACK_RATE:
            log_issue(dataset, rec["source_record_id"], business_id, "no_bank_receipt",
                      "Recorded as paid/partially paid but no bank transaction exists (held back intentionally)")
            continue
        payment_date = rec["payment_date_dt"]
        amount = rec["_bank_amount"]
        if pd.isna(payment_date) or pd.isna(amount) or amount <= 0:
            continue

        if abs(amount - rec["amount_paid"]) > 0.005:
            log_issue(dataset, rec["source_record_id"], business_id, "ledger_bank_amount_conflict",
                      f"Bank amount {amount} differs from ledger amount_paid {rec['amount_paid']}")

        txn_date = clip_to_range(payment_date + timedelta(days=random.randint(-1, 3)))
        counterparty = rec[counterparty_field] if rec[counterparty_field] else ""
        description = f"{description_prefix} {counterparty}".strip()
        balance += amount if direction == "inflow" else -amount
        rows.append(_txn_row(sid, business_id, bank, account_id, txn_date, description,
                             round(amount, 2), credit=(direction == "inflow"), balance=balance))
        sid += 1
    return rows, sid, balance


def generate_operational_rows(sme, bank, account_id, start_sid, start_balance):
    """Independent, non-ledger transactions: daily cash sales, payroll, operating
    expenses, and (wholesale) high-volume cash-and-carry orders."""
    pattern, business_id = sme["txn_pattern"], sme["business_id"]
    rows, sid, balance = [], start_sid, start_balance
    all_days = [START_DATE + timedelta(days=i) for i in range((END_DATE - START_DATE).days + 1)]

    for d in all_days:
        if pattern == "retail":
            for _ in range(np.random.poisson(6)):
                amt = round(np.random.gamma(2, 250), 2)
                balance += amt
                rows.append(_txn_row(sid, business_id, bank, account_id, d,
                                     "POS SETTLEMENT - DAILY SALES", amt, True, balance))
                sid += 1
        elif pattern == "wholesale":
            for _ in range(np.random.poisson(20)):
                amt = round(np.random.gamma(3, 400), 2)
                balance += amt
                rows.append(_txn_row(sid, business_id, bank, account_id, d,
                                     "CASH AND CARRY ORDER PAYMENT", amt, True, balance))
                sid += 1

        if pattern in ("consulting", "construction", "professional") and d.day == 25:
            per_head = {"consulting": (18_000, 28_000), "construction": (9_000, 15_000),
                        "professional": (15_000, 22_000)}[pattern]
            amt = round(sme["employees"] * random.uniform(*per_head), 2)
            balance -= amt
            rows.append(_txn_row(sid, business_id, bank, account_id, d, "PAYROLL RUN", amt, False, balance))
            sid += 1

        if pattern in ("consulting", "professional") and random.random() < 0.08:
            amt = round(np.random.uniform(500, 6_000), 2)
            balance -= amt
            rows.append(_txn_row(sid, business_id, bank, account_id, d, "OPERATING EXPENSE", amt, False, balance))
            sid += 1
    return rows, sid, balance


def generate_bank_transactions(invoices_df, bills_df):
    all_rows, sid = [], 1
    inv_desc = {"retail": "CUSTOMER INVOICE PAYMENT", "consulting": "CLIENT PAYMENT",
                "construction": "PROJECT MILESTONE PAYMENT", "wholesale": "TRADE ACCOUNT PAYMENT",
                "professional": "RETAINER FEE"}
    bill_desc = {"retail": "SUPPLIER PAYMENT", "consulting": "SUPPLIER PAYMENT",
                 "construction": "SUBCONTRACTOR PAYMENT", "wholesale": "SUPPLIER CREDIT SETTLEMENT",
                 "professional": "SUPPLIER PAYMENT"}

    for sme in SMES:
        business_id = sme["business_id"]
        bank = random.choice(BANKS)
        account_id = f"ACC-{fake.random_number(digits=8, fix_len=True)}"
        balance = round(random.uniform(50_000, 250_000), 2)

        rows, sid, balance = generate_operational_rows(sme, bank, account_id, sid, balance)
        all_rows.extend(rows)

        rows, sid, balance = generate_settlement_rows(
            invoices_df, business_id, bank, account_id, sid, balance,
            status_field="invoice_status", paid_values=STATUS_CHOICES_PAID + ["Partially Paid"],
            description_prefix=inv_desc[sme["txn_pattern"]], counterparty_field="customer_id",
            direction="inflow")
        all_rows.extend(rows)

        rows, sid, balance = generate_settlement_rows(
            bills_df, business_id, bank, account_id, sid, balance,
            status_field="bill_status", paid_values=["Paid", "Partially Paid"],
            description_prefix=bill_desc[sme["txn_pattern"]], counterparty_field="supplier_id",
            direction="outflow")
        all_rows.extend(rows)

    df = pd.DataFrame(all_rows)
    df = df.sort_values(["business_id", "transaction_date"], kind="stable").reset_index(drop=True)
    df["source_record_id"] = [f"BT_{i + 1:07d}" for i in range(len(df))]
    return df


def apply_bank_messiness(df):
    df = df.copy()
    n = len(df)
    for col in ["transaction_reference", "balance_after_transaction", "debit_amount", "credit_amount"]:
        df[col] = df[col].astype(object)

    # Posting delays (0-5 days typical, occasional 12-day late postings)
    delays = np.random.choice([0, 1, 2, 3, 5, 12], size=n, p=[0.5, 0.2, 0.15, 0.08, 0.05, 0.02])
    df["posting_date"] = [d + timedelta(days=int(x)) for d, x in zip(df["transaction_date"], delays)]
    for pos, i in enumerate(df.index):
        if delays[pos] >= 10:
            log_issue("bank_transactions_raw.csv", df.at[i, "source_record_id"], df.at[i, "business_id"],
                      "delayed_posting", f"Posting delayed {delays[pos]} days after transaction_date")

    df["transaction_date"] = df["transaction_date"].apply(random_date_format)
    df["posting_date"] = df["posting_date"].apply(random_date_format)

    idx = df.sample(frac=0.04, random_state=SEED).index
    df.loc[idx, "transaction_reference"] = ""
    for i in idx:
        log_issue("bank_transactions_raw.csv", df.at[i, "source_record_id"], df.at[i, "business_id"],
                  "missing_reference", "transaction_reference missing")

    idx = df.sample(frac=0.03, random_state=SEED + 1).index
    df.loc[idx, "balance_after_transaction"] = ""
    for i in idx:
        log_issue("bank_transactions_raw.csv", df.at[i, "source_record_id"], df.at[i, "business_id"],
                  "missing_value", "balance_after_transaction missing")

    # Sign inconsistency: one bank's export records some debits under credit_amount
    # (the wholesale business has the most debits, so it gives a measurable sample)
    flip_bank = df.loc[df["business_id"] == "SME_004", "bank_name"].iloc[0]
    flip_pool = df[(df["bank_name"] == flip_bank) & (df["debit_amount"] != "")]
    for i in flip_pool.sample(frac=0.08, random_state=SEED + 2).index:
        df.at[i, "credit_amount"] = df.at[i, "debit_amount"]
        df.at[i, "debit_amount"] = ""
        log_issue("bank_transactions_raw.csv", df.at[i, "source_record_id"], df.at[i, "business_id"],
                  "sign_inconsistency", f"Debit recorded under credit_amount in {flip_bank} export")

    # Duplicate imports
    dup_rows = []
    for _, r in df.sample(frac=0.015, random_state=SEED + 3).iterrows():
        dup = r.copy()
        dup["source_record_id"] = f"{r['source_record_id']}_DUP"
        dup_rows.append(dup)
        log_issue("bank_transactions_raw.csv", dup["source_record_id"], r["business_id"],
                  "duplicate", f"Duplicate import of {r['source_record_id']}")
    if dup_rows:
        df = pd.concat([df, pd.DataFrame(dup_rows)], ignore_index=True)

    # Reversals (a debit followed by its reversal)
    rev_rows = []
    candidates = df[(df["debit_amount"] != "") & (~df["source_record_id"].str.endswith("_DUP"))]
    for _, r in candidates.sample(frac=0.008, random_state=SEED + 4).iterrows():
        rev = r.copy()
        rev["source_record_id"] = f"{r['source_record_id']}_REV"
        rev["debit_amount"] = ""
        rev["credit_amount"] = r["debit_amount"]
        rev["transaction_description"] = f"REVERSAL - {r['transaction_description']}"
        rev_rows.append(rev)
        log_issue("bank_transactions_raw.csv", rev["source_record_id"], r["business_id"],
                  "reversal", f"Reversal of {r['source_record_id']}")
    if rev_rows:
        df = pd.concat([df, pd.DataFrame(rev_rows)], ignore_index=True)

    # Inconsistent description spellings
    for i in df.sample(frac=0.03, random_state=SEED + 5).index:
        df.at[i, "transaction_description"] = vary_description(df.at[i, "transaction_description"])
    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Finalize ledgers: mixed-format date strings + duplicate injection
# ---------------------------------------------------------------------------
def _finalize_ledger(df, date_cols, out_cols, dataset, label):
    df = df.copy()
    for c in date_cols:
        df[c] = df[f"{c}_dt"].apply(random_date_format)
    dup_rows = []
    for _, r in df.sample(frac=0.01, random_state=SEED).iterrows():
        dup = r.copy()
        dup["source_record_id"] = f"{r['source_record_id']}_DUP"
        dup_rows.append(dup)
        log_issue(dataset, dup["source_record_id"], r["business_id"],
                  "duplicate", f"Duplicate {label} import of {r['source_record_id']}")
    if dup_rows:
        df = pd.concat([df, pd.DataFrame(dup_rows)], ignore_index=True)
    return df[out_cols].reset_index(drop=True)


def finalize_invoices(df):
    cols = ["source_record_id", "business_id", "invoice_id", "customer_id", "invoice_date",
            "due_date", "invoice_amount", "amount_paid", "invoice_status", "payment_date",
            "currency", "source_file"]
    return _finalize_ledger(df, ["invoice_date", "due_date", "payment_date"], cols,
                            "invoices_raw.csv", "invoice")


def finalize_bills(df):
    cols = ["source_record_id", "business_id", "bill_id", "supplier_id", "bill_date",
            "due_date", "bill_amount", "amount_paid", "bill_status", "payment_date",
            "currency", "source_file"]
    return _finalize_ledger(df, ["bill_date", "due_date", "payment_date"], cols,
                            "supplier_bills_raw.csv", "bill")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main(outdir, force=False):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    if (outdir / "business_profiles_raw.csv").exists() and not force:
        print(f"Raw data already exists in {outdir.resolve()}.\n"
              "Raw data is treated as immutable, so nothing was overwritten.\n"
              "Re-run with --force to regenerate the synthetic dataset.")
        return

    print("Generating business profiles ...")
    profiles = generate_business_profiles()
    print("Generating invoices and supplier bills (economic events, pre-bank) ...")
    invoices_dt = generate_invoices()
    bills_dt = generate_supplier_bills()
    print("Generating bank transactions (ledger-derived settlements + operational noise) ...")
    bank = apply_bank_messiness(generate_bank_transactions(invoices_dt, bills_dt))
    print("Finalizing ledgers (date formats + duplicate imports) ...")
    invoices = finalize_invoices(invoices_dt)
    bills = finalize_bills(bills_dt)

    profiles.to_csv(outdir / "business_profiles_raw.csv", index=False)
    bank.to_csv(outdir / "bank_transactions_raw.csv", index=False)
    invoices.to_csv(outdir / "invoices_raw.csv", index=False)
    bills.to_csv(outdir / "supplier_bills_raw.csv", index=False)

    issues_df = pd.DataFrame(issues_log)
    issues_df.to_csv(outdir / "data-quality-issues-log.csv", index=False)

    lines = ["# Generation Summary\n\n", f"Seed: {SEED}\n\n",
             f"Period: {START_DATE.date()} to {END_DATE.date()}\n\n", "## Row counts\n\n",
             f"- business_profiles_raw.csv: {len(profiles)}\n",
             f"- bank_transactions_raw.csv: {len(bank)}\n",
             f"- invoices_raw.csv: {len(invoices)}\n",
             f"- supplier_bills_raw.csv: {len(bills)}\n\n", "## Injected issues by type\n\n"]
    for _, r in issues_df.groupby(["dataset", "issue_type"]).size().reset_index(name="n").iterrows():
        lines.append(f"- {r['dataset']} / {r['issue_type']}: {r['n']}\n")
    lines.append(f"\nTotal issues logged: {len(issues_df)}\n")
    (outdir / "generation-summary.md").write_text("".join(lines), encoding="utf-8")

    print(f"\nDone. Files written to: {outdir.resolve()}\n")
    print("".join(lines))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", default=str(_DEFAULT_OUTDIR))
    parser.add_argument("--force", action="store_true", help="Overwrite existing raw files")
    args = parser.parse_args()
    main(args.outdir, args.force)
