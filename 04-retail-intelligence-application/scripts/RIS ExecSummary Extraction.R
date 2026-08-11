##############################################################################
# Orey Analytics
# Retail Intelligence Executive Summary Extraction Script
# Purpose: Extract board-level KPIs, risks, forecasts, and strategic insights
##############################################################################

library(tidyverse)
library(lubridate)
library(readr)

# ===========================================================================
# SECTION 1: OUTPUT DIRECTORY
# ===========================================================================

output_path <- "E:/Business/Orey Analytics/Portfolio Building/10-dashboards/Retail Intelligence/Executive Summary data"
dir.create(output_path, showWarnings = FALSE)

# ===========================================================================
# SECTION 2: BUSINESS OVERVIEW KPIs
# ===========================================================================

business_overview <- data.frame(
  Metric = c(
    "Total Revenue",
    "Total Net Revenue",
    "Total Profit",
    "Average Profit Margin",
    "Average Monthly Revenue",
    "Average Monthly Profit",
    "Revenue Growth Rate",
    "Average Return Rate",
    "Average Stockout Rate",
    "Average Supplier Lead Time"
  ),
  Value = c(
    sum(retail$Revenue),
    sum(retail$NetRevenue),
    sum(retail$Profit),
    mean(retail$ProfitMargin) * 100,
    mean(monthly_data$Revenue),
    mean(monthly_data$Profit),
    ((last(monthly_data$Revenue) / first(monthly_data$Revenue)) - 1) * 100,
    mean(retail$ReturnFlag) * 100,
    mean(retail$StockOutFlag) * 100,
    mean(retail$LeadTimeDays)
  )
)

write_csv(
  business_overview,
  file.path(output_path, "Executive_Business_overview.csv")
)

# ===========================================================================
# SECTION 3: FORECAST SUMMARY
# ===========================================================================

forecast_summary <- data.frame(
  Metric = c(
    "Revenue Forecast Next 6 Months",
    "Profit Forecast Next 6 Months",
    "Forecast MAPE",
    "Rolling RMSE",
    "Rolling MAE"
  ),
  Value = c(
    sum(as.numeric(forecast_values$mean)),
    sum(as.numeric(profit_forecast$mean)),
    round(acc["Test set", "MAPE"], 2),
    round(rolling_rmse, 2),
    round(rolling_mae, 2)
  )
)

write_csv(
  forecast_summary,
  file.path(output_path, "Executive_Forecast_Summary.csv")
)

# ===========================================================================
# SECTION 4: PRODUCT PERFORMANCE EXTRACTION
# ===========================================================================

top_products <- product_performance %>%
  arrange(desc(Revenue)) %>%
  head(10)

bottom_products <- product_performance %>%
  arrange(Revenue) %>%
  head(10)

write_csv(
  top_products,
  file.path(output_path, "Executive_Top_Products.csv")
)

write_csv(
  bottom_products,
  file.path(output_path, "Executive_Bottom_Products.csv")
)

# Category Summary
category_summary <- retail %>%
  group_by(Category) %>%
  summarise(
    Revenue      = sum(Revenue),
    Profit       = sum(Profit),
    Avg_Margin   = mean(ProfitMargin),
    ReturnRate   = mean(ReturnFlag),
    StockOutRate = mean(StockOutFlag)
  ) %>%
  arrange(desc(Revenue))

write_csv(
  category_summary,
  file.path(output_path, "Executive_Category_Summary.csv")
)

# ===========================================================================
# SECTION 5: STORE PERFORMANCE EXTRACTION
# ===========================================================================

top_stores <- store_analysis %>%
  arrange(desc(Revenue)) %>%
  head(10)

risk_stores <- store_analysis %>%
  filter(Store_Risk == "High Risk")

write_csv(
  top_stores,
  file.path(output_path, "Executive_Top_Stores.csv")
)

write_csv(
  risk_stores,
  file.path(output_path, "Executive_high_risk_Stores.csv")
)

# ===========================================================================
# SECTION 6: INVENTORY & OPERATIONAL RISK
# ===========================================================================

inventory_summary <- inventory_by_category %>%
  mutate(
    Inventory_Risk = case_when(
      StockOutRate > 0.10 ~ "Critical",
      StockOutRate > 0.05 ~ "Moderate",
      TRUE ~ "Healthy"
    )
  )

write_csv(
  inventory_summary,
  file.path(output_path, "Executive_Inventory_Summary.csv")
)

operational_risk_summary <- monthly_data %>%
  summarise(
    Avg_StockOutRate = mean(StockOutRate),
    Avg_ReturnRate   = mean(ReturnRate),
    Avg_LeadTime     = mean(Avg_LeadTime)
  )

write_csv(
  operational_risk_summary,
  file.path(output_path, "Executive_Operational_Risk_Summary.csv")
)

# ===========================================================================
# SECTION 7: SUPPLIER RISK EXTRACTION
# ===========================================================================

high_risk_suppliers <- supplier_analysis %>%
  filter(Supplier_Risk == "High Risk")

write_csv(
  supplier_analysis,
  file.path(output_path, "Executive_Supplier_Summary.csv")
)

write_csv(
  high_risk_suppliers,
  file.path(output_path, "Executive_high_risk_Suppliers.csv")
)

# ===========================================================================
# SECTION 8: CUSTOMER SEGMENT & CHANNEL PERFORMANCE
# ===========================================================================

write_csv(
  segment_analysis,
  file.path(output_path, "Executive_Customer_Segments.csv")
)

write_csv(
  channel_analysis,
  file.path(output_path, "Executive_Sales_Channels.csv")
)

# ===========================================================================
# SECTION 9: SEASONAL RISK
# ===========================================================================

seasonal_risk <- data.frame(
  Month_Number = worst_months,
  Month_Name = month.name[worst_months],
  Seasonal_Effect = round(monthly_seasonal[worst_months], 2),
  Strategic_Risk = "Weak Sales Period"
)

write_csv(
  seasonal_risk,
  file.path(output_path, "Executive_Seasonal_Risk.csv")
)

# ===========================================================================
# SECTION 10: STRATEGIC FINDINGS SUMMARY
# ===========================================================================

strategic_findings <- data.frame(
  Strategic_Area = c(
    "Revenue Growth",
    "Profitability",
    "Inventory Health",
    "Returns",
    "Supplier Reliability",
    "Seasonality",
    "Store Risk",
    "Category Opportunity"
  ),
  Insight = c(
    ifelse(((last(monthly_data$Revenue) / first(monthly_data$Revenue)) - 1) > 0,
           "Positive revenue growth trajectory",
           "Revenue contraction detected"),
    
    ifelse(mean(retail$ProfitMargin) > 0.30,
           "Strong margin profile",
           "Margin pressure present"),
    
    ifelse(mean(retail$StockOutFlag) < 0.05,
           "Healthy inventory availability",
           "Elevated stockout exposure"),
    
    ifelse(mean(retail$ReturnFlag) < 0.08,
           "Returns under control",
           "Returns impacting profitability"),
    
    ifelse(mean(retail$LeadTimeDays) < 15,
           "Supplier network efficient",
           "Supplier delays increasing operational risk"),
    
    paste("Weak months:", paste(month.name[worst_months], collapse = ", ")),
    
    paste(nrow(risk_stores), "stores flagged high risk"),
    
    paste(category_summary$Category[1], "drives strongest category revenue")
  )
)

write_csv(
  strategic_findings,
  file.path(output_path, "Executive_Strategic_Findings.csv")
)

# ===========================================================================
# SECTION 11: EXECUTIVE SUMMARY CONSOLE REPORT
# ===========================================================================

cat("\n")
cat("==========================================================\n")
cat("      OREY ANALYTICS — RETAIL EXECUTIVE SUMMARY          \n")
cat("==========================================================\n")
cat("Total Revenue                :", round(sum(retail$Revenue), 2), "\n")
cat("Total Net Revenue            :", round(sum(retail$NetRevenue), 2), "\n")
cat("Total Profit                 :", round(sum(retail$Profit), 2), "\n")
cat("Average Profit Margin        :", round(mean(retail$ProfitMargin) * 100, 2), "%\n")
cat("Revenue Growth Rate          :", round(((last(monthly_data$Revenue) / first(monthly_data$Revenue)) - 1) * 100, 2), "%\n")
cat("Forecast Accuracy (MAPE)     :", round(acc["Test set", "MAPE"], 2), "%\n")
cat("Rolling RMSE                 :", round(rolling_rmse, 2), "\n")
cat("Average Return Rate          :", round(mean(retail$ReturnFlag) * 100, 2), "%\n")
cat("Average Stockout Rate        :", round(mean(retail$StockOutFlag) * 100, 2), "%\n")
cat("Weak Sales Months            :", paste(month.name[worst_months], collapse = ", "), "\n")
cat("Top Revenue Category         :", as.character(category_summary$Category[1]), "\n")
cat("High Risk Suppliers          :", nrow(high_risk_suppliers), "\n")
cat("High Risk Stores             :", nrow(risk_stores), "\n")
cat("==========================================================\n")

##############################################################################
# END OF EXECUTIVE SUMMARY EXTRACTION SCRIPT
##############################################################################