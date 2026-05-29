##############################################################################
# Orey Analytics
# Retail Intelligence System
# Purpose: Revenue Optimization, Inventory Intelligence & Operational Risk
##############################################################################

library(tidyverse)
library(lubridate)
library(forecast)
library(tseries)

setwd("E:/Business/Orey Analytics/Portfolio Building/10-dashboards/data")
retail <- read_csv("retail_intelligence_dataset_clean.csv")

# ===========================================================================
# SECTION 1: DATA PREPARATION
# ===========================================================================

retail$Date <- as.Date(retail$Date)

retail <- retail %>%
  mutate(
    Revenue         = as.numeric(Revenue),
    NetRevenue      = as.numeric(NetRevenue),
    Cost            = as.numeric(Cost),
    Profit          = as.numeric(Profit),
    UnitsSold       = as.numeric(UnitsSold),
    UnitPrice       = as.numeric(UnitPrice),
    DiscountAmount  = as.numeric(DiscountAmount),
    DiscountRate    = as.numeric(DiscountRate),
    ProfitMargin    = as.numeric(ProfitMargin),
    InventoryLevel  = as.numeric(InventoryLevel),
    LeadTimeDays    = as.numeric(LeadTimeDays),
    
    TransactionID    = as.factor(TransactionID),
    StoreID          = as.factor(StoreID),
    StoreLocation    = as.factor(StoreLocation),
    ProductID        = as.factor(ProductID),
    ProductName      = as.factor(ProductName),
    Category         = as.factor(Category),
    SubCategory      = as.factor(SubCategory),
    CustomerSegment  = as.factor(CustomerSegment),
    SalesChannel     = as.factor(SalesChannel),
    SupplierID       = as.factor(SupplierID)
  )

# ===========================================================================
# SECTION 2: MONTHLY AGGREGATION
# ===========================================================================

monthly_data <- retail %>%
  mutate(Month = floor_date(Date, "month")) %>%
  group_by(Month) %>%
  summarise(
    Revenue        = sum(Revenue),
    NetRevenue     = sum(NetRevenue),
    Cost           = sum(Cost),
    Profit         = sum(Profit),
    UnitsSold      = sum(UnitsSold),
    Avg_Margin     = mean(ProfitMargin),
    Avg_Inventory  = mean(InventoryLevel),
    StockOutRate   = mean(StockOutFlag),
    ReturnRate     = mean(ReturnFlag),
    Avg_LeadTime   = mean(LeadTimeDays)
  ) %>%
  arrange(Month)

# ===========================================================================
# SECTION 3: EXPLORATORY RETAIL ANALYSIS
# ===========================================================================

# Revenue Time Series
ts_revenue <- ts(
  monthly_data$Revenue,
  start = c(year(min(monthly_data$Month)), month(min(monthly_data$Month))),
  frequency = 12
)

plot(ts_revenue,
     main = "Monthly Retail Revenue Time Series",
     ylab = "Revenue",
     xlab = "Time")

# 3-Month Moving Average
monthly_data <- monthly_data %>%
  mutate(MA_3 = sapply(seq_along(Revenue), function(i) {
    if (i < 3) NA else mean(Revenue[(i-2):i])
  }))

# Growth Rate
monthly_data <- monthly_data %>%
  mutate(Growth = (Revenue / lag(Revenue)) - 1)

# STL Decomposition
stl_decomp <- stl(ts_revenue, s.window = "periodic")
plot(stl_decomp)

# Weak Seasonal Months
seasonal_component <- stl_decomp$time.series[, "seasonal"]
monthly_seasonal <- tapply(seasonal_component, cycle(ts_revenue), mean)
worst_months <- order(monthly_seasonal)[1:3]

# Stationarity
PP.test(ts_revenue)

# ===========================================================================
# SECTION 4: REVENUE FORECASTING
# ===========================================================================

n <- length(ts_revenue)
test_size <- 3
train_end <- n - test_size

