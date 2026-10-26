
# Orey Analytics
## Phase 06 — Cash Flow Intelligence
### Module 04: Expense Intelligence

---

## 1. Module Overview

The Expense Intelligence module analyses supplier-bill records to help monitor business purchasing obligations, understand expense-related trends, assess supplier concentration, and identify data-quality and reconciliation risks.

The module is designed to support the wider Orey Analytics Cash Flow Intelligence system through PostgreSQL analytical views.

It transforms the processed supplier-bill data into structured monthly metrics and business-level indicators that can subsequently be consumed by forecasting, liquidity monitoring, risk analysis, dashboards, and executive reporting components.

**Core objectives:**

- Monitor supplier-bill amounts and indicative outstanding balances.
- Compare supplier-bill amounts across observed calendar months.
- Calculate rolling measures using observed monthly records.
- Assess supplier concentration using identifiable supplier records.
- Identify inconsistencies and data-quality risks.
- Surface supplier-bill reconciliation concerns.
- Preserve transparency regarding the verification status of financial information.

This module analyses supplier-bill records. It does not independently establish a business's accounting expenses or verify cash leaving its bank accounts.

---

## 2. Architecture and Dependencies

**Database:** `orey_cashflow_dev`

**Database schema:** `analytics`

**Primary source table:**

- `processed.supplier_bills`

**Supporting source table:**

- `processed.business_profiles`

**Output views:**

- `analytics.v_monthly_expense_metrics`
- `analytics.v_expense_trends`
- `analytics.v_supplier_concentration`
- `analytics.v_expense_quality`
- `analytics.v_consolidated_expenses`

The analytical views read processed records and do not modify the underlying source data.

### Processing flow

```text
processed.supplier_bills
           |
           v
001_monthly_expense_metrics.sql
           |
           +------------------------------+
           |                              |
           v                              v
002_expense_trends.sql       003_supplier_concentration.sql
           |                              |
           +---------------+--------------+
                           |
processed.supplier_bills  |
           |               |
           v               |
004_expense_quality.sql    |
           |               |
           +-------+-------+
                   |
                   v
005_consolidated_expenses.sql
                   |
                   v
analytics.v_consolidated_expenses
```

The consolidated view uses the monthly metrics view as its base, joins the trend and supplier-concentration views at business, currency, and month level, and joins separately aggregated quality indicators at business and currency level.

---

## 3. SQL Scripts and Responsibilities

### 001 — Monthly Expense Metrics

**File:** `001_monthly_expense_metrics.sql`

**Output:** `analytics.v_monthly_expense_metrics`

Calculates monthly supplier-bill indicators for each business and currency.

Key outputs include:

- Supplier-bill count.
- Non-duplicate bill count.
- Duplicate bill count.
- Total supplier-bill amount.
- Non-duplicate supplier-bill amount.
- Amount recorded as paid on supplier bills.
- Indicative outstanding bill amount.
- Counts of selected data-quality and reconciliation flags.

Bills without a standardized bill date cannot be assigned to a monthly period and are excluded from the monthly aggregation. Their source records remain available for quality analysis.

The amount recorded as paid on bills is not automatically equivalent to a verified bank payment.

### 002 — Expense Trends

**File:** `002_expense_trends.sql`

**Output:** `analytics.v_expense_trends`

Evaluates changes in supplier-bill amounts over time.

Key outputs include:

- Previous observed month.
- Previous calendar month's bill amounts, where a valid comparison exists.
- Month-over-month changes and percentage changes.
- Rolling three-observed-month bill amounts.
- Rolling non-duplicate bill amounts.
- Average bill amount per observed month across the three-row window.
- Indicators identifying incomplete rolling windows.
- Indicators identifying unavailable month-over-month comparisons.

**Interpretation rules:**

1. Month-over-month comparisons are only valid when the previous observation is the immediately preceding calendar month.
2. A three-row rolling window represents the latest three observed monthly rows. It does not necessarily represent three consecutive calendar months.
3. The rolling-window completeness indicator confirms the presence of three observed rows, not the completeness of every calendar month.
4. Missing observations must not be interpreted as zero-valued months.

