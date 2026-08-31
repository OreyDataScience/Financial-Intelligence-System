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

# Project Objectives

This project was developed to demonstrate how data science can support:

* Alternative lending decisions
* SME financial risk assessment
* Creditworthiness evaluation
* Applicant-facing explainability and reason codes
* Ongoing model monitoring and population stability tracking
* Fairness and disparate impact screening
* Model governance and recalibration decision-making

Rather than relying solely on historical financial statements, the scoring model incorporates operational behaviour, cash-flow stability, and bureau history to produce a more holistic assessment of business health.

---

# Project Components

## 1. Data Quality Audit

A comprehensive data audit was performed across the core panel, applicant population, and transaction sample before any modelling took place.

The assessment includes:

* Row/column counts, dtypes, and memory profiling
* Missing value detection and missingness percentages
* Duplicate row detection
* Date-range validation
* Target (default event) distribution analysis
* A keyword scan for potential leakage variables

This stage demonstrates the importance of ensuring high-quality, well-understood data before any analytical or predictive modelling takes place.

## 2. Feature Engineering

Financially meaningful SME risk features were engineered from the audited panel, with transaction-level information temporally aligned to each snapshot via an as-of merge.

Feature categories include:

* Cash-flow stability and volatility
* Liquidity and cash buffer
* Debt serviceability (including DSCR)
* Profitability and operating margin
* Balance-sheet leverage
* Operational distress events (bounced payments, reversals)
* Business bureau risk
* Director bureau risk
* Business structure

Business-level train/validation/test splits are also assigned here to prevent entity-level leakage.

## 3. Preprocessing & Leakage Control

Data quality issues identified in the audit were addressed through structured, training-only preprocessing.

Activities included:

* Handling missing values via training-derived medians
* Creating missingness indicators to preserve information about unavailable data
* Removing zero-variance predictors
* Excluding administrative, outcome, and transaction columns from the modelling matrix
* Preparing the final model-ready feature schema

These steps ensure downstream modelling is reliable, reproducible, and free of information leakage from validation/test into training.

## 4. WoE Binning & Information Value

Model-ready predictors were transformed into Weight-of-Evidence (WoE) features, with Information Value (IV) used to assess each predictor's discriminative strength.

* Binning rules and WoE mappings are learned from training data only
* Validation and test data reuse the training-derived bins unchanged
* Numerical variables use quantile-based bins; categorical variables are treated as discrete risk groups
* Unseen validation/test categories receive neutral WoE
* Very high IV values are flagged for leakage investigation

## 5. Feature Selection & Scorecard Modelling

Stable, predictive features were selected and combined into an interpretable logistic regression scorecard.

* Information Value used as the initial predictive filter
* Highly correlated predictors reduced to avoid redundancy
* Logistic regression fit on WoE-transformed training features
* Probability scaled to a 300–850 point **Orey Financial Health Score**
* Model coefficients, selected features, and scoring metadata saved for full auditability

## 6. Model Validation, Calibration & Risk Bands

The fitted scorecard is independently validated — without retraining — on held-out validation and test data.

* Discrimination assessed via AUC, Gini coefficient, and Kolmogorov–Smirnov statistic
* Calibration assessed via Brier score and mean/maximum absolute calibration error
* Empirically-derived risk bands, checked for monotonic default-rate separation
* Validation-to-test stability comparison
* A single `model_validation_pass` flag gates every downstream stage

## 7. Final Scoring & Lending Decision Policy

Validated scores and risk bands are translated into a finished, business-facing product.

* Business identifiers re-attached to the scored population, with integrity checks
* Validated risk bands applied consistently across the full population
* An editable lending-decision policy layered on top (approve / refer / decline, indicative pricing tier) — kept separate from the statistical model
* Portfolio-level risk and segment summaries
* A full model card produced for governance and audit

## 8. Applicant Scoring & Reason Codes

New, unlabelled SME applicants are scored by exactly replaying the fitted pipeline — no refitting of any kind.

