from pathlib import Path
import pandas as pd

# BASE DIRECTORIES

BASE_DIR = Path(__file__).resolve().parent.parent

DATA = BASE_DIR / "data" / "retail-intelligence"

# CORE DASHBOARD DATA

monthly = pd.read_csv(
    DATA / "Dashboard_1_Monthly_Retail_Overview.csv"
)

forecast = pd.read_csv(
    DATA / "Dashboard_1_Revenue_Forecast.csv"
)

products = pd.read_csv(
    DATA / "Dashboard_1_Product_Performance.csv"
)

stores = pd.read_csv(
    DATA / "Dashboard_1_Store_Performance.csv"
)

inventory = pd.read_csv(
    DATA / "Dashboard_2_Inventory_Analysis.csv"
)

suppliers = pd.read_csv(
    DATA / "Dashboard_2_Supplier_Risk.csv"
)

channels = pd.read_csv(
    DATA / "Dashboard_2_Channel_Analysis.csv"
)

segments = pd.read_csv(
    DATA / "Dashboard_2_Customer_Segments.csv"
)

operational = pd.read_csv(
    DATA / "Dashboard_2_Operational_Risk.csv"
)

# EXECUTIVE INTELLIGENCE DATA

business_overview = pd.read_csv(
    DATA / "Executive_Business_overview.csv"
)

forecast_summary = pd.read_csv(
    DATA / "Executive_Forecast_Summary.csv"
)

operational_summary = pd.read_csv(
    DATA / "Executive_Operational_Risk_Summary.csv"
)

inventory_summary = pd.read_csv(
    DATA / "Executive_Inventory_Summary.csv"
)

supplier_summary = pd.read_csv(
    DATA / "Executive_Supplier_Summary.csv"
)

sales_channels = pd.read_csv(
    DATA / "Executive_Sales_Channels.csv"
)

customer_segments = pd.read_csv(
    DATA / "Executive_Customer_Segments.csv"
)

top_products = pd.read_csv(
    DATA / "Executive_Top_Products.csv"
)

top_stores = pd.read_csv(
    DATA / "Executive_Top_Stores.csv"
)

bottom_products = pd.read_csv(
    DATA / "Executive_Bottom_Products.csv"
)

high_risk_stores = pd.read_csv(
    DATA / "Executive_high_risk_Stores.csv"
)

high_risk_suppliers = pd.read_csv(
    DATA / "Executive_high_risk_Suppliers.csv"
)

category_summary = pd.read_csv(
    DATA / "Executive_Category_Summary.csv"
)

seasonal_risk = pd.read_csv(
    DATA / "Executive_Seasonal_Risk.csv"
)

strategic_findings = pd.read_csv(
    DATA / "Executive_Strategic_Findings.csv"
)

recommended_actions = pd.read_csv(
    DATA / "Executive_Recommended_Actions.csv"
)

needs_attention = pd.read_csv(
    DATA / "Executive_Needs_Attention.csv"
)

sku_reorder_decisions = pd.read_csv(
    DATA / "Executive_SKU_Reorder_Decisions.csv"
)