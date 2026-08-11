# Orey Analytics - Dashboards & Retail Intelligence System

## 1. Project Overview

The **Retail Intelligence System** is an end-to-end business intelligence and analytics project developed by **Orey Analytics** to demonstrate how transactional retail data can be transformed into actionable business intelligence and management decision support.

The project began as a statistical and analytical system developed in **R**, and was subsequently transformed into a multi-page interactive web application using **Python, Dash and Plotly**.

The system moves beyond descriptive reporting by combining:

- Financial performance analysis
- Revenue intelligence
- Revenue and profit forecasting
- Profitability analysis
- Product performance
- Store performance
- Inventory intelligence
- Supplier risk analysis
- Customer segmentation
- Sales channel analysis
- Operational risk monitoring
- SKU-level reorder decisions
- Executive-level business intelligence
- Prescriptive recommendations

The final system demonstrates the complete analytical workflow:

> **Raw Retail Data → Data Preparation → Statistical Analysis → Forecasting → Risk Analysis → Business Intelligence → Prescriptive Analytics → Executive Decision Support → Interactive Web Application**

---

## 2. Business Objective

The objective of the Retail Intelligence System is to help a retail business understand its financial and operational performance while identifying risks, forecasting future outcomes and supporting management decision-making.

The system is designed to answer questions relating to:

- Financial performance
- Revenue and profit trends
- Future revenue and profit outlook
- Product performance
- Store performance
- Inventory and stock-out risk
- Supplier risk
- Customer segments
- Sales channels
- Operational risk
- Management attention areas
- Recommended business actions

---

## 3. Retail Intelligence System in R (Phase 1)

The first version of the Retail Intelligence System was developed in **R**.

The R system formed the analytical foundation of the project and was responsible for the underlying statistical analysis, forecasting, business intelligence calculations and prescriptive analytics.

### Core R Technologies

- R
- tidyverse
- dplyr
- lubridate
- forecast
- tseries
- ggplot2
- Statistical time-series analysis

The retail transaction dataset was cleaned, transformed and aggregated into monthly business performance metrics before being used for further analysis.

### Time-Series Analysis

The revenue time series was analysed using:

- Monthly revenue time series
- Moving averages
- Growth analysis
- STL decomposition
- Seasonal analysis
- Stationarity testing

### Forecasting

Seasonal ARIMA models were used to forecast future **revenue and profit**.

The system generated:

- 3-month validation forecasts
- 6-month forward forecasts
- Upper and lower 95% confidence intervals

This allowed future revenue and profit trajectories to be evaluated alongside forecast uncertainty.

### Model Evaluation

Forecast performance was evaluated using:

- MAPE
- Rolling RMSE
- Rolling MAE
- Walk-forward validation

### Exploratory Analysis

The analytical system also included:

- Store performance analysis
- Product performance analysis
- Inventory intelligence
- Supplier intelligence
- Customer segment analysis
- Sales channel analysis
- Operational risk analysis

### Extensions

The system was extended beyond descriptive and predictive analytics through the development of:

- A SKU-level reorder decision engine
- Inventory risk classification
- Supplier risk classification
- Store risk classification
- Prescriptive management actions
- A management attention framework

The management attention framework identifies areas requiring follow-up and links each issue to the relevant dashboard page.

---

## 4. Executive Intelligence Extraction

After completing the core Retail Intelligence System, additional R scripts were developed to extract executive-level information from the analytical outputs.

The executive extraction layer produced datasets covering:

- Business overview
- Forecast summary
- Operational risk
- Inventory summary
- Supplier summary
- Sales channels
- Customer segments
- Top products
- Bottom products
- Top stores
- High-risk stores
- High-risk suppliers
- Category performance
- Seasonal risk
- Strategic findings
- Recommended actions
- Needs attention
- SKU reorder decisions

An **executive report was also generated as a PDF**, providing a consolidated management-level view of the retail intelligence findings.

---

## 5. Dashboard Development

Following the analytical R system, the project was transformed into an interactive web-based dashboard application.

The web application was developed using:

- VS Code
- Python
- Dash
- Plotly
- Dash Bootstrap Components
- Pandas
- HTML
- CSS

The application consumes the analytical outputs produced by the Retail Intelligence System and presents them through interactive business intelligence dashboards.

### Final Application Contains Multiple Intelligence Layers

- Executive Dashboard
- Revenue Intelligence
- Product Performance
- Store Performance
- Inventory Intelligence
- Supplier Risk
- Channel Analysis
- Customer Segment Intelligence
- Operational Risk

The **Executive Dashboard** consolidates financial performance, forecast outlook, strategic findings, management attention areas and recommended actions into a single management-facing interface.

---

## 6. Technology Stack

### Data & Statistical Analysis

- R
- tidyverse
- dplyr
- lubridate
- forecast
- tseries
- ggplot2

### Data Processing

- Python
- Pandas

### Forecasting & Statistical Modelling

- ARIMA
- Seasonal ARIMA
- STL decomposition
- Walk-forward validation
- MAPE
- RMSE
- MAE
- Confidence intervals

### Dashboard Development

- Python
- Dash
- Plotly
- Dash Bootstrap Components
- HTML
- CSS

### Business Intelligence

- Power BI-ready CSV exports
- Executive reporting
- KPI development
- Risk scoring
- Prescriptive analytics
- Decision-support dashboards
- Interactive data visualisation

### Development Tools

- Visual Studio Code
- Git
- GitHub
- GitHub Codespaces

---

## 7. Orey Analytics Perspective

This project represents the development philosophy behind **Orey Analytics**:

> **Data should not simply describe a business. It should help the business make better decisions.**

The Retail Intelligence System therefore combines:

**Statistics + Data Science + Financial Analysis + Forecasting + Risk Intelligence + Business Intelligence + Prescriptive Analytics**

into a single decision-support workflow.

The progression of the system can be summarised as:

> **What happened? → Why did it happen? → What is likely to happen? → What should management do?**

### Future Development

Potential future improvements include:

- Automated data ingestion
- SQL-based data storage
- Cloud deployment
- Automated dashboard refresh
- Real-time KPI monitoring
- Advanced forecasting models
- Machine-learning forecasting
- Automated anomaly detection
- More advanced inventory optimisation
- Supplier performance scoring
- Customer lifetime value analysis
- Scenario analysis
- What-if modelling
- Automated executive reporting
- Role-based dashboards
- API integration
- Production-grade authentication
- Data quality monitoring
- Automated alerts

---

## 8. Project Status

**Status:** Completed analytical prototype and interactive dashboard system.

The project has progressed from an **R-based statistical and forecasting system** into a **multi-page interactive business intelligence application**.

The completed system includes:

- Retail Intelligence System
- Revenue Intelligence
- Revenue & Profit Forecasting
- Product Performance
- Store Performance
- Inventory Intelligence
- Supplier Risk
- Customer Segment Intelligence
- Channel Analysis
- Operational Risk
- Executive Dashboard
- Strategic Findings
- Management Attention Framework
- Recommended Actions
- SKU Reorder Decision Engine
- Executive Reporting

---

## 9. Conclusion

The Retail Intelligence System demonstrates an end-to-end analytics workflow capable of transforming raw retail transaction data into executive-level business intelligence.

The project combines:

- Statistical analysis
- Data science
- Financial intelligence
- Forecasting
- Risk analysis
- Business intelligence
- Prescriptive analytics
- Interactive dashboard development

within
