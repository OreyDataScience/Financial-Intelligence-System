##############################################################################
# Orey Analytics
# Data Quality Assessment Report
# Purpose: Validate dataset integrity before analysis
##############################################################################

library(tidyverse)
library(readr)

#===========================================================================
# OUTPUT DIRECTORY
#===========================================================================

output_path <- "E:/Business/Orey Analytics/Portfolio Building/07-scoring-engine/Outputs"
dir.create(output_path, recursive = TRUE, showWarnings = FALSE)

#===========================================================================
# BASIC DATASET INFORMATION
#===========================================================================

total_rows <- nrow(service)
total_columns <- ncol(service)

#===========================================================================
# MISSING VALUES
#===========================================================================

#Inspecting Missing values found in region
service %>%
  filter(is.na(Region))

service$Region <- replace_na(service$Region, "Unknown")

missing_summary <- data.frame(
  Variable = names(service),
  Missing_Values = colSums(is.na(service)),
  Missing_Percentage = round(colSums(is.na(service))/total_rows*100,2)
)

write_csv(
  missing_summary,
  file.path(output_path,"Missing_Value_Report.csv")
)

#===========================================================================
# BLANK CHARACTER VALUES
#===========================================================================

blank_summary <- service %>%
  summarise(
    across(
      where(is.character),
      ~sum(trimws(.)=="")
    )
  ) %>%
  pivot_longer(
    everything(),
    names_to="Variable",
    values_to="Blank_Values"
  )

write_csv(
  blank_summary,
  file.path(output_path,"Blank_Value_Report.csv")
)

#===========================================================================
# DUPLICATE RECORDS
#===========================================================================

duplicate_rows <- service %>%
  filter(duplicated(.))

write_csv(
  duplicate_rows,
  file.path(output_path,"Duplicate_Records.csv")
)

duplicate_summary <- data.frame(
  Total_Duplicates = nrow(duplicate_rows)
)

write_csv(
  duplicate_summary,
  file.path(output_path,"Duplicate_Summary.csv")
)

#===========================================================================
# DATA TYPES
#===========================================================================

data_types <- data.frame(
  
  Variable = names(service),
  
  Data_Type = sapply(service,class)
  
)

write_csv(
  data_types,
  file.path(output_path,"Data_Types.csv")
)

#===========================================================================
# NUMERIC SUMMARY
#===========================================================================

numeric_summary <- service %>%
  summarise(
    across(
      where(is.numeric),
      list(
        Mean=mean,
        Median=median,
        SD=sd,
        Min=min,
        Max=max
      ),
      na.rm=TRUE
    )
  ) %>%
  pivot_longer(
    everything(),
    names_to="Statistic",
    values_to="Value"
  )

write_csv(
  numeric_summary,
  file.path(output_path,"Numeric_Summary.csv")
)

#===========================================================================
# OUTLIER REPORT (IQR METHOD)
#===========================================================================

numeric_cols <- names(service)[sapply(service,is.numeric)]

outlier_report <- map_df(numeric_cols,function(col){
  
  x <- service[[col]]
  
  Q1 <- quantile(x,.25,na.rm=TRUE)
  
  Q3 <- quantile(x,.75,na.rm=TRUE)
  
  IQR_Value <- IQR(x,na.rm=TRUE)
  
  Lower <- Q1-1.5*IQR_Value
  
  Upper <- Q3+1.5*IQR_Value
  
  data.frame(
    
    Variable=col,
    
    Outliers=sum(x<Lower | x>Upper,na.rm=TRUE),
    
    Outlier_Percentage=round(
      sum(x<Lower | x>Upper,na.rm=TRUE)/total_rows*100,
      2
    )
    
  )
  
})

write_csv(
  outlier_report,
  file.path(output_path,"Outlier_Report.csv")
)

#===========================================================================
# OVERALL DATA QUALITY SCORE
#===========================================================================

missing_pct <- sum(is.na(service))/(total_rows*total_columns)

duplicate_pct <- nrow(duplicate_rows)/total_rows

blank_pct <- sum(blank_summary$Blank_Values)/(total_rows*max(1,nrow(blank_summary)))

quality_score <- round(
  
  100-
    (
      missing_pct*100+
        duplicate_pct*100+
        blank_pct*100
    ),
  
  2)

quality_score <- max(0,quality_score)

quality_summary <- data.frame(
  
  Metric=c(
    "Rows",
    "Columns",
    "Missing Cells",
    "Duplicate Rows",
    "Blank Values",
    "Overall Data Quality Score"
  ),
  
  Value=c(
    total_rows,
    total_columns,
    sum(is.na(service)),
    nrow(duplicate_rows),
    sum(blank_summary$Blank_Values),
    paste0(quality_score,"%")
  )
  
)

write_csv(
  quality_summary,
  file.path(output_path,"Data_Quality_Summary.csv")
)

##############################################################################