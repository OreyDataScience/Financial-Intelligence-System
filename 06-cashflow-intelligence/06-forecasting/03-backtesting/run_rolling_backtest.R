# ============================================================
# Orey Analytics
# Phase 06 — Cash Flow Intelligence
# Rolling-Origin Forecast Backtesting
#
# Models:
#   1. Naive
#   2. Seasonal naive
#   3. ETS
#   4. ARIMA
#
# Design:
#   Initial training window: 12 months
#   Forecast horizon:        Up to 6 months
#   Source: analytics.v_monthly_cashflow_monitoring
#
# Principles:
#   - Preserve intentional real-world data messiness.
#   - Do not automatically remove or modify observations.
#   - Retain failed model attempts for auditability.
#   - Evaluate forecasts only against unseen observations.
# ============================================================


# ------------------------------------------------------------
# 1. Project paths and packages
# ------------------------------------------------------------

required_packages <- c(
  "DBI",
  "RPostgres",
  "forecast",
  "dplyr",
  "lubridate",
  "readr",
  "rstudioapi"
)

missing_packages <- required_packages[
  !vapply(
    required_packages,
    requireNamespace,
    logical(1),
    quietly = TRUE
  )
]

if (length(missing_packages) > 0L) {
  stop(
    "Install the following packages first: ",
    paste(missing_packages, collapse = ", ")
  )
}

# Assumes the working directory is 06-forecasting.
source(
  "02-model-development/07_forecast_helpers.R"
)

output_dir <- "05-outputs/evaluation"

dir.create(
  output_dir,
  recursive = TRUE,
  showWarnings = FALSE
)


# ------------------------------------------------------------
# 2. Connect to PostgreSQL and load source data
# ------------------------------------------------------------

con <- DBI::dbConnect(
  RPostgres::Postgres(),
  dbname = "orey_cashflow_dev",
  host = "localhost",
  port = 5432,
  user = "postgres",
  password = rstudioapi::askForPassword(
    "PostgreSQL password"
  )
)

# Ensure the connection is closed if this script exits early.
on.exit(
  if (DBI::dbIsValid(con)) {
    DBI::dbDisconnect(con)
  },
  add = TRUE
)

sql <- "
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

data <- DBI::dbGetQuery(con, sql)

DBI::dbDisconnect(con)
con <- NULL

data <- data |>
  dplyr::mutate(
    month_start = as.Date(month_start)
  ) |>
  dplyr::arrange(
    business_id,
    month_start
  )


# ------------------------------------------------------------
# 3. Validate source structure
# ------------------------------------------------------------

targets <- c(
  "total_credit_inflows",
  "total_debit_outflows",
  "net_bank_movement"
)

required_columns <- c(
  "business_id",
  "business_name",
  "currency",
  "month_start",
  targets,
  "investigation_required_count",
  "reversal_count",
  "sign_inconsistency_count"
)

missing_columns <- setdiff(
  required_columns,
  names(data)
)

if (length(missing_columns) > 0L) {
  stop(
    "Missing source columns: ",
    paste(missing_columns, collapse = ", ")
  )
}

if (nrow(data) == 0L) {
  stop("The source query returned no records.")
}

if (anyNA(data$business_id)) {
  stop("Missing business_id values detected.")
}

if (anyDuplicated(data[c("business_id", "month_start")])) {
  stop("Duplicate business-month records detected.")
}

if (anyNA(data$month_start)) {
  stop("Missing month_start values detected.")
}

# Every monthly observation must start on day one.
if (any(lubridate::day(data$month_start) != 1L)) {
  stop(
    "Expected month_start values on the first day of each month."
  )
}

# Check target data types without changing any observations.
for (target_name in targets) {
  if (!is.numeric(data[[target_name]])) {
    stop(
      "Target must be numeric: ",
      target_name
    )
  }
}


# ------------------------------------------------------------
# 4. Backtesting configuration
# ------------------------------------------------------------

initial_window <- 12L
forecast_horizon <- 6L

methods <- c(
  "naive",
  "seasonal_naive",
  "ETS",
  "ARIMA"
)

results <- list()
result_index <- 1L


# ------------------------------------------------------------
# 5. Rolling-origin backtest
# ------------------------------------------------------------

for (business in unique(data$business_id)) {
  
  business_data <- data |>
    dplyr::filter(
      business_id == business
    ) |>
    dplyr::arrange(
      month_start
    )
  
  if (nrow(business_data) < initial_window + 1L) {
    warning(
      "Skipping ", business,
      ": insufficient observations."
    )
    next
  }
  
  # Confirm that the monthly series has no missing months.
  expected_months <- seq.Date(
    from = business_data$month_start[1],
    by = "month",
    length.out = nrow(business_data)
  )
  
  if (!all(expected_months == business_data$month_start)) {
    stop(
      "Non-contiguous monthly observations for ",
      business,
      ". Investigate the data before backtesting."
    )
  }
  
  for (target_name in targets) {
    
    values <- business_data[[target_name]]
    
    # Preserve unusual values, but do not fit models to
    # missing, infinite, or otherwise non-finite observations.
    # Stop and investigate rather than silently dropping rows.
    if (any(!is.finite(values))) {
      stop(
        "Non-finite observations for ",
        business, " / ", target_name,
        ". Investigate; do not silently drop observations."
      )
    }
    
    # Expanding training window.
    # The forecast is evaluated against observations
    # excluded from that origin's training data.
    last_origin <- length(values) - 1L
    
    if (last_origin < initial_window) {
      next
    }
    
    for (origin in seq.int(
      initial_window,
      last_origin
    )) {
      
      actual_horizon <- min(
        forecast_horizon,
        length(values) - origin
      )
      
      training_values <- values[seq_len(origin)]
      
      test_indices <- seq.int(
        origin + 1L,
        origin + actual_horizon
      )
      
      actual_values <- values[test_indices]
      
      origin_date <- business_data$month_start[origin]
      
      forecast_dates <- business_data$month_start[test_indices]
      
      for (method_name in methods) {
        
        # Seasonal naive repeats the latest annual cycle.
        # Twelve observations are the minimum accepted
        # by the shared forecasting helper.
        #
        # With only one annual cycle, seasonal estimates
        # have limited supporting evidence.
        if (
          method_name == "seasonal_naive" &&
          length(training_values) < 12L
        ) {
          next
        }
        
        model_result <- run_forecast_safely(
          y = training_values,
          method = method_name,
          horizon = actual_horizon
        )
        
        # ----------------------------------------------------
        # Record failed model attempts for auditability
        # ----------------------------------------------------
        
        if (model_result$status != "success") {
          
          results[[result_index]] <- data.frame(
            business_id = business,
            target = target_name,
            method = method_name,
            origin_date = origin_date,
            forecast_date = forecast_dates,
            horizon = seq_len(actual_horizon),
            actual_value = actual_values,
            forecast_value = NA_real_,
            error = NA_real_,
            absolute_error = NA_real_,
            squared_error = NA_real_,
            status = "failed",
            error_message = model_result$error_message,
            investigation_required_count =
              business_data$investigation_required_count[
                test_indices
              ],
            reversal_count =
              business_data$reversal_count[
                test_indices
              ],
            sign_inconsistency_count =
              business_data$sign_inconsistency_count[
                test_indices
              ],
            stringsAsFactors = FALSE
          )
          
          result_index <- result_index + 1L
          next
        }
        
        predicted_values <- as.numeric(
          model_result$forecast$mean
        )
        
        # Protect against unexpected forecast lengths.
        if (length(predicted_values) != actual_horizon) {
          
          results[[result_index]] <- data.frame(
            business_id = business,
            target = target_name,
            method = method_name,
            origin_date = origin_date,
            forecast_date = forecast_dates,
            horizon = seq_len(actual_horizon),
            actual_value = actual_values,
            forecast_value = NA_real_,
            error = NA_real_,
            absolute_error = NA_real_,
            squared_error = NA_real_,
            status = "failed",
            error_message =
              "Forecast length did not match requested horizon.",
            investigation_required_count =
              business_data$investigation_required_count[
                test_indices
              ],
            reversal_count =
              business_data$reversal_count[
                test_indices
              ],
            sign_inconsistency_count =
              business_data$sign_inconsistency_count[
                test_indices
              ],
            stringsAsFactors = FALSE
          )
          
          result_index <- result_index + 1L
          next
        }
        
        # A model may return non-finite predictions.
        # Record these as failures rather than treating
        # them as valid forecasts.
        if (any(!is.finite(predicted_values))) {
          
          results[[result_index]] <- data.frame(
            business_id = business,
            target = target_name,
            method = method_name,
            origin_date = origin_date,
            forecast_date = forecast_dates,
            horizon = seq_len(actual_horizon),
            actual_value = actual_values,
            forecast_value = NA_real_,
            error = NA_real_,
            absolute_error = NA_real_,
            squared_error = NA_real_,
            status = "failed",
            error_message =
              "Model returned non-finite forecast values.",
            investigation_required_count =
              business_data$investigation_required_count[
                test_indices
              ],
            reversal_count =
              business_data$reversal_count[
                test_indices
              ],
            sign_inconsistency_count =
              business_data$sign_inconsistency_count[
                test_indices
              ],
            stringsAsFactors = FALSE
          )
          
          result_index <- result_index + 1L
          next
        }
        
        # ----------------------------------------------------
        # Record successful forecasts and errors
        # ----------------------------------------------------
        
        forecast_errors <- actual_values - predicted_values
        
        results[[result_index]] <- data.frame(
          business_id = business,
          target = target_name,
          method = method_name,
          origin_date = origin_date,
          forecast_date = forecast_dates,
          horizon = seq_len(actual_horizon),
          actual_value = actual_values,
          forecast_value = predicted_values,
          error = forecast_errors,
          absolute_error = abs(forecast_errors),
          squared_error = forecast_errors^2,
          status = "success",
          error_message = NA_character_,
          investigation_required_count =
            business_data$investigation_required_count[
              test_indices
            ],
          reversal_count =
            business_data$reversal_count[
              test_indices
            ],
          sign_inconsistency_count =
            business_data$sign_inconsistency_count[
              test_indices
            ],
          stringsAsFactors = FALSE
        )
        
        result_index <- result_index + 1L
      }
    }
  }
}


# ------------------------------------------------------------
# 6. Combine and save results
# ------------------------------------------------------------

if (length(results) == 0L) {
  stop("No backtest results were produced.")
}

backtest_results <- dplyr::bind_rows(results)

output_file <- file.path(
  output_dir,
  "rolling_model_comparison_errors.csv"
)

readr::write_csv(
  backtest_results,
  output_file,
  na = ""
)

# ------------------------------------------------------------
# 7. Report completion
# ------------------------------------------------------------

cat("\nRolling-origin backtest finished.\n")

cat(
  "Rows produced:",
  nrow(backtest_results),
  "\n"
)

cat(
  "Successful forecasts:",
  sum(backtest_results$status == "success"),
  "\n"
)

cat(
  "Failed forecasts:",
  sum(backtest_results$status == "failed"),
  "\n"
)

cat(
  "Methods represented:\n"
)

print(
  backtest_results |>
    dplyr::count(
      method,
      status,
      name = "forecast_records"
    )
)

cat(
  "Output:",
  normalizePath(output_file),
  "\n"
)
