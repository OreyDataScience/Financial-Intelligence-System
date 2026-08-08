from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent

DATA = BASE_DIR / "data" / "retail-intelligence"

monthly = pd.read_csv(DATA / "Dashboard_1_Monthly_Retail_Overview.csv")
forecast = pd.read_csv(DATA / "Dashboard_1_Revenue_Forecast.csv")
products = pd.read_csv(DATA / "Dashboard_1_Product_Performance.csv")
stores = pd.read_csv(DATA / "Dashboard_1_Store_Performance.csv")

inventory = pd.read_csv(DATA / "Dashboard_2_Inventory_Analysis.csv")
suppliers = pd.read_csv(DATA / "Dashboard_2_Supplier_Risk.csv")
channels = pd.read_csv(DATA / "Dashboard_2_Channel_Analysis.csv")
segments = pd.read_csv(DATA / "Dashboard_2_Customer_Segments.csv")
operational = pd.read_csv(DATA / "Dashboard_2_Operational_Risk.csv")