* Feature engineering, imputation, and WoE transform replayed using only saved Stage 02–06 artifacts
* Per-applicant reason codes generated directly from the scorecard's own points table
* Top adverse (score-reducing) and protective (score-increasing) factors surfaced per applicant
* Applicant-level risk band and indicative lending decision produced

## 9. Score Monitoring (Population & Characteristic Stability)

The scored applicant population is compared against the training population the model was built on.

* **Score-level PSI** — has the overall score distribution drifted from the model's training baseline?
* **Feature-level CSI** — which individual features are driving that drift, if any?
* Risk-band mix comparison between training and applicant populations

## 10. Fairness & Disparate Impact Review

Lending decisions, scores, and calibration are screened for disparities across business-level segments on out-of-sample, labelled data.

* Adverse Impact Ratio (four-fifths rule heuristic), with statistical significance testing
* Calibration gap review (predicted vs. observed default rate) by segment
* False-decline rate — the direct harm metric — among non-defaulters by segment
* Segments reviewed: province, industry sector, legal entity type, business maturity

## 11. Recalibration & Governance Trigger Policy

The closing stage of the phase. Combines statistical validation, population stability, and fairness signals into a single, auditable governance decision.

* 5-tier escalation policy (Critical / Recalibrate / Escalate / Monitor / No Action)
* Explicit owner and SLA per tier
* Persistent, append-only decision log across monitoring cycles
* Trend check for worsening governance severity across recent runs

---

# The Orey Financial Health Score

A validated Financial Health Score was developed to evaluate the credit risk of each SME applicant.

The model combines 20 selected, WoE-transformed predictors into a single interpretable score ranging from **300–850**, scaled using a base score of 600, base odds of 5.0, and 20 points-to-double-odds (PDO).

The scoring framework incorporates factors such as:

* Cash-flow stability and volatility
* Liquidity and cash buffer adequacy
* Debt service coverage ratio (DSCR)
* Profitability and operating margin
* Balance-sheet leverage
* Operational distress events
* Business and director bureau risk
* Business age and structure

The resulting score provides a decomposable, auditable indication of financial stability and repayment capacity — every point on the score can be traced back to the specific feature that produced it.

---

# Risk Classification

Applicants are classified into five empirically-derived risk bands, validated for monotonic default-rate separation on held-out test data:

| Risk band | Score range | Test default rate |
|---|---|---|
| Very High Risk | ≤ 580 | 46.31% |
| High Risk | 581–606 | 19.35% |
| Moderate Risk | 607–629 | 9.81% |
| Low Risk | 630–657 | 4.65% |
| Very Low Risk | ≥ 658 | 1.26% |

These classifications support rapid interpretation for underwriters, credit analysts, and lending institutions, and feed directly into the lending decision policy.

---

# Lending Decision Support

One of the primary applications of this project is improving lending confidence and speed for alternative credit providers.

The Orey Financial Health Score can support:

* Alternative lenders
* SME finance providers
* Invoice and revenue-based financiers
* Credit committees
* SMEs themselves, seeking to understand and improve their own financial health

Instead of evaluating businesses using only traditional financial statements, lenders gain additional insight into cash-flow behaviour, operational conduct, and bureau history — with a full, auditable trail from raw data to decision.

---

# Validated Model Performance

Results from the completed Stage 06 validation run — actual, validated figures.

**Population:** 207,132 panel observations across 11,500 businesses; 170,726 (82.4%) with an observable 12-month outcome; observed default rate ≈ 16.8%.

**Discrimination**

| Dataset | AUC | Gini | KS |
|---|---|---|---|
| Training | 0.826421 | 0.652842 | 0.495403 |
| Validation | 0.823898 | 0.647796 | 0.490547 |
| Test | 0.825186 | 0.650372 | 0.494691 |

**Calibration**

