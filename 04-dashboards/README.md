# Orey Analytics - Dashboards & Retail Intelligence System

## 1. Project overview
The Retail Intelligence System is an end-to-end business intelligence and analytics project developed by **Orey Analytics** to demonstrate how transactional retail data can be transformed into actionable business intelligence.

The project began as a statistical and analytical system developed in **R**, and was subsequently transformed into a multi-page interactive web application using **Python, Dash and Plotly**.

The system is designed to move beyond descriptive reporting by combining: Financial performance analysis, Revenue intelligence, Revenue forecasting, Profitability analysis, Product performance, Store performance, Inventory intelligence, Supplier risk analysis, Customer segmentation, Sales channel analysis, Operational risk monitoring, SKU-level reorder decisions, Executive-level business intelligence and Prescriptive recommendations.

The final system demonstrates the complete analytical workflow:

> **Raw Retail Data → Data Preparation → Statistical Analysis → Forecasting → Risk Analysis → Business Intelligence → Prescriptive Analytics → Executive Decision Support → Interactive Web Application**

---

## 2. Business Objective
The objective of the Retail Intelligence System is to help a retail business answer questions about financial performance, revenue intelligence, product intelligence, supplier intelligence, store performance, operational risk, and executive decision support.

---

## 3. Retail Intelligence System in R (Phase 1)
The first version of the Retail Intelligence System was developed in R. This was responsible for the underlying statistical analysis, forecasting, business intelligence calculations and prescriptive analytics.
### Core R Technologies: 
- R
- tidyverse
- lubridate
- forecast
- tseries
- dplyr
- ggplot2
- statistical time-series analysis

The retail transaction dataset was cleaned and transformed before analysis then aggregated into monthly business performance metrics. Revenue was modelled as a monthly time series.

### Time-Series Analysis:
Monthly revenue time series, Moving averages, Growth analysis, STL decomposition, Seasonal analysis and Stationarity testing.

### Forecasting:
Seasonal ARIMA models were used to forecast future revenue & profit.
- The system generated: 3-month validation forecasts, 6-month forward forecasts and Upper/Lower 95% confidence intervals

### Model Evaluation
Forecast performance was evaluated using: 
- MAPE, Rolling RMSE, Rolling MAE and Walk-forward validation

This allowed the dashboard to communicate not only the expected revenue/profit trajectory but also forecast uncertainty.

### Exploratory Analysis
Store performance, product perfromance, inventory intelligence, Supplier intelligence, customer segment intelligence, channel analysis and operational risk.

### Extensions 
The creation of SKU-level reorder decision engine, prescriptive analytics (recommended management actions). A amanegement attenton framework was developed ro identify areas requiring immediate follow-up . Each issue is connected to the relevant dashboard page.

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
- An executive report was also generated as a PDF.

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
- HTML/CSS

The application consumes the analytical outputs produced by the Retail Intelligence System.

### Final application contains multiple intelligence layers:
- Executive Dashboard
- Revenue Intelligence
- Product Performance
- Store Performance
- Inventory Intelligence
- Supplier Risk
- Channel Analysis
- Customer Segment Intelligence
- Operational Risk

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

### Forecasting
- ARIMA
- Seasonal ARIMA
- STL decomposition
- Walk-forward validation
- MAPE
- RMSE
- MAE
- Confidence intervals

### Dashboard Development
-- Python
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

### Development Tools
Visual Studio Code
Git
GitHub
GitHub Codespaces

---

## 7. Orey Analytics Perspective
This project represents the development philosophy behind Orey Analytics:
- Data should not simply describe a business. It should help the business make better decisions.

### The Retail Intelligence System therefore combines:
Statistics + Data Science + Financial Analysis + Forecasting + Risk Intelligence + Business Intelligence + Prescriptive Analytics
into a single decision-support workflow.

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
Status: Completed analytical prototype and interactive dashboard system.
The project has progressed from an R-based statistical analysis into a multi-page interactive business intelligence application.

## 9. Conclusion
The Retail Intelligence System demonstrates an end-to-end analytics workflow capable of transforming raw retail transaction data into executive-level business intelligence.
The project combines statistical analysis, forecasting, financial intelligence, operational risk analysis and prescriptive decision support within an interactive dashboard environment. It also forms an important foundation for the broader Orey Analytics product and portfolio.
