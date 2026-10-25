# Orey Analytics — Cash Flow Metrics

## 1. Purpose

This module develops reusable SQL views for analysing monthly cash-flow movements across SMEs. It provides a consistent metrics layer for identifying movement patterns, monitoring rolling performance, detecting persistent trends, and measuring volatility.

The module reads from the existing PostgreSQL analytics views and does not modify the underlying processed data.

## 2. Architecture

**Database:** `orey_cashflow_dev`  
**Schema:** `analytics`  
**Source view:** `analytics.v_monthly_cashflow_monitoring`

The module currently contains four SQL view definitions.

## 3. SQL Views

### 001 — Monthly Cash Flow Metrics

**File:** `001_monthly_cashflow_metrics.sql`  
**View:** `analytics.v_monthly_cashflow_metrics`

Calculates monthly indicators, including:
- Net movement margin.
- Outflow-to-inflow ratio.
- Zero-inflow and zero-outflow flags.
- Negative net movement flag.
- Data-quality attention flag.
- Prior-month comparisons and source quality indicators.

Ratios requiring positive inflows are returned as `NULL` when inflows are zero or unavailable.

### 002 — Rolling Cash Flow Metrics

**File:** `002_rolling_cashflow_metrics.sql`  
**View:** `analytics.v_rolling_cashflow_metrics`

Calculates rolling metrics, including:
- Three-month observation count.
- Three-month average and sample standard deviation of net bank movement.
- Six-month observation count and average net bank movement.
- Number of negative-movement months in the three-month window.
- Three-month and six-month completeness flags.

### 003 — Cash Flow Trend Persistence

**File:** `003_cashflow_trend_persistence.sql`  
**View:** `analytics.v_cashflow_trend_persistence`

Measures consecutive monthly patterns in:
- Negative net bank movement.
- Declining inflows.
- Increasing outflows.

It also produces persistence flags that identify when each pattern reaches at least three consecutive months. Consecutive streaks reset when the relevant condition ends or a calendar-month gap occurs.

These indicators highlight patterns for investigation; they do not independently establish insolvency or financial distress.

### 004 — Cash Flow Volatility Metrics

**File:** `004_cashflow_volatility_metrics.sql`  
**View:** `analytics.v_cashflow_volatility_metrics`

Calculates rolling variability measures, including:
- Three-month standard deviation and relative volatility.
- Six-month standard deviation and relative volatility.
- Three-month and six-month observation counts.
- Rolling-window completeness flags.

Relative volatility is calculated by dividing the relevant standard deviation by the absolute mean movement. It is returned as `NULL` when the mean is zero or there are insufficient observations.

## 4. Validation

The four views have been created in PostgreSQL and their core validation checks have been completed.

The latest validation of the volatility view returned:

| Validation | Result |
|---|---:|
| Monthly records | 120 |
| Distinct businesses | 5 |
| Negative volatility values | 0 |
| Negative standard deviations | 0 |
| Invalid complete three-month windows | 0 |
| Invalid complete six-month windows | 0 |

The trend-persistence view was also validated across 120 records, with zero negative streak values and zero mismatches between streak lengths and persistence flags.

The monthly and rolling views passed their previously performed validation checks.

## 5. Interpretation and Limitations

These metrics describe **bank transaction movements**, not verified closing cash balances.

- Negative net bank movement does not necessarily mean a business is insolvent.
- Inflow and outflow patterns require contextual interpretation.
- Volatility measures variability, not risk on their own.
- Data-quality flags should be considered when interpreting results.
- Rolling metrics depend on the number and continuity of observed monthly records.

The metrics layer is intended to support subsequent cash-flow intelligence, forecasting, scenario analysis, and risk-monitoring components.

## 6. Current Status

**Status:** Initial metrics layer implemented and validated.

**Next development:** Continue building the remaining cash-flow metrics required by the wider Orey Analytics Phase 06 system, then integrate relevant metrics with forecasting and downstream intelligence components.