| Dataset | Brier score | Mean abs. calib. error | Max abs. calib. error |
|---|---|---|---|
| Training | 0.107867 | 0.002104 | 0.004480 |
| Validation | 0.108676 | 0.002336 | 0.007238 |
| Test | 0.107542 | 0.003716 | 0.011474 |

**Stage 06 outcome:** `MODEL VALIDATION STATUS: PASS`

---

# Monitoring & Governance

Stage 09 (PSI/CSI) and Stage 10 (fairness) feed a single 5-tier governance policy in Stage 11:

| Tier | Trigger | Owner | SLA |
|---|---|---|---|
| 0 — Critical | Stage 06 statistical validation fails | Head of Model Risk | 1 business day |
| 1 — Recalibrate | Score PSI ≥ 0.25, or a material *and* statistically significant fairness disparity | Model Risk Committee | 10 business days |
| 2 — Escalate | A material fairness flag without significance, or ≥ 3 features with material CSI shift | Model Risk Analyst | 15 business days |
| 3 — Monitor | Moderate PSI, any material/moderate CSI shift, or a borderline fairness flag | Model Risk Analyst | 30 business days |
| 4 — No Action | Nothing flagged | Model Risk Analyst | — |

PSI/CSI thresholds: `< 0.10` stable · `0.10–0.25` moderate · `≥ 0.25` material.
Adverse Impact Ratio thresholds: `≥ 0.80` no flag · `0.70–0.80` borderline · `< 0.70` material.

---

# Reporting & Documentation

Technical outputs are translated into governance- and stakeholder-ready artifacts throughout the pipeline:

* **Model card** (`orey_financial_health_model_card.json`) — full model documentation for governance and audit
* **Applicant reason codes** (`applicant_reason_codes.csv`) — top adverse/protective factors per applicant, for underwriter and applicant-facing explanations
* **Governance decision log** (`governance_decision_log.csv`) — persistent, append-only audit trail of every monitoring cycle's outcome
* **Full-phase methodology document** — a formal reference covering all 11 stages, validated performance, governance thresholds, and documented limitations

---

# Technologies Used

* Python
* pandas, numpy
* scikit-learn (`LogisticRegression`, `SimpleImputer`, `VarianceThreshold`)
* Weight-of-Evidence / Information Value credit scoring methodology
* JSON/CSV artifact contracts between pipeline stages

---

# Known Limitations

* **Fairness screening uses proxy segments, not protected characteristics.** The dataset has no owner/director demographic attributes — Stage 10 uses province, industry sector, legal entity type, and business maturity as the best available proxies. The four-fifths rule is a US EEOC heuristic, not a South African legal standard; any flag should be reviewed against PEPUDA and the National Credit Act with qualified counsel.
* **`default_flag_bureau_history` required manual verification** before acceptance as a model feature, due to its name matching Stage 01's leakage-keyword scanner. Verified as legitimate; its exact timing definition should still be confirmed against the bureau data dictionary.
* **Training-set statistics are reconstructed, not persisted.** Stage 03's imputation medians are fit on training data but not saved as standalone artifacts — Stages 08 and 09 rebuild them by replaying Stage 03's logic, requiring any future change there to be mirrored in both.
* **Reason codes are a linear decomposition, not a causal explanation** — they show how the fitted scorecard arrived at a score, not what would happen if a single feature changed in isolation.

---

# Business Value

This project demonstrates the ability to move beyond descriptive reporting by developing a practical, production-grade credit intelligence system.

The combined scoring, monitoring, and governance framework provides organisations with:

* Faster, more consistent, and explainable lending decisions
* Early identification of financially vulnerable SMEs
* An auditable trail from raw data to every individual decision
* Ongoing population stability and fairness monitoring, not just a one-time model build
* A governance layer that turns monitoring signals into accountable, owned actions

---

## Orey Analytics

**Cash Flow Intelligence for SMEs**

Helping businesses and financial institutions predict risk, improve financial visibility, and make smarter data-driven decisions through advanced analytics.

**Author:** Oreneile Katlego

