##############################################################################
# Orey Analytics
# Financial Health Score (FHS)
##############################################################################

library(tidyverse)
library(scales)

setwd("E:/Business/Orey Analytics/Portfolio Building/07-scoring-engine/Data")
service <- read_csv("service_business_dataset_clean.csv")

#=============================================================================
# NORMALISING FUNCTIONS
#=============================================================================
scale_positive <- function(x){
  rescale(x, to = c(0,100))
}

scale_negative <- function(x){
  100 - rescale(x, to = c(0,100))
}

#===========================================================================
# CREATING SUB SCORES
#===========================================================================
service <- service %>%
  mutate(
    Profitability_Score =
      scale_positive(ProfitMargin),
    
    Revenue_Score =
      scale_positive(Revenue),
    
    Cashflow_Score =
      scale_positive(MRR),
    
    Payment_Score =
      scale_negative(PaymentDelayDays),
    
    Customer_Score =
      scale_positive(
        RetentionFlag*100 -
          ChurnRiskScore*100
      ),
    
    Operational_Score =
      scale_positive(SatisfactionScore),
    
    Forecast_Score =
      scale_positive(ClientTenureMonths),
    
    Risk_Score =
      scale_negative(ChurnRiskScore)
  )

#===========================================================================
# FINAL WEIGHTED SCORE
#===========================================================================
service <- service %>%
  mutate(
    FinancialHealthScore =
      
      Profitability_Score * 0.20 +
      
      Cashflow_Score * 0.20 +
      
      Revenue_Score * 0.15 +
      
      Payment_Score * 0.10 +
      
      Customer_Score * 0.10 +
      
      Operational_Score * 0.10 +
      
      Forecast_Score * 0.10 +
      
      Risk_Score * 0.05
  )

#===========================================================================
# RATINGS
#===========================================================================
service <- service %>%
  mutate(
    Rating = case_when(
      FinancialHealthScore >= 90 ~ "Excellent",
      
      FinancialHealthScore >= 80 ~ "Strong",
      
      FinancialHealthScore >= 70 ~ "Healthy",
      
      FinancialHealthScore >= 60 ~ "Watchlist",
      
      FinancialHealthScore >= 50 ~ "Weak",
      
      TRUE ~ "Critical"
    )
  )

#===========================================================================
# LENDING RECOMMENDATION
#===========================================================================
service <- service %>%
  mutate(
    LendingRecommendation = case_when(
      Rating=="Excellent" ~
        "Approve",
      
      Rating=="Strong" ~
        "Approve",
      
      Rating=="Healthy" ~
        "Approve with Monitoring",
      
      Rating=="Watchlist" ~
        "Conditional Approval",
      
      Rating=="Weak" ~
        "Additional Security Required",
      
      TRUE ~
        "Decline"
    
  )
)

#===========================================================================
# CHECKING
#===========================================================================
colSums(is.na(service))

service %>%
  filter(
    if_any(
      where(is.character),
      ~ . == ""
    )
  )

#===========================================================================
# EXPORT
#===========================================================================
write_csv(service, "Financial_Health_Score.csv")

##############################################################################