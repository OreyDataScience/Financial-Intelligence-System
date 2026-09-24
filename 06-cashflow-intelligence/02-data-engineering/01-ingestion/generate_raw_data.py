"""
Phase 06 - Synthetic SME Raw Data Generator
Orey Analytics - Cash Flow Intelligence

Implements DATA-SPECIFICATION.md. Generates deliberately messy raw datasets
for 5 South African SMEs across a 24-month history (2024-01-01 to 2025-12-31).

Outputs (into --outdir, default ./01-data/01-raw):
    business_profiles_raw.csv
    bank_transactions_raw.csv
    invoices_raw.csv
    supplier_bills_raw.csv
    data-quality-issues-log.csv
    generation-summary.md

Reproducible via fixed SEED.
"""

import argparse
import random
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from faker import Faker

# Default output path is resolved relative to THIS FILE, not the current
# working directory - so it's correct no matter where you run the script from.
# This script lives at: 02-data-engineering/01-ingestion/generate_raw_data.py
# Target:                01-data/01-raw/
_SCRIPT_DIR = Path(__file__).resolve().parent
_DEFAULT_OUTDIR = _SCRIPT_DIR.parent.parent / "01-data" / "01-raw"

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
fake = Faker()
Faker.seed(SEED)

START_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2025, 12, 31)

PROVINCES = ["Gauteng", "Western Cape", "KwaZulu-Natal", "Eastern Cape", "Free State"]
BANKS = ["FNB", "Standard Bank", "Absa", "Nedbank", "Capitec"]

# ---------------------------------------------------------------------------
# SME profile definitions (drive generation parameters, not literal rows)
# ---------------------------------------------------------------------------
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

def random_date_format(d: datetime) -> str:
    """Return a date string in one of several inconsistent real-world formats."""
    fmt = random.choice(["iso", "slash", "text"])
    if fmt == "iso":
        return d.strftime("%Y-%m-%d")
    elif fmt == "slash":
        return d.strftime("%d/%m/%Y")
    else:
        return d.strftime("%d %b %Y")

def vary_description(base: str) -> str:
    variant = random.choice(["exact", "abbrev", "hyphen", "upper"])
    if variant == "exact":
        return base
    elif variant == "abbrev":
        return base.replace(" SUPPLIERS", " SUPP").replace(" TRADERS", " TRD")
    elif variant == "hyphen":
        return base.replace(" ", "-")
    else:
        return base.upper()

# ---------------------------------------------------------------------------
# 1. business_profiles_raw.csv
# ---------------------------------------------------------------------------
def generate_business_profiles():
    rows = []
    sid = 0
    for sme in SMES:
        sid += 1
        row = dict(
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
        )
        rows.append(row)

    df = pd.DataFrame(rows)
    df["employee_count"] = df["employee_count"].astype(object)
    df["annual_revenue"] = df["annual_revenue"].astype(object)
    df["financial_year_end"] = df["financial_year_end"].astype(object)

    # Inject: missing employee_count
    idx = df.sample(1, random_state=SEED).index
    for i in idx:
        rec_id = df.at[i, "source_record_id"]
        df.at[i, "employee_count"] = np.nan
        log_issue("business_profiles_raw.csv", rec_id, df.at[i, "business_id"],
                   "missing_value", "employee_count missing")

    # Inject: annual_revenue as text with currency symbol
    idx = df.sample(1, random_state=SEED + 1).index
    for i in idx:
        rec_id = df.at[i, "source_record_id"]
        df.at[i, "annual_revenue"] = f"R {df.at[i, 'annual_revenue']:,}"
        log_issue("business_profiles_raw.csv", rec_id, df.at[i, "business_id"],
                   "type_inconsistency", "annual_revenue stored as formatted text, not numeric")

    # Inject: missing financial_year_end
    idx = df.sample(1, random_state=SEED + 2).index
    for i in idx:
        rec_id = df.at[i, "source_record_id"]
        df.at[i, "financial_year_end"] = np.nan
        log_issue("business_profiles_raw.csv", rec_id, df.at[i, "business_id"],
                   "missing_value", "financial_year_end missing")

    # Inject: one conflicting duplicate profile version (stale employee_count/revenue)
    conflict_sme = SMES[0]
    sid += 1
    dup_row = dict(
        source_record_id=f"BP_{sid:04d}",
        business_id=conflict_sme["business_id"],
        business_name=conflict_sme["name"],
        industry=conflict_sme["industry"],
        business_start_date=conflict_sme["start"].strftime("%Y-%m-%d"),
        province=conflict_sme["province"],
        employee_count=conflict_sme["employees"] - 3,  # stale/conflicting figure
        annual_revenue=conflict_sme["annual_revenue"] * 0.8,  # stale figure
        accounting_basis=conflict_sme["basis"],
        financial_year_end=conflict_sme["fy_end"],
        source_file="business_profiles_export_2025_stale.csv",
    )
    df = pd.concat([df, pd.DataFrame([dup_row])], ignore_index=True)
    log_issue("business_profiles_raw.csv", dup_row["source_record_id"], conflict_sme["business_id"],
               "conflicting_record", "Duplicate profile version with stale employee_count and annual_revenue")

    return df

# ---------------------------------------------------------------------------
# 2. bank_transactions_raw.csv
# ---------------------------------------------------------------------------
def daterange_days(start, end):
    days = (end - start).days
    return [start + timedelta(days=i) for i in range(days + 1)]

def generate_bank_transactions_for_sme(sme, start_sid):
    pattern = sme["txn_pattern"]
    business_id = sme["business_id"]
    bank = random.choice(BANKS)
    account_id = f"ACC-{fake.random_number(digits=8, fix_len=True)}"
    rows = []
    sid = start_sid
    balance = round(random.uniform(50_000, 250_000), 2)
    sign_flip_source_file = None

    all_days = daterange_days(START_DATE, END_DATE)

    if pattern == "retail":
        # Daily small credits (sales), periodic supplier debits
        for d in all_days:
            n_sales = np.random.poisson(6)
            for _ in range(n_sales):
                amt = round(np.random.gamma(2, 250), 2)
                balance += amt
                rows.append(_txn_row(sid, business_id, bank, account_id, d,
                                      "POS SETTLEMENT - DAILY SALES", amt, credit=True,
                                      balance=balance))
                sid += 1
            if d.day in (5, 20):  # biweekly supplier payment
                amt = round(np.random.uniform(8_000, 25_000), 2)
                balance -= amt
                rows.append(_txn_row(sid, business_id, bank, account_id, d,
                                      vary_description("ABC SUPPLIERS PAYMENT"), amt,
                                      credit=False, balance=balance))
                sid += 1

    elif pattern == "consulting":
        for d in all_days:
            if d.day == 25:  # payroll
                amt = round(sme["employees"] * random.uniform(18_000, 28_000), 2)
                balance -= amt
                rows.append(_txn_row(sid, business_id, bank, account_id, d,
                                      "PAYROLL RUN", amt, credit=False, balance=balance))
                sid += 1
            if random.random() < 0.05:  # irregular client payment
                amt = round(np.random.uniform(15_000, 180_000), 2)
                balance += amt
                rows.append(_txn_row(sid, business_id, bank, account_id, d,
                                      f"CLIENT PAYMENT {fake.company().upper()}", amt,
                                      credit=True, balance=balance))
                sid += 1
            if random.random() < 0.08:  # operating costs
                amt = round(np.random.uniform(500, 6_000), 2)
                balance -= amt
                rows.append(_txn_row(sid, business_id, bank, account_id, d,
                                      "OPERATING EXPENSE", amt, credit=False, balance=balance))
                sid += 1

    elif pattern == "construction":
        for d in all_days:
            if random.random() < 0.02:  # large infrequent project payment
                amt = round(np.random.uniform(250_000, 1_500_000), 2)
                balance += amt
                rows.append(_txn_row(sid, business_id, bank, account_id, d,
                                      f"PROJECT MILESTONE PAYMENT {fake.company().upper()}", amt,
                                      credit=True, balance=balance))
                sid += 1
            if random.random() < 0.06:  # subcontractor / materials payment
                amt = round(np.random.uniform(20_000, 300_000), 2)
                balance -= amt
                rows.append(_txn_row(sid, business_id, bank, account_id, d,
                                      vary_description("SUBCONTRACTOR PAYMENT"), amt,
                                      credit=False, balance=balance))
                sid += 1
            if d.day == 25:
                amt = round(sme["employees"] * random.uniform(9_000, 15_000), 2)
                balance -= amt
                rows.append(_txn_row(sid, business_id, bank, account_id, d,
                                      "PAYROLL RUN", amt, credit=False, balance=balance))
                sid += 1

    elif pattern == "wholesale":
        for d in all_days:
            n_orders = np.random.poisson(20)
            for _ in range(n_orders):
                amt = round(np.random.gamma(3, 400), 2)
                balance += amt
                rows.append(_txn_row(sid, business_id, bank, account_id, d,
                                      "CUSTOMER ORDER PAYMENT", amt, credit=True, balance=balance))
                sid += 1
            if d.day in (10, 25):  # supplier credit settlement
                amt = round(np.random.uniform(60_000, 220_000), 2)
                balance -= amt
                rows.append(_txn_row(sid, business_id, bank, account_id, d,
                                      vary_description("SUPPLIER CREDIT SETTLEMENT"), amt,
                                      credit=False, balance=balance))
                sid += 1

    else:  # professional services
        for d in all_days:
            if d.day == 1:  # recurring retainer revenue
                for _ in range(random.randint(2, 5)):
                    amt = round(np.random.uniform(8_000, 22_000), 2)
                    balance += amt
                    rows.append(_txn_row(sid, business_id, bank, account_id, d,
                                          f"RETAINER FEE {fake.company().upper()}", amt,
                                          credit=True, balance=balance))
                    sid += 1
            if d.day == 25:
                amt = round(sme["employees"] * random.uniform(15_000, 22_000), 2)
                balance -= amt
                rows.append(_txn_row(sid, business_id, bank, account_id, d,
                                      "PAYROLL RUN", amt, credit=False, balance=balance))
                sid += 1
            if random.random() < 0.04:
                amt = round(np.random.uniform(400, 4_000), 2)
                balance -= amt
                rows.append(_txn_row(sid, business_id, bank, account_id, d,
                                      "OPERATING EXPENSE", amt, credit=False, balance=balance))
                sid += 1

    df = pd.DataFrame(rows)
    return df, sid

