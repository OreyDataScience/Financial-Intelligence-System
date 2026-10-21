# ============================================================
# Orey Analytics
# Phase 06 — Cash Flow Intelligence
# Forecast Evaluation Metrics
#
# Purpose:
#   1. Evaluate rolling-origin forecast accuracy.
#   2. Compare models on equivalent forecast cases.
#   3. Report metrics by SME, target, and horizon.
#   4. Preserve operational investigation flags.
#
# Input:
#   05-outputs/evaluation/
#     rolling_model_comparison_errors.csv
#
# Outputs:
#   05-outputs/evaluation/
#     rolling_model_metrics_by_business_target.csv
#     rolling_model_metrics_by_horizon.csv
#     rolling_model_metrics_overall.csv
#     rolling_model_comparison_quality.csv
#
# Principles:
#   - Do not alter source observations.
#   - Do not silently remove unusual cashflow values.
#   - Compare models using matching forecast cases.
#   - Treat MAPE cautiously when actual values are zero
#     or negative.
# ============================================================

# ------------------------------------------------------------
# 1. Packages and paths
# ------------------------------------------------------------

required_packages <- c(
  "dplyr",
  "readr"
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

input_file <- file.path(
  "05-outputs",
  "evaluation",
  "rolling_model_comparison_errors.csv"
)

output_dir <- file.path(
  "05-outputs",
  "evaluation"
)

if (!file.exists(input_file)) {
  stop(
    "Backtest input file not found: ",
    input_file,
    "\nRun run_rolling_backtest.R first."
  )
}

# ------------------------------------------------------------
# 2. Load backtest results
# ------------------------------------------------------------

backtest <- readr::read_csv(
  input_file,
  show_col_types = FALSE
)

if (nrow(backtest) == 0L) {
  stop("The backtest file contains no records.")
}

required_columns <- c(
  "business_id",
  "target",
  "method",
  "origin_date",
  "forecast_date",
  "horizon",
  "actual_value",
  "forecast_value",
  "error",
  "absolute_error",
  "squared_error",
  "status",
  "error_message",
  "investigation_required_count",
  "reversal_count",
  "sign_inconsistency_count"
)

missing_columns <- setdiff(
  required_columns,
  names(backtest)
)

if (length(missing_columns) > 0L) {
  stop(
    "Missing columns in backtest results: ",
    paste(missing_columns, collapse = ", ")
  )
}

expected_methods <- c(
  "naive",
  "seasonal_naive",
  "ETS",
  "ARIMA"
)

unexpected_methods <- setdiff(
  unique(backtest$method),
  expected_methods
)

if (length(unexpected_methods) > 0L) {
  stop(
    "Unexpected forecasting methods: ",
    paste(unexpected_methods, collapse = ", ")
  )
}

if (anyNA(backtest$business_id) ||
    anyNA(backtest$target) ||
    anyNA(backtest$method) ||
    anyNA(backtest$status)) {
  stop(
    "Missing business, target, method, or status values detected."
  )
}

if (!all(backtest$status %in% c("success", "failed"))) {
  stop("Unexpected forecast status values detected.")
}

# Parse dates explicitly for consistent grouping.
backtest <- backtest |>
  dplyr::mutate(
    origin_date = as.Date(origin_date),
    forecast_date = as.Date(forecast_date)
  )

if (anyNA(backtest$origin_date) ||
    anyNA(backtest$forecast_date)) {
  stop("Invalid origin_date or forecast_date values detected.")
}

# ------------------------------------------------------------
# 3. Validate forecast errors
# ------------------------------------------------------------

successful <- backtest |>
  dplyr::filter(status == "success")

failed <- backtest |>
  dplyr::filter(status == "failed")

if (nrow(successful) == 0L) {
  stop("No successful forecasts are available for evaluation.")
}

numeric_columns <- c(
  "actual_value",
  "forecast_value",
  "error",
  "absolute_error",
  "squared_error",
  "horizon"
)

for (column_name in numeric_columns) {
  if (!is.numeric(backtest[[column_name]])) {
    stop(
      "Expected numeric column: ",
      column_name
    )
  }
}

if (any(!is.finite(successful$actual_value)) ||
    any(!is.finite(successful$forecast_value)) ||
    any(!is.finite(successful$error))) {
  stop(
    "Successful records contain non-finite values. ",
    "Investigate before calculating metrics."
  )
}

# Verify the saved errors instead of trusting them blindly.
calculated_error <-
  successful$actual_value - successful$forecast_value

if (!isTRUE(all.equal(
  successful$error,
  calculated_error,
  tolerance = 1e-8,
  check.attributes = FALSE
))) {
  stop("Saved error values do not match actual minus forecast.")
}

if (any(successful$horizon < 1L) ||
    any(successful$horizon != as.integer(successful$horizon))) {
  stop("Invalid forecast horizon values detected.")
}

# Recalculate absolute and squared errors from validated values.
# This does not change the source actuals or forecasts.
successful <- successful |>
  dplyr::mutate(
    error = actual_value - forecast_value,
    absolute_error = abs(error),
    squared_error = error^2,
    actual_is_zero = actual_value == 0,
    actual_is_negative = actual_value < 0,
    actual_is_nonpositive = actual_value <= 0,
    absolute_actual = abs(actual_value)
  )


# ------------------------------------------------------------
# 4. Check duplicate forecast cases
# ------------------------------------------------------------

case_columns <- c(
  "business_id",
  "target",
  "method",
  "origin_date",
  "forecast_date",
  "horizon"
)

if (anyDuplicated(successful[case_columns])) {
  stop(
    "Duplicate successful forecast cases detected. ",
    "Investigate before calculating metrics."
  )
}


# ------------------------------------------------------------
# 5. Identify comparable cases across all four models
# ------------------------------------------------------------

# A case is defined by SME, target, origin, forecast date,
# and horizon. It is comparable only when all four methods
# have a successful forecast for that exact case.

case_keys <- successful |>
  dplyr::distinct(
    business_id,
    target,
    origin_date,
    forecast_date,
    horizon,
    method
  )

case_coverage <- case_keys |>
  dplyr::group_by(
    business_id,
    target,
    origin_date,
    forecast_date,
    horizon
  ) |>
  dplyr::summarise(
    methods_available = dplyr::n_distinct(method),
    .groups = "drop"
  )

comparable_cases <- case_coverage |>
  dplyr::filter(
    methods_available == length(expected_methods)
  ) |>
  dplyr::select(
    business_id,
    target,
    origin_date,
    forecast_date,
    horizon
  )

comparable_results <- successful |>
  dplyr::inner_join(
    comparable_cases,
    by = c(
      "business_id",
      "target",
      "origin_date",
      "forecast_date",
      "horizon"
    )
  )

if (nrow(comparable_results) == 0L) {
  stop(
    "No equivalent successful forecast cases exist ",
    "across all four methods."
  )
}

# All four methods must have the same actual value for
# a given case. This detects mismatched evaluation inputs.
actual_consistency <- comparable_results |>
  dplyr::group_by(
    business_id,
    target,
    origin_date,
    forecast_date,
    horizon
  ) |>
  dplyr::summarise(
    distinct_actuals = dplyr::n_distinct(actual_value),
    .groups = "drop"
  )

if (any(actual_consistency$distinct_actuals != 1L)) {
  stop(
    "Actual values differ across models for the same case."
  )
}


# ------------------------------------------------------------
# 6. Define metric calculation
# ------------------------------------------------------------

calculate_metrics <- function(data) {
  
  data |>
    dplyr::summarise(
      n_forecasts = dplyr::n(),
      
      MAE = mean(
        absolute_error
      ),
      
      RMSE = sqrt(
        mean(squared_error)
      ),
      
      mean_error_bias = mean(
        error
      ),
      
      mean_actual = mean(
        actual_value
      ),
      
      zero_actual_count = sum(
        actual_is_zero
      ),
      
      negative_actual_count = sum(
        actual_is_negative
      ),
      
      nonpositive_actual_count = sum(
        actual_is_nonpositive
      ),
      
      # MAPE is reported only for positive actuals.
      # This restriction is explicitly disclosed because
      # excluding zero/negative values changes its scope.
      positive_actual_count = sum(
        actual_value > 0
      ),
      
      MAPE_positive_actuals_pct = {
        positive_rows <- actual_value > 0
        
        if (any(positive_rows)) {
          mean(
            abs(
              error[positive_rows] /
                actual_value[positive_rows]
            )
          ) * 100
        } else {
          NA_real_
        }
      },
      
      # MAE divided by mean absolute actual value.
      # This avoids division by zero at individual rows,
      # but is still undefined if every actual is zero.
      WAPE_pct = {
        denominator <- sum(abs(actual_value))
        
        if (denominator > 0) {
          sum(absolute_error) /
            denominator * 100
        } else {
          NA_real_
        }
      },
      
      .groups = "drop"
    )
}


# ------------------------------------------------------------
# 7. Metrics by SME, target, and method
# ------------------------------------------------------------

metrics_by_business_target <- comparable_results |>
  dplyr::group_by(
    business_id,
    target,
    method
  ) |>
  calculate_metrics() |>
  dplyr::arrange(
    business_id,
    target,
    MAE
  )

readr::write_csv(
  metrics_by_business_target,
  file.path(
    output_dir,
    "rolling_model_metrics_by_business_target.csv"
  ),
  na = ""
)


# ------------------------------------------------------------
# 8. Metrics by SME, target, horizon, and method
# ------------------------------------------------------------

metrics_by_horizon <- comparable_results |>
  dplyr::group_by(
    business_id,
    target,
    horizon,
    method
  ) |>
  calculate_metrics() |>
  dplyr::arrange(
    business_id,
    target,
    horizon,
    MAE
  )

readr::write_csv(
  metrics_by_horizon,
  file.path(
    output_dir,
    "rolling_model_metrics_by_horizon.csv"
  ),
  na = ""
)


# ------------------------------------------------------------
# 9. Overall metrics by target and method
# ------------------------------------------------------------

metrics_overall <- comparable_results |>
  dplyr::group_by(
    target,
    method
  ) |>
  calculate_metrics() |>
  dplyr::arrange(
    target,
    MAE
  )

readr::write_csv(
  metrics_overall,
  file.path(
    output_dir,
    "rolling_model_metrics_overall.csv"
  ),
  na = ""
)


# ------------------------------------------------------------
# 10. Backtest coverage and quality report
# ------------------------------------------------------------

coverage_by_method <- backtest |>
  dplyr::group_by(
    method,
    status
  ) |>
  dplyr::summarise(
    forecast_records = dplyr::n(),
    .groups = "drop"
  )

comparable_counts <- comparable_results |>
  dplyr::group_by(
    method
  ) |>
  dplyr::summarise(
    comparable_forecasts = dplyr::n(),
    .groups = "drop"
  )

flag_summary <- comparable_results |>
  dplyr::group_by(
    method
  ) |>
  dplyr::summarise(
    comparable_forecasts = dplyr::n(),
    
    forecasts_with_investigations = sum(
      investigation_required_count > 0,
      na.rm = TRUE
    ),
    
    forecasts_with_reversals = sum(
      reversal_count > 0,
      na.rm = TRUE
    ),
    
    forecasts_with_sign_inconsistencies = sum(
      sign_inconsistency_count > 0,
      na.rm = TRUE
    ),
    
    .groups = "drop"
  )

readr::write_csv(
  coverage_by_method,
  file.path(
    output_dir,
    "rolling_model_comparison_quality.csv"
  ),
  na = ""
)


# ------------------------------------------------------------
# 11. Print evaluation summary
# ------------------------------------------------------------

cat("\n============================================\n")
cat("Orey Analytics — Forecast Evaluation\n")
cat("============================================\n")

cat("\nInput records:", nrow(backtest), "\n")
cat("Successful source records:", nrow(successful), "\n")
cat("Failed source records:", nrow(failed), "\n")

cat(
  "Comparable cases:",
  nrow(comparable_cases),
  "\n"
)

cat(
  "Comparable forecast records:",
  nrow(comparable_results),
  "\n"
)

cat("\nRecord coverage by method and status:\n")
print(coverage_by_method)

cat("\nComparable forecast counts by method:\n")
print(comparable_counts)

cat("\nOverall metrics by target and method:\n")
print(metrics_overall)

cat("\nMetrics by SME and target:\n")
print(metrics_by_business_target)

cat("\nOperational flag summary:\n")
print(flag_summary)

cat("\nFiles saved in:\n")
cat(normalizePath(output_dir), "\n")

cat("\nMAPE note:\n")
cat(
  "MAPE_positive_actuals_pct uses only cases with positive ",
  "actual values. Zero and negative actuals are counted separately.\n",
  sep = ""
)

cat(
  "WAPE_pct uses absolute actual values in its denominator.\n"
)

cat(
  "Bias convention: actual minus forecast. ",
  "Positive bias indicates underforecasting on average; ",
  "negative bias indicates overforecasting.\n",
  sep = ""
)

cat("\nEvaluation script finished.\n")
