# OREY ANALYTICS
# Phase 06 — Cash Flow Intelligence
# 02 — Monthly Baseline Forecasting
#
# Purpose:
#   Establish and evaluate simple benchmark forecasts before
#   developing more complex statistical forecasting models.
#
# Methods:
#   1. Naive: repeat the latest observed value.
#   2. Seasonal naive: repeat the value from 12 months earlier.
#
# Evaluation:
#   Rolling-origin backtesting with a 12-month initial window
#   and a maximum six-month forecast horizon.
#
# Principles:
#   - Never use future observations to train a forecast.
#   - Preserve deliberately messy observations.
#   - Do not silently replace missing financial values with zero.
#   - Keep each business and currency separate.
#   - Carry data-quality information into forecast outputs.
#   - Baseline performance is a benchmark, not proof of
#     production readiness.

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

evaluation_dir <- file.path(
  output_root,
  "evaluation"
)

forecasts_dir <- file.path(
  output_root,
  "forecasts"
)

dir.create(
  evaluation_dir,
  recursive = TRUE,
  showWarnings = FALSE
)

dir.create(
  forecasts_dir,
  recursive = TRUE,
  showWarnings = FALSE
)

# ============================================================
# 3. SETTINGS
# ============================================================

initial_window <- 12L
forecast_horizon <- 6L

targets <- c(
  "total_credit_inflows",
  "total_debit_outflows",
  "net_bank_movement"
)

methods <- c(
  "naive",
  "seasonal_naive"
)

# ============================================================
# 4. RETRIEVE MONTHLY DATA
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

monthly_data <- tryCatch(
  dbGetQuery(
    con,
    "
    SELECT
        business_id,
        business_name,
        industry,
        currency,
        month_start,
        total_credit_inflows,
        total_debit_outflows,
        net_bank_movement,
        investigation_required_count,
        reversal_count,
        sign_inconsistency_count
    FROM analytics.v_monthly_cashflow_monitoring
    ORDER BY business_id, month_start;
    "
  ),
  finally = dbDisconnect(con)
)

# ============================================================
# 5. VALIDATE INPUT DATA
# ============================================================

if (nrow(monthly_data) == 0) {
  stop("No monthly observations were retrieved.")
}

required_columns <- c(
  "business_id",
  "business_name",
  "industry",
  "currency",
  "month_start",
  targets,
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
    "Missing required columns: ",
    paste(missing_columns, collapse = ", ")
  )
}

monthly_data$month_start <- as.Date(
  monthly_data$month_start
)

for (target in targets) {
  monthly_data[[target]] <- as.numeric(
    monthly_data[[target]]
  )
}

if (anyNA(monthly_data$business_id) ||
    anyNA(monthly_data$month_start)) {
  stop("Business IDs or month dates contain missing values.")
}

if (anyDuplicated(
  monthly_data[c("business_id", "month_start")]
) > 0) {
  stop("Duplicate business-month rows detected.")
}

if (any(!is.finite(
  as.matrix(monthly_data[targets])
))) {
  stop(
    "Financial targets contain missing or non-finite values. ",
    "Investigate the source rather than replacing them with zero."
  )
}

# ============================================================
# 6. PREPARE RESULT CONTAINERS
# ============================================================

business_ids <- unique(monthly_data$business_id)

backtest_results <- list()
forecast_results <- list()

backtest_index <- 1L
forecast_index <- 1L

# ============================================================
# 7. PROCESS EACH BUSINESS SEPARATELY
# ============================================================

for (id in business_ids) {

  business_data <- monthly_data[
    monthly_data$business_id == id,
  ]

  business_data <- business_data[
    order(business_data$month_start),
  ]

  business_name <- business_data$business_name[1]
  currency <- business_data$currency[1]
  n <- nrow(business_data)

  if (length(unique(business_data$currency)) != 1L) {
    stop(
      "Multiple currencies found for business ",
      id,
      ". Separate currencies before forecasting."
    )
  }

  if (n < initial_window + forecast_horizon) {
    warning(
      "Skipping ", id,
      ": insufficient observations for the configured ",
      "backtest window and forecast horizon."
    )
    next
  }

  # Confirm there is one observation for every calendar month.
  expected_months <- seq.Date(
    from = min(business_data$month_start),
    to = max(business_data$month_start),
    by = "month"
  )

  if (length(expected_months) != n ||
      !all(business_data$month_start == expected_months)) {
    stop(
      "Monthly gaps detected for ", id,
      ". Investigate missing months before forecasting. ",
      "Do not automatically interpret absent months as zero."
    )
  }

  # ----------------------------------------------------------
  # 7A. ROLLING-ORIGIN BACKTEST
  # ----------------------------------------------------------
  #
  # Each origin uses only observations available at that time.
  # For 24 observations, the initial window is 12 months.
  # Origins advance one month at a time while leaving enough
  # actual future observations for the six-month evaluation.
  #
  # This produces several historical forecast tests rather
  # than relying on one train/test split.

  for (target in targets) {

    values <- business_data[[target]]

    for (origin in seq.int(
      initial_window,
      n - forecast_horizon
    )) {

      training_values <- values[seq_len(origin)]

      actual_months <- business_data$month_start[
        origin + seq_len(forecast_horizon)
      ]

      actual_values <- values[
        origin + seq_len(forecast_horizon)
      ]

      # Scale used for MASE. It is calculated from training
      # observations only, avoiding information leakage.
      scale_value <- mean(
        abs(diff(training_values))
      )

      for (method in methods) {

        if (method == "naive") {

          predictions <- rep(
            tail(training_values, 1),
            forecast_horizon
          )

        } else if (method == "seasonal_naive") {

          # Each forecast uses the value from 12 months earlier.
          seasonal_indices <- (
            origin + seq_len(forecast_horizon) - 12L
          )

          predictions <- values[seasonal_indices]
        }

        errors <- actual_values - predictions

        scaled_errors <- if (
          is.finite(scale_value) &&
          scale_value > 0
        ) {
          abs(errors) / scale_value
        } else {
          rep(NA_real_, length(errors))
        }

        backtest_results[[backtest_index]] <- data.frame(
          business_id = id,
          business_name = business_name,
          currency = currency,
          target = target,
          method = method,
          training_end_month =
            business_data$month_start[origin],
          forecast_month = actual_months,
          horizon_month = seq_len(forecast_horizon),
          actual_value = actual_values,
          forecast_value = predictions,
          error = errors,
          absolute_error = abs(errors),
          squared_error = errors^2,
          scaled_absolute_error = scaled_errors
        )

        backtest_index <- backtest_index + 1L
      }
    }

    # --------------------------------------------------------
    # 7B. FORECAST THE NEXT SIX MONTHS
    # --------------------------------------------------------

    future_months <- seq.Date(
      from = max(business_data$month_start),
      by = "month",
      length.out = forecast_horizon + 1L
    )[-1]

    latest_value <- tail(values, 1)

    future_quality <- data.frame(
      training_months = n,
      training_months_with_investigations = sum(
        business_data$investigation_required_count > 0,
        na.rm = TRUE
      ),
      missing_investigation_flag_months = sum(
        is.na(business_data$investigation_required_count)
      ),
      training_reversal_flags = if (
        all(is.na(business_data$reversal_count))
      ) NA_real_ else sum(
        business_data$reversal_count,
        na.rm = TRUE
      ),
      training_sign_inconsistency_flags = if (
        all(is.na(business_data$sign_inconsistency_count))
      ) NA_real_ else sum(
        business_data$sign_inconsistency_count,
        na.rm = TRUE
      )
    )

    for (method in methods) {

      if (method == "naive") {

        predictions <- rep(
          latest_value,
          forecast_horizon
        )

      } else {

        # For a six-month horizon, use the corresponding
        # observations from the previous year.
        seasonal_indices <- (
          n + seq_len(forecast_horizon) - 12L
        )

        predictions <- values[seasonal_indices]
      }

      forecast_results[[forecast_index]] <- data.frame(
        business_id = id,
        business_name = business_name,
        industry = business_data$industry[1],
        currency = currency,
        target = target,
        method = method,
        forecast_origin_month = max(
          business_data$month_start
        ),
        forecast_month = future_months,
        horizon_month = seq_len(forecast_horizon),
        last_observed_value = latest_value,
        forecast_value = predictions,
        future_quality[rep(1, forecast_horizon), ]
      )

      forecast_index <- forecast_index + 1L
    }
  }
}

# ============================================================
# 8. CHECK THAT RESULTS EXIST
# ============================================================

if (length(backtest_results) == 0 ||
    length(forecast_results) == 0) {
  stop(
    "No forecast results were produced. ",
    "Check observation counts and validation messages."
  )
}

backtest_table <- do.call(
  rbind,
  backtest_results
)

forecast_table <- do.call(
  rbind,
  forecast_results
)

# ============================================================
# 9. SUMMARISE BACKTEST PERFORMANCE
# ============================================================

group_keys <- c(
  "business_id",
  "business_name",
  "currency",
  "target",
  "method"
)

groups <- unique(backtest_table[group_keys])

metric_results <- vector("list", nrow(groups))

for (i in seq_len(nrow(groups))) {

  group <- groups[i, ]

  matches <- rep(TRUE, nrow(backtest_table))

  for (key in group_keys) {
    matches <- matches &
      backtest_table[[key]] == group[[key]]
  }

  errors <- backtest_table$error[matches]

  absolute_errors <- backtest_table$absolute_error[matches]

  scaled_errors <- backtest_table$scaled_absolute_error[matches]

  metric_results[[i]] <- data.frame(
    group,
    forecast_error_count = length(errors),
    MAE = mean(absolute_errors),
    RMSE = sqrt(mean(errors^2)),
    MASE = if (all(is.na(scaled_errors))) {
      NA_real_
    } else {
      mean(scaled_errors, na.rm = TRUE)
    }
  )
}

baseline_metrics <- do.call(
  rbind,
  metric_results
)

# ============================================================
# 10. SAVE RESULTS
# ============================================================

write.csv(
  backtest_table,
  file.path(
    evaluation_dir,
    "monthly_baseline_backtest_errors.csv"
  ),
  row.names = FALSE
)

write.csv(
  baseline_metrics,
  file.path(
    evaluation_dir,
    "monthly_baseline_metrics.csv"
  ),
  row.names = FALSE
)

write.csv(
  forecast_table,
  file.path(
    forecasts_dir,
    "monthly_baseline_forecasts.csv"
  ),
  row.names = FALSE
)