def _txn_row(sid, business_id, bank, account_id, txn_date, description, amount, credit, balance):
    debit_amount = "" if credit else amount
    credit_amount = amount if credit else ""
    return dict(
        source_record_id=f"BT_{sid:07d}",
        business_id=business_id,
        bank_name=bank,
        account_id=account_id,
        transaction_date=txn_date,  # kept as datetime until final formatting pass
        posting_date=txn_date,
        transaction_description=description,
        transaction_reference=f"REF{fake.random_number(digits=9, fix_len=True)}",
        debit_amount=debit_amount,
        credit_amount=credit_amount,
        balance_after_transaction=round(balance, 2),
        currency="ZAR",
        source_file=f"{bank.replace(' ', '_').lower()}_statement_export.csv",
    )

def apply_bank_messiness(df):
    df = df.copy()
    n = len(df)
    for col in ["transaction_reference", "balance_after_transaction", "debit_amount", "credit_amount"]:
        df[col] = df[col].astype(object)

    # Posting delays (0-5 days typical, some 10+ day late postings)
    delays = np.random.choice([0, 1, 2, 3, 5, 12], size=n, p=[0.5, 0.2, 0.15, 0.08, 0.05, 0.02])
    df["posting_date"] = [d + timedelta(days=int(delay)) for d, delay in zip(df["transaction_date"], delays)]
    late_idx = df.index[delays >= 10]
    for i in late_idx:
        log_issue("bank_transactions_raw.csv", df.at[i, "source_record_id"], df.at[i, "business_id"],
                   "delayed_posting", f"Posting delayed {delays[list(df.index).index(i)]} days after transaction_date")

    # Format transaction_date / posting_date inconsistently (per-row independent choice)
    df["transaction_date"] = df["transaction_date"].apply(random_date_format)
    df["posting_date"] = df["posting_date"].apply(random_date_format)

    # Missing transaction_reference (~4%)
    miss_idx = df.sample(frac=0.04, random_state=SEED).index
    df.loc[miss_idx, "transaction_reference"] = ""
    for i in miss_idx:
        log_issue("bank_transactions_raw.csv", df.at[i, "source_record_id"], df.at[i, "business_id"],
                   "missing_reference", "transaction_reference missing")

    # Missing balance_after_transaction (~3%)
    miss_bal_idx = df.sample(frac=0.03, random_state=SEED + 1).index
    df.loc[miss_bal_idx, "balance_after_transaction"] = ""
    for i in miss_bal_idx:
        log_issue("bank_transactions_raw.csv", df.at[i, "source_record_id"], df.at[i, "business_id"],
                   "missing_value", "balance_after_transaction missing")

    # Sign inconsistency: for one bank's exports, flip debit/credit convention on a subset
    flip_bank = df["bank_name"].iloc[0]
    flip_idx = df[(df["bank_name"] == flip_bank)].sample(frac=0.02, random_state=SEED + 2).index
    for i in flip_idx:
        if df.at[i, "debit_amount"] != "":
            amt = df.at[i, "debit_amount"]
            df.at[i, "debit_amount"] = ""
            df.at[i, "credit_amount"] = amt  # incorrectly represented as positive/credit
            log_issue("bank_transactions_raw.csv", df.at[i, "source_record_id"], df.at[i, "business_id"],
                       "sign_inconsistency", f"Debit incorrectly recorded under credit_amount for {flip_bank} export")

    # Duplicate imports (~1.5%): same txn, new source_record_id
    dup_sample = df.sample(frac=0.015, random_state=SEED + 3)
    dup_rows = []
    for _, r in dup_sample.iterrows():
        dup = r.copy()
        new_id = f"{r['source_record_id']}_DUP"
        dup["source_record_id"] = new_id
        dup_rows.append(dup)
        log_issue("bank_transactions_raw.csv", new_id, r["business_id"],
                   "duplicate", f"Duplicate import of {r['source_record_id']}")
    if dup_rows:
        df = pd.concat([df, pd.DataFrame(dup_rows)], ignore_index=True)

    # Reversals: pick a small sample of debits, add matching reversal 1-4 days later
    reversal_candidates = df[df["debit_amount"] != ""].sample(frac=0.008, random_state=SEED + 4)
    reversal_rows = []
    for _, r in reversal_candidates.iterrows():
        rev = r.copy()
        rev_sid = f"{r['source_record_id']}_REV"
        rev["source_record_id"] = rev_sid
        rev["debit_amount"] = ""
        rev["credit_amount"] = r["debit_amount"]
        rev["transaction_description"] = f"REVERSAL - {r['transaction_description']}"
        reversal_rows.append(rev)
        log_issue("bank_transactions_raw.csv", rev_sid, r["business_id"],
                   "reversal", f"Reversal of {r['source_record_id']}")
    if reversal_rows:
        df = pd.concat([df, pd.DataFrame(reversal_rows)], ignore_index=True)

    # Inconsistent description casing/spacing already partially applied via vary_description;
    # add a few more ad hoc variants across all rows
    variant_idx = df.sample(frac=0.03, random_state=SEED + 5).index
    for i in variant_idx:
        df.at[i, "transaction_description"] = vary_description(df.at[i, "transaction_description"])

    return df.reset_index(drop=True)

def generate_bank_transactions():
    all_dfs = []
    sid = 1
    for sme in SMES:
        df, sid = generate_bank_transactions_for_sme(sme, sid)
        all_dfs.append(df)
    df = pd.concat(all_dfs, ignore_index=True)
    df = apply_bank_messiness(df)
    return df

# ---------------------------------------------------------------------------
# 3 & 4. invoices_raw.csv / supplier_bills_raw.csv
# ---------------------------------------------------------------------------
def generate_invoices():
    rows = []
    sid = 1
    for sme in SMES:
        business_id = sme["business_id"]
        n_invoices = {"retail": 40, "consulting": 60, "construction": 30,
                      "wholesale": 250, "professional": 90}[sme["txn_pattern"]]
        customers = [f"CUST_{sme['business_id']}_{i:03d}" for i in range(1, 16)]

        for _ in range(n_invoices):
            invoice_date = START_DATE + timedelta(days=random.randint(0, (END_DATE - START_DATE).days))
            terms = random.choice([15, 30, 45, 60])
            due_date = invoice_date + timedelta(days=terms)
            amount = round(np.random.uniform(3_000, 400_000) if sme["txn_pattern"] == "construction"
                            else np.random.uniform(1_000, 60_000), 2)

            status_roll = random.random()
            if status_roll < 0.65:
                status = random.choice(["Paid", "paid", "PAID"])
                paid_amt = amount
                pay_delay = random.randint(-2, terms + 30)  # occasionally "paid" before invoice (bad data)
                payment_date = invoice_date + timedelta(days=pay_delay)
            elif status_roll < 0.85:
                status = "Partially Paid"
                paid_amt = round(amount * random.uniform(0.2, 0.8), 2)
                payment_date = invoice_date + timedelta(days=random.randint(5, terms + 20))
            else:
                status = random.choice(["Unpaid", "Overdue"])
                paid_amt = 0
                payment_date = None

            rows.append(dict(
                source_record_id=f"INV_{sid:06d}",
                business_id=business_id,
                invoice_id=f"{business_id}-INV-{sid:05d}",
                customer_id=random.choice(customers),
                invoice_date=random_date_format(invoice_date),
                due_date=random_date_format(due_date) if random.random() > 0.05 else "",
                invoice_amount=amount,
                amount_paid=paid_amt,
                invoice_status=status,
                payment_date=random_date_format(payment_date) if payment_date else "",
                currency="ZAR",
                source_file=f"{business_id.lower()}_accounting_export.csv",
            ))
            sid += 1

    df = pd.DataFrame(rows)

    # missing due_date already partially injected inline; log it
    for i, r in df.iterrows():
        if r["due_date"] == "":
            log_issue("invoices_raw.csv", r["source_record_id"], r["business_id"],
                       "missing_value", "due_date missing")
        if r["invoice_status"] in ("Paid", "paid", "PAID") and r["amount_paid"] < r["invoice_amount"] * 0.99:
            log_issue("invoices_raw.csv", r["source_record_id"], r["business_id"],
                       "amount_mismatch", "Marked Paid but amount_paid does not match invoice_amount")

    # Duplicate invoices (~1%)
    dup_sample = df.sample(frac=0.01, random_state=SEED)
    dup_rows = []
    for _, r in dup_sample.iterrows():
        dup = r.copy()
        dup["source_record_id"] = f"{r['source_record_id']}_DUP"
        dup_rows.append(dup)
        log_issue("invoices_raw.csv", dup["source_record_id"], r["business_id"],
                   "duplicate", f"Duplicate invoice import of {r['source_record_id']}")
    if dup_rows:
        df = pd.concat([df, pd.DataFrame(dup_rows)], ignore_index=True)

    return df.reset_index(drop=True)

def generate_supplier_bills():
    rows = []
    sid = 1
    for sme in SMES:
        business_id = sme["business_id"]
        n_bills = {"retail": 50, "consulting": 20, "construction": 70,
                   "wholesale": 200, "professional": 15}[sme["txn_pattern"]]
        suppliers = [f"SUPP_{sme['business_id']}_{i:03d}" for i in range(1, 11)]

        for _ in range(n_bills):
            bill_date = START_DATE + timedelta(days=random.randint(0, (END_DATE - START_DATE).days))
            terms = random.choice([15, 30, 45, 60])
            due_date = bill_date + timedelta(days=terms)
            amount = round(np.random.uniform(2_000, 250_000) if sme["txn_pattern"] == "construction"
                            else np.random.uniform(500, 40_000), 2)

            status_roll = random.random()
            if status_roll < 0.7:
                status = "Paid"
                paid_amt = amount
                payment_date = bill_date + timedelta(days=random.randint(1, terms + 15))
            elif status_roll < 0.88:
                status = "Partially Paid"
                paid_amt = round(amount * random.uniform(0.3, 0.75), 2)
                payment_date = bill_date + timedelta(days=random.randint(5, terms + 20))
            else:
                status = random.choice(["Unpaid", "Overdue"])
                paid_amt = 0
                payment_date = None

            missing_supplier = random.random() < 0.03
            rows.append(dict(
                source_record_id=f"BILL_{sid:06d}",
                business_id=business_id,
                bill_id=f"{business_id}-BILL-{sid:05d}",
                supplier_id="" if missing_supplier else random.choice(suppliers),
                bill_date=random_date_format(bill_date),
                due_date=random_date_format(due_date),
                bill_amount=amount,
                amount_paid=paid_amt,
                bill_status=status,
                payment_date=random_date_format(payment_date) if payment_date else "",
                currency="ZAR",
                source_file=f"{business_id.lower()}_accounting_export.csv",
            ))
            if missing_supplier:
                log_issue("supplier_bills_raw.csv", f"BILL_{sid:06d}", business_id,
                           "missing_value", "supplier_id missing")
            sid += 1

    df = pd.DataFrame(rows)

    # Duplicate bills (~1%)
    dup_sample = df.sample(frac=0.01, random_state=SEED)
    dup_rows = []
    for _, r in dup_sample.iterrows():
        dup = r.copy()
        dup["source_record_id"] = f"{r['source_record_id']}_DUP"
        dup_rows.append(dup)
        log_issue("supplier_bills_raw.csv", dup["source_record_id"], r["business_id"],
                   "duplicate", f"Duplicate bill import of {r['source_record_id']}")
    if dup_rows:
        df = pd.concat([df, pd.DataFrame(dup_rows)], ignore_index=True)

    return df.reset_index(drop=True)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main(outdir: str):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    print("Generating business_profiles_raw.csv ...")
    profiles = generate_business_profiles()
    profiles.to_csv(outdir / "business_profiles_raw.csv", index=False)

    print("Generating bank_transactions_raw.csv ...")
    bank_txns = generate_bank_transactions()
    bank_txns.to_csv(outdir / "bank_transactions_raw.csv", index=False)

    print("Generating invoices_raw.csv ...")
    invoices = generate_invoices()
    invoices.to_csv(outdir / "invoices_raw.csv", index=False)

    print("Generating supplier_bills_raw.csv ...")
    bills = generate_supplier_bills()
    bills.to_csv(outdir / "supplier_bills_raw.csv", index=False)

    print("Writing data-quality-issues-log.csv ...")
    issues_df = pd.DataFrame(issues_log)
    issues_df.to_csv(outdir / "data-quality-issues-log.csv", index=False)

    summary_lines = [
        "# Generation Summary\n",
        f"Seed: {SEED}\n",
        f"Period: {START_DATE.date()} to {END_DATE.date()}\n\n",
        "## Row counts\n",
        f"- business_profiles_raw.csv: {len(profiles)}\n",
        f"- bank_transactions_raw.csv: {len(bank_txns)}\n",
        f"- invoices_raw.csv: {len(invoices)}\n",
        f"- supplier_bills_raw.csv: {len(bills)}\n\n",
        "## Injected issues by type\n",
    ]
    if len(issues_df):
        counts = issues_df.groupby(["dataset", "issue_type"]).size().reset_index(name="count")
        for _, r in counts.iterrows():
            summary_lines.append(f"- {r['dataset']} / {r['issue_type']}: {r['count']}\n")
    summary_lines.append(f"\nTotal issues logged: {len(issues_df)}\n")

    with open(outdir / "generation-summary.md", "w") as f:
        f.writelines(summary_lines)

    print(f"\nDone. Files written to: {outdir.resolve()}")
    print("".join(summary_lines))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", default=str(_DEFAULT_OUTDIR))
    args = parser.parse_args()
    main(args.outdir)