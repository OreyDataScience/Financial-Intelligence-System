# OREY ANALYTICS
# Phase 06 — Cash Flow Intelligence
# 00 — Exploratory Statistical Analysis
#
# Purpose:
#   Establish a statistically transparent understanding of
#   monthly SME cash movements before forecasting.
#
# Data source:
#   PostgreSQL: analytics.v_monthly_cashflow_monitoring
#
# Principles:
#   1. Preserve the source data.
#   2. Never silently replace missing values with zero.
#   3. Analyse each SME separately before pooling results.
#   4. Distinguish observed evidence from statistical inference.

# ============================================================
# 1. PACKAGES
# ============================================================

library(DBI)
library(RPostgres)

# ============================================================
# 2. PROJECT PATHS
# ============================================================

project_dir <- normalizePath(
  getwd(),
  winslash = "/",
  mustWork = TRUE
)

output_root <- file.path(
  project_dir,
  "05-outputs"
)

diagnostics_dir <- file.path(
  output_root,
  "diagnostics"
)

evaluation_dir <- file.path(
  output_root,
  "evaluation"
)

dir.create(
  diagnostics_dir,
  recursive = TRUE,
  showWarnings = FALSE
)

dir.create(
  evaluation_dir,
  recursive = TRUE,
  showWarnings = FALSE
)

# ============================================================
# 3. DATABASE CONNECTION
# ============================================================

con <- dbConnect(
  RPostgres::Postgres(),
  dbname = "orey_cashflow_dev",
  host = "localhost",
  port = 5432,
  user = "postgres",
  password = rstudioapi::askForPassword(
    "PostgreSQL password"
  )
)

# ============================================================
# 4. RETRIEVE MONTHLY DATA
# ============================================================

monthly_data <- dbGetQuery(
  con,
  "
  SELECT
      business_id,
      business_name,
      industry,
      currency,
      month_start,
      transaction_count,
      total_credit_inflows,
      total_debit_outflows,
      net_bank_movement,
      investigation_required_count,
      reversal_count,
      sign_inconsistency_count
  FROM analytics.v_monthly_cashflow_monitoring
  ORDER BY business_id, month_start;
  "
)

# Close the connection after retrieval.
dbDisconnect(con)

# ============================================================
# 5. INITIAL DATA VALIDATION
# ============================================================

required_columns <- c(
  "business_id",
  "business_name",
  "industry",
  "currency",
  "month_start",
  "transaction_count",
  "total_credit_inflows",
  "total_debit_outflows",
  "net_bank_movement",
  "investigation_required_count",
  "reversal_count",
  "sign_inconsistency_count"
)

missing_columns <- setdiff(
  required_columns,
  names(monthly_data)
)

if (length(missing_columns) > 0) {
  stop(
    "Required columns are missing: ",
    paste(missing_columns, collapse = ", ")
  )
}

if (nrow(monthly_data) == 0) {
  stop("The database returned no monthly observations.")
}

monthly_data$month_start <- as.Date(
  monthly_data$month_start
)

targets <- c(
  "total_credit_inflows",
  "total_debit_outflows",
  "net_bank_movement"
)

for (target in targets) {
  monthly_data[[target]] <- as.numeric(
    monthly_data[[target]]
  )
}

if (anyNA(monthly_data$business_id) ||
    anyNA(monthly_data$month_start)) {
  stop("Business identifiers or month dates contain missing values.")
}

if (anyDuplicated(
  monthly_data[c("business_id", "month_start")]
) > 0) {
  stop("Duplicate business-month observations detected.")
}

if (any(!is.finite(
  as.matrix(monthly_data[targets])
))) {
  stop("At least one target contains missing or non-finite values.")
}

# ============================================================
# 6. INITIAL DATASET PROFILE
# ============================================================

dataset_profile <- data.frame(
  metric = c(
    "Total observations",
    "Unique businesses",
    "Unique industries",
    "First observation month",
    "Last observation month",
    "Unique currencies"
  ),
  value = c(
    nrow(monthly_data),
    length(unique(monthly_data$business_id)),
    length(unique(monthly_data$industry)),
    as.character(min(monthly_data$month_start)),
    as.character(max(monthly_data$month_start)),
    length(unique(monthly_data$currency))
  )
)

write.csv(
  dataset_profile,
  file.path(
    diagnostics_dir,
    "exploratory_dataset_profile.csv"
  ),
  row.names = FALSE
)

# ============================================================
# 7. DESCRIPTIVE STATISTICS FUNCTION
# ============================================================

calculate_descriptive_statistics <- function(x) {

  x <- x[is.finite(x)]

  if (length(x) == 0) {
    return(data.frame(
      n = 0,
      mean = NA_real_,
      median = NA_real_,
      standard_deviation = NA_real_,
      variance = NA_real_,
      minimum = NA_real_,
      q1 = NA_real_,
      q3 = NA_real_,
      maximum = NA_real_,
      coefficient_of_variation = NA_real_
    ))
  }

  x_mean <- mean(x)
  x_sd <- if (length(x) >= 2) sd(x) else NA_real_

  data.frame(
    n = length(x),
    mean = x_mean,
    median = median(x),
    standard_deviation = x_sd,
    variance = if (length(x) >= 2) var(x) else NA_real_,
    minimum = min(x),
    q1 = unname(quantile(x, 0.25)),
    q3 = unname(quantile(x, 0.75)),
    maximum = max(x),
    coefficient_of_variation = if (
      length(x) >= 2 &&
      is.finite(x_sd) &&
      x_mean != 0
    ) x_sd / abs(x_mean) else NA_real_
  )
}

# ============================================================
# 8. BUSINESS-LEVEL DESCRIPTIVE STATISTICS
# ============================================================

business_ids <- unique(monthly_data$business_id)

descriptive_results <- list()
result_index <- 1

for (id in business_ids) {

  business_data <- monthly_data[
    monthly_data$business_id == id,
  ]

  for (target in targets) {

    stats <- calculate_descriptive_statistics(
      business_data[[target]]
    )

    descriptive_results[[result_index]] <- data.frame(
      business_id = id,
      business_name = business_data$business_name[1],
      target = target,
      stats
    )

    result_index <- result_index + 1
  }
}

descriptive_statistics <- do.call(
  rbind,
  descriptive_results
)

write.csv(
  descriptive_statistics,
  file.path(
    evaluation_dir,
    "exploratory_descriptive_statistics.csv"
  ),
  row.names = FALSE
)

# ============================================================
# 9. DATA-QUALITY SUMMARY
# ============================================================

quality_results <- list()

for (id in business_ids) {

  business_data <- monthly_data[
    monthly_data$business_id == id,
  ]

  quality_results[[id]] <- data.frame(
    business_id = id,
    business_name = business_data$business_name[1],
    observations = nrow(business_data),
    months_with_investigations = sum(
      business_data$investigation_required_count > 0,
      na.rm = TRUE
    ),
    total_investigation_flags = sum(
      business_data$investigation_required_count,
      na.rm = TRUE
    ),
    total_reversals = sum(
      business_data$reversal_count,
      na.rm = TRUE
    ),
    total_sign_inconsistencies = sum(
      business_data$sign_inconsistency_count,
      na.rm = TRUE
    ),
    missing_inflows = sum(
      is.na(business_data$total_credit_inflows)
    ),
    missing_outflows = sum(
      is.na(business_data$total_debit_outflows)
    ),
    missing_net_movement = sum(
      is.na(business_data$net_bank_movement)
    )
  )
}

quality_summary <- do.call(
  rbind,
  quality_results
)

write.csv(
  quality_summary,
  file.path(
    diagnostics_dir,
    "exploratory_data_quality_summary.csv"
  ),
  row.names = FALSE
)
