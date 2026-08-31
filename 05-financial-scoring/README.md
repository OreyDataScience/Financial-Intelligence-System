# Financial Health Scoring

**Orey Analytics — Cash Flow Intelligence for SMEs**

An interpretable, end-to-end SME credit risk scoring system: from raw transactional and bureau data to a validated, monitored, and governed lending decision engine. Built for two audiences ... SMEs seeking to understand their own financial health, and alternative lenders seeking faster, more consistent, and more explainable credit decisions.

---

## Overview

This phase takes raw SME financial panel data, bank transactions, and applicant records, and turns them into:

- A validated **Weight-of-Evidence (WoE) logistic regression scorecard** predicting 12-month SME default risk
- A **300–850 point score** (the *Orey Financial Health Score*) with five empirically-derived risk bands
- Per-applicant **reason codes** explaining exactly what drove each score
- An **indicative lending decision** (approve / refer / decline) and pricing tier for each applicant
- Ongoing **population stability monitoring** (PSI/CSI) and a **fairness/disparate impact screen**
- A single **governance decision layer** that turns all of the above into an auditable escalation policy

The architecture deliberately favours interpretability over raw predictive power: every score decomposes into per-feature point contributions, every risk band is derived from validation performance rather than chosen by hand, and every stage reads and writes fixed, inspectable artifacts on disk rather than hidden state.

---

## Repository Structure

---

# Project Objectives

This project was developed to demonstrate how data science can support:

* Alternative lending decisions
* SME financial risk assessment
* Creditworthiness evaluation
* Early warning systems
* Executive financial reporting
* Data quality governance

Rather than relying solely on historical financial statements, the scoring model incorporates operational behaviour and commercial performance to produce a more holistic assessment of business health.

---

# Project Components

## 1. Data Quality Assessment

A comprehensive data quality framework was developed to evaluate the reliability of the source dataset before modelling.

The assessment includes:

* Missing value detection
* Duplicate detection
* Blank value identification
* Invalid value checks
* Data completeness
* Consistency evaluation
* Overall Data Quality Score

The project demonstrates the importance of ensuring high-quality data before any analytical or predictive modelling takes place.

---

## 2. Data Cleaning

Where required, data quality issues were addressed through structured preprocessing.

Cleaning activities included:

* Handling missing values
* Standardising variable types
* Correcting inconsistent records
* Preparing analytical features
* Creating model-ready datasets

These steps ensure that downstream analyses are reliable and reproducible.

---

## 3. Financial Health Scoring Model

A proprietary Financial Health Score was developed to evaluate the financial strength of each client.

The model combines multiple business performance indicators into a single score ranging from **0–100**.

The scoring framework incorporates factors such as:

* Profitability
* Profit Margin
* Monthly Recurring Revenue (MRR)
* Client Retention
* Churn Risk
* Client Tenure
* Payment Behaviour
* Customer Satisfaction
* Upselling Activity

The resulting score provides an overall indication of financial stability and repayment capacity.

---

## 4. Financial Risk Classification

Clients are classified into risk categories based on their Financial Health Score.

Typical classifications include:

* Excellent
* Good
* Moderate
* High Risk
* Critical

These classifications support rapid interpretation for executives, credit analysts and lending institutions.

---

## 5. Lending Decision Support

One of the primary applications of this project is improving lending confidence.

The Financial Health Score can support:

* Alternative lenders
* SME finance providers
* Banks
* Venture debt providers
* Credit committees

Instead of evaluating businesses using only traditional financial statements, lenders gain additional insight into operational performance, customer retention and future sustainability.

---

## Dashboards

Interactive Power BI dashboards for:

### Financial Health Dashboard

Featuring:

* Average Financial Health Score
* Risk distribution
* Client segmentation
* High-risk client monitoring
* Financial trend analysis

### Data Quality Dashboard

Featuring:

* Overall Quality Score
* Missing value analysis
* Completeness metrics
* Duplicate monitoring
* Data governance KPIs

These dashboards demonstrate how technical analysis can be translated into executive-ready decision support tools.

---

# Technologies Used

* R
* tidyverse
* dplyr
* readr
* lubridate
* Power BI
* GitHub

---

# Business Value

This project demonstrates the ability to move beyond descriptive reporting by developing practical financial intelligence solutions that improve decision-making.

The combined data quality framework and Financial Health Score provide organisations with:

* Improved confidence in analytical outputs
* Early identification of financially vulnerable clients
* Better credit and lending decisions
* Enhanced portfolio monitoring
* Data-driven financial risk management

---

## Orey Analytics

**Cash Flow Intelligence for SMEs**

Helping businesses and financial institutions predict risk, improve financial visibility and make smarter data-driven decisions through advanced analytics.

