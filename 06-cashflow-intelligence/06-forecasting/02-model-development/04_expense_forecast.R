# ============================================================
# Orey Analytics
# Phase 06 — Debit Outflow Forecast
# ============================================================

library(DBI)
library(RPostgres)

project_dir <- normalizePath(getwd(), winslash = "/", mustWork = TRUE)

source(file.path(
  project_dir, "02-model-development", "07_forecast_helpers.R"
))

output_dir <- file.path(project_dir, "05-outputs", "forecasts")
evaluation_dir <- file.path(project_dir, "05-outputs", "evaluation")

dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(evaluation_dir, recursive = TRUE, showWarnings = FALSE)

target <- "total_debit_outflows"
horizon <- 6L

metrics_file <- file.path(
  evaluation_dir,
  "rolling_model_metrics_by_business_target.csv"
)

if (!file.exists(metrics_file)) {
  stop("Backtest metrics file not found: ", metrics_file)
}

model_metrics <- read.csv(metrics_file, stringsAsFactors = FALSE)

required_metrics <- c("business_id", "target", "method", "MAE")
if (!all(required_metrics %in% names(model_metrics))) {
  stop("The model metrics file is missing required columns.")
}

con <- DBI::dbConnect(
  RPostgres::Postgres(),
  dbname = "orey_cashflow_dev",
  host = "localhost",
  port = 5432,
  user = "postgres",
  password = rstudioapi::askForPassword("PostgreSQL password")
)

monthly_data <- tryCatch(
  DBI::dbGetQuery(con, "
    SELECT business_id, business_name, industry, currency,
           month_start, total_debit_outflows,
           investigation_required_count, reversal_count,
           sign_inconsistency_count
    FROM analytics.v_monthly_cashflow_monitoring
    ORDER BY business_id, month_start;
  "),
  finally = DBI::dbDisconnect(con)
)

if (nrow(monthly_data) == 0) stop("No monthly observations retrieved.")

monthly_data$month_start <- as.Date(monthly_data$month_start)
monthly_data[[target]] <- as.numeric(monthly_data[[target]])

if (anyNA(monthly_data$business_id) ||
    anyNA(monthly_data$month_start)) {
  stop("Missing business IDs or month dates require investigation.")
}

if (anyDuplicated(monthly_data[c("business_id", "month_start")]) > 0) {
  stop("Duplicate business-month records detected.")
}

if (any(!is.finite(monthly_data[[target]]))) {
  stop("Debit outflows contain missing or non-finite values. Do not replace them with zero.")
}

forecast_rows <- list()
selection_rows <- list()
fi <- 1L
si <- 1L

for (id in unique(monthly_data$business_id)) {
  d <- monthly_data[monthly_data$business_id == id, ]
  d <- d[order(d$month_start), ]
  
  if (length(unique(d$currency)) != 1L) {
    stop("Multiple currencies found for business ", id, ".")
  }
  
  expected_months <- seq.Date(
    min(d$month_start), max(d$month_start), by = "month"
  )
  
  if (nrow(d) != length(expected_months) ||
      !all(d$month_start == expected_months)) {
    stop("Missing calendar months detected for business ", id, ".")
  }
  
  if (nrow(d) < 12L) {
    warning("Skipping ", id, ": fewer than 12 observations.")
    next
  }
  
  candidates <- model_metrics[
    model_metrics$business_id == id &
      model_metrics$target == target &
      is.finite(model_metrics$MAE),
  ]
  
  if (nrow(candidates) == 0L) {
    stop("No valid backtest model metrics for ", id, " / ", target, ".")
  }
  
  candidates <- candidates[order(candidates$MAE), ]
  chosen <- candidates[1, ]
  
  result <- run_forecast_safely(
    y = d[[target]],
    method = chosen$method,
    horizon = horizon
  )
  
  if (result$status != "success") {
    stop(
      "Forecast failed for ", id, " using ", chosen$method,
      ": ", result$error_message
    )
  }
  
  f <- extract_forecast_values(
    forecast_result = result,
    business_id = id,
    target = target,
    origin_date = max(d$month_start),
    horizon = horizon
  )
  
  f$business_name <- d$business_name[1]
  f$industry <- d$industry[1]
  f$currency <- d$currency[1]
  f$selected_model_MAE <- chosen$MAE
  f$training_months <- nrow(d)
  f$training_months_with_investigations <- sum(
    d$investigation_required_count > 0, na.rm = TRUE
  )
  f$training_reversal_flags <- if (
    all(is.na(d$reversal_count))
  ) NA_real_ else sum(d$reversal_count, na.rm = TRUE)
  f$training_sign_inconsistency_flags <- if (
    all(is.na(d$sign_inconsistency_count))
  ) NA_real_ else sum(d$sign_inconsistency_count, na.rm = TRUE)
  
  forecast_rows[[fi]] <- f
  fi <- fi + 1L
  
  selection_rows[[si]] <- data.frame(
    business_id = id,
    target = target,
    selected_method = chosen$method,
    backtest_MAE = chosen$MAE,
    backtest_RMSE = if ("RMSE" %in% names(chosen)) chosen$RMSE else NA_real_,
    selection_basis = "Lowest MAE in rolling backtest",
    stringsAsFactors = FALSE
  )
  si <- si + 1L
}

if (length(forecast_rows) == 0L) stop("No forecasts were generated.")

forecasts <- do.call(rbind, forecast_rows)
selections <- do.call(rbind, selection_rows)

write.csv(
  forecasts,
  file.path(output_dir, "04_expense_forecasts.csv"),
  row.names = FALSE
)

write.csv(
  selections,
  file.path(evaluation_dir, "04_expense_model_selection.csv"),
  row.names = FALSE
)

cat("\nDebit-outflow forecasting complete.\n")
cat("Forecast rows:", nrow(forecasts), "\n")
cat("Businesses forecast:", nrow(selections), "\n")
print(selections)