These measures describe supplier-bill activity rather than independently verified accounting expense trends.

### 003 — Supplier Concentration

**File:** `003_supplier_concentration.sql`

**Output:** `analytics.v_supplier_concentration`

Evaluates the distribution of identifiable supplier-bill amounts.

Key outputs include:

- Total non-duplicate bill amount.
- Identifiable positive supplier-bill amount.
- Number of identifiable suppliers.
- Number of suppliers with positive bill amounts.
- Bill records with missing supplier identifiers.
- Largest supplier share.
- Supplier concentration Herfindahl–Hirschman Index (HHI).
- Descriptive supplier-concentration band.
- Indicators identifying incomplete supplier information.

Duplicate-flagged bills are excluded from the relevant concentration calculations.

The HHI is a descriptive concentration measure calculated from identifiable positive supplier amounts. Its descriptive bands are not validated Orey credit-risk rules, probability-of-default estimates, or lending decisions.

Missing supplier identities can limit the reliability of concentration analysis.

### 004 — Expense Quality

**File:** `004_expense_quality.sql`

**Output:** `analytics.v_expense_quality`

Provides bill-level quality and reconciliation indicators.

The view identifies conditions including:

- Missing supplier identifiers.
- Paid-amount mismatches.
- Duplicate bills.
- Missing standardized bill or due dates.
- Unparsed payment dates.
- Negative bill amounts or recorded paid amounts.
- Recorded payments exceeding bill amounts.
- Due dates or payment dates preceding bill dates.
- Reconciliation statuses requiring review.
- Incomplete bank-match evidence.
- Differences between matched bank amounts and bill amounts.
- Negative indicative outstanding balances.

The combined `requires_quality_review_flag` identifies records that trigger one or more of the conditions included in its definition.

A flagged record is not automatically fraudulent or incorrect. It identifies a condition that may require investigation.

A record that does not trigger the combined flag is not necessarily fully verified.

### 005 — Consolidated Expenses

**File:** `005_consolidated_expenses.sql`

**Output:** `analytics.v_consolidated_expenses`

Combines monthly metrics, expense trends, supplier concentration, and aggregated quality indicators.

The intended output grain is:

`business_id + currency + month_start`

The monthly metrics view provides the base records. Trend and supplier-concentration data are joined using:

- `business_id`
- `currency`
- `month_start`

Quality indicators are aggregated separately by `business_id` and `currency` before joining. This prevents bill-level quality records from multiplying monthly metrics.

**Important:** The `business_currency_` quality columns represent all available bill records for the relevant business and currency. They are not restricted to the month shown in a particular row.

The consolidated view explicitly sets:

- `accounting_expenses_verified = FALSE`
- `bank_outflows_verified = FALSE`

These safeguards must remain in place until appropriate independent verification is implemented.

---

## 4. Execution Order

Run the scripts in the following order from the repository root:

1. `001_monthly_expense_metrics.sql`
2. `002_expense_trends.sql`
3. `003_supplier_concentration.sql`
4. `004_expense_quality.sql`
5. `005_consolidated_expenses.sql`

The scripts depend on views created earlier in the sequence. Run the prerequisite scripts before running the consolidated view after a fresh database setup.

### Execution command

Example for Script 005:

```powershell
psql -U postgres -d orey_cashflow_dev -v ON_ERROR_STOP=1 -f "05-cashflow-intelligence\04-expense-intelligence\005_consolidated_expenses.sql"
```

A successful execution should return:

```text
CREATE VIEW
```

The `ON_ERROR_STOP=1` option makes `psql` stop when an SQL error occurs.

---

## 5. Validation and Current Build Status

The five SQL views have been created and tested in the development database.

### Script validation results

| Validation | Observed result |
|---|---:|
| Bill records in expense-quality view | 355 |
| Records requiring quality review | 70 |
| Unparsed payment dates | 0 |
| Payment dates before bill dates | 0 |
| Consolidated monthly rows | 98 |
| Distinct businesses in consolidated view | 5 |
| Rows marked as verified accounting expenses | 0 |
| Rows marked as verified bank outflows | 0 |

These figures describe the current development dataset and should be refreshed after changes to the source data or analytical logic.

The 70 records requiring review can contain multiple quality issues per bill. They should not be interpreted as 70 unique errors.

The 98 consolidated rows represent monthly business-currency combinations, not individual bills.

### Consolidated view validation query

```sql
SELECT
    COUNT(*) AS monthly_rows,
    COUNT(DISTINCT business_id) AS businesses,

    COUNT(*) FILTER (
        WHERE accounting_expenses_verified
    ) AS verified_accounting_expense_rows,

    COUNT(*) FILTER (
        WHERE bank_outflows_verified
    ) AS verified_bank_outflow_rows

FROM analytics.v_consolidated_expenses;
```

Expected result for the currently validated development dataset:

- `monthly_rows`: 98
- `businesses`: 5
- `verified_accounting_expense_rows`: 0
- `verified_bank_outflow_rows`: 0

---

## 6. Financial Interpretation and Limitations

This module is intended for financial intelligence and monitoring. Its output must be interpreted according to the reliability of its source records.

### Supplier-bill amounts versus accounting expenses

Supplier-bill amounts represent the values recorded in the processed bill dataset. They must not automatically be treated as recognized accounting expenses.

Accounting treatment may depend on the business's accounting basis, expense recognition policies, invoice validity, accruals, credit notes, and other supporting records.

### Recorded payments versus bank outflows

An amount recorded as paid on a supplier bill does not independently prove that the corresponding payment left the business's bank account.

Bank transaction reconciliation and supporting evidence are required before reporting an amount as a verified bank outflow.

### Indicative outstanding balances

The indicative bill balance is calculated as:

`bill_amount - amount_paid`

This is a monitoring indicator. It may be affected by duplicate bills, incorrect recorded payments, credit notes, disputed invoices, or incomplete source data.

A negative indicative balance requires interpretation rather than automatic correction.

### Missing dates and incomplete periods

Records without standardized bill dates cannot be reliably assigned to monthly periods.

Consequently, monthly bill totals may not include every record in the source dataset. Bill-level quality indicators should be consulted when assessing data completeness.

### Supplier concentration

Concentration measures depend on the completeness and correctness of supplier identities and bill amounts. Missing supplier identifiers can understate or otherwise distort the apparent distribution of supplier spending.

### Quality flags

Quality flags are investigative indicators. They should not be interpreted as proof of fraud, financial distress, or deliberate misreporting.

Original source values should be preserved, with corrections handled through controlled data-engineering and review processes.

---

## 7. Integration with the Wider Cash Flow Intelligence System

The module is designed to support subsequent analytical components, including:

- Cash-flow monitoring.
- Liquidity and payment-obligation analysis.
- Cash-flow forecasting.
- Scenario analysis.
- Financial risk monitoring.
- SME-facing dashboards.
- Executive summary reporting.

Integration should preserve business identifiers, currency distinctions, reporting periods, and source-verification status.

Supplier-bill indicators should not be substituted directly for bank transaction outflows in cash-flow models without a defined reconciliation and validation process.

---

## 8. Maintenance and Governance

When updating this module:

1. Preserve the processed source records and their original values.
2. Use standardized dates for date comparisons and monthly grouping.
3. Avoid silently replacing missing values with zero.
4. Keep currency-specific metrics separate unless an explicit conversion methodology is implemented.
5. Confirm that joins preserve the intended output grain.
6. Re-run validation queries after changes to source data or SQL logic.
7. Document changes to metric definitions and quality-flag logic.
8. Keep verification indicators false until their verification criteria have been implemented and evidenced.
9. Review concentration bands before using them in formal risk decisions.
10. Ensure downstream dashboards clearly distinguish observed, derived, indicative, and verified values.

---

## 9. Current Status

**Module 04 — Expense Intelligence: Built and validated in the development database.**

The five analytical views are available in the `analytics` schema.

The module provides monthly supplier-bill monitoring, trend analysis, supplier concentration, bill-level quality indicators, and a consolidated output for downstream use.

It does not yet provide independently verified accounting expense totals or independently verified bank outflows.

**Orey Analytics — Data-Driven Financial Intelligence**