ts_train <- window(ts_revenue, end = time(ts_revenue)[train_end])
ts_test  <- window(ts_revenue, start = time(ts_revenue)[train_end + 1])

model_train <- auto.arima(ts_train, seasonal = TRUE)
fc_test <- forecast(model_train, h = test_size)
acc <- accuracy(fc_test, ts_test)

rolling_errors <- tsCV(
  ts_revenue,
  forecastfunction = function(x, h) {
    forecast(auto.arima(x, seasonal = TRUE), h = h)
  },
  h = 3,
  window = 12
)

rolling_rmse <- sqrt(mean(rolling_errors^2, na.rm = TRUE))
rolling_mae  <- mean(abs(rolling_errors), na.rm = TRUE)

model_full <- auto.arima(ts_revenue, seasonal = TRUE)
forecast_values <- forecast(model_full, h = 6)

plot(forecast_values,
     main = "6-Month Retail Revenue Forecast",
     ylab = "Revenue",
     xlab = "Time")

# ===========================================================================
# SECTION 5: PROFIT FORECASTING
# ===========================================================================

ts_profit <- ts(
  monthly_data$Profit,
  start = c(year(min(monthly_data$Month)), month(min(monthly_data$Month))),
  frequency = 12
)

profit_model <- auto.arima(ts_profit, seasonal = TRUE)
profit_forecast <- forecast(profit_model, h = 6)

# ===========================================================================
# SECTION 6: INVENTORY INTELLIGENCE
# ===========================================================================

monthly_data <- monthly_data %>%
  mutate(
    Inventory_Risk = case_when(
      StockOutRate > 0.10 ~ "Critical",
      StockOutRate > 0.05 ~ "Moderate",
      TRUE ~ "Healthy"
    )
  )

inventory_by_category <- retail %>%
  group_by(Category) %>%
  summarise(
    Avg_Inventory = mean(InventoryLevel),
    StockOutRate  = mean(StockOutFlag),
    Revenue       = sum(Revenue),
    Profit        = sum(Profit)
  ) %>%
  arrange(desc(Revenue))

# ===========================================================================
# SECTION 7: PRODUCT PERFORMANCE
# ===========================================================================

product_performance <- retail %>%
  group_by(ProductName, Category, SubCategory) %>%
  summarise(
    Revenue      = sum(Revenue),
    NetRevenue   = sum(NetRevenue),
    Profit       = sum(Profit),
    UnitsSold    = sum(UnitsSold),
    ReturnRate   = mean(ReturnFlag),
    AvgMargin    = mean(ProfitMargin)
  ) %>%
  arrange(desc(Revenue))

best_products  <- head(product_performance, 10)
worst_products <- tail(product_performance, 10)

# ===========================================================================
# SECTION 8: STORE PERFORMANCE ANALYSIS
# ===========================================================================

store_analysis <- retail %>%
  group_by(StoreID, StoreLocation) %>%
  summarise(
    Revenue       = sum(Revenue),
    Profit        = sum(Profit),
    AvgMargin     = mean(ProfitMargin),
    StockOutRate  = mean(StockOutFlag),
    ReturnRate    = mean(ReturnFlag)
  ) %>%
  mutate(
    Store_Risk = case_when(
      StockOutRate > 0.05 | ReturnRate > 0.09 ~ "High Risk",
      StockOutRate > 0.03 | ReturnRate > 0.07 ~ "Moderate Risk",
      TRUE ~ "Reliable"
    )
  )

# ===========================================================================
# SECTION 9: CUSTOMER SEGMENT ANALYSIS
# ===========================================================================

segment_analysis <- retail %>%
  group_by(CustomerSegment) %>%
  summarise(
    Revenue      = sum(Revenue),
    Profit       = sum(Profit),
    AvgMargin    = mean(ProfitMargin),
    ReturnRate   = mean(ReturnFlag)
  ) %>%
  arrange(desc(Revenue))

# ===========================================================================
# SECTION 10: SALES CHANNEL PERFORMANCE
# ===========================================================================

channel_analysis <- retail %>%
  group_by(SalesChannel) %>%
  summarise(
    Revenue       = sum(Revenue),
    Profit        = sum(Profit),
    AvgMargin     = mean(ProfitMargin),
    ReturnRate    = mean(ReturnFlag)
  ) %>%
  mutate(
    Revenue_Share = Revenue / sum(Revenue)
  )

# ===========================================================================
# SECTION 11: SUPPLIER RISK ANALYSIS
# ===========================================================================

supplier_analysis <- retail %>%
  group_by(SupplierID) %>%
  summarise(
    Avg_LeadTime  = mean(LeadTimeDays),
    StockOutRate  = mean(StockOutFlag),
    Revenue       = sum(Revenue)
  ) %>%
  mutate(
    Supplier_Risk = case_when(
      Avg_LeadTime > 16 | StockOutRate > 0.03 ~ "High Risk",
      Avg_LeadTime > 12 | StockOutRate > 0.02 ~ "Moderate Risk",
      TRUE ~ "Reliable"
    )
  )

# ===========================================================================
# SECTION 12: EXECUTIVE SUMMARY
# ===========================================================================

cat("==========================================================\n")
cat("      OREY ANALYTICS — RETAIL INTELLIGENCE REPORT        \n")
cat("==========================================================\n")
cat("Revenue Forecast MAPE       :", round(acc["Test set", "MAPE"], 2), "%\n")
cat("Rolling RMSE                :", round(rolling_rmse, 2), "\n")
cat("Rolling MAE                 :", round(rolling_mae, 2), "\n")
cat("Weak Sales Months           :", month.name[worst_months], "\n")
cat("Current Inventory Health    :", tail(monthly_data$Inventory_Risk, 1), "\n")
cat("Average Return Rate         :", round(mean(retail$ReturnFlag) * 100, 2), "%\n")
cat("==========================================================\n")

# ===========================================================================
# SECTION 13: POWER BI EXPORTS
# ===========================================================================

output_path <- "E:/Business/Orey Analytics/Portfolio Building/10-dashboards/Retail Intelligence/PowerBI data"
dir.create(output_path, recursive = TRUE, showWarnings = FALSE)

# Dashboard 1: Revenue & Sales Intelligence
write_csv(
  monthly_data,
  file.path(output_path, "Dashboard_1_Monthly_Retail_Overview.csv")
)

write_csv(data.frame(
  Month = seq.Date(
    from = max(monthly_data$Month) %m+% months(1),
    by = "month",
    length.out = 6
  ),
  Revenue_Forecast = as.numeric(forecast_values$mean),
  Lower_95 = as.numeric(forecast_values$lower[,2]),
  Upper_95 = as.numeric(forecast_values$upper[,2])
),
file.path(output_path, "Dashboard_1_Revenue_Forecast.csv"))

write_csv(product_performance,
          file.path(output_path, "Dashboard_1_Product_Performance.csv"))

write_csv(store_analysis,
          file.path(output_path, "Dashboard_1_Store_Performance.csv"))

# Dashboard 2: Inventory, Returns & Operational Risk
write_csv(inventory_by_category,
          file.path(output_path, "Dashboard_2_Inventory_Analysis.csv"))

write_csv(supplier_analysis,
          file.path(output_path, "Dashboard_2_Supplier_Risk.csv"))

write_csv(channel_analysis,
          file.path(output_path, "Dashboard_2_Channel_Analysis.csv"))

write_csv(segment_analysis,
          file.path(output_path, "Dashboard_2_Customer_Segments.csv"))

write_csv(monthly_data %>%
            select(Month, StockOutRate, ReturnRate, Avg_LeadTime, Inventory_Risk),
          file.path(output_path, "Dashboard_2_Operational_Risk.csv"))

