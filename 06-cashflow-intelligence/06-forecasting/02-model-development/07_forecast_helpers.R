
# ============================================================
# Orey Analytics
# Phase 06 — Cash Flow Intelligence
# Shared Forecasting Helpers
#
# Purpose:
#   1. Naive baseline
#   2. Seasonal naive baseline
#   3. ETS
#   4. ARIMA
#
# Principles:
#   - Preserve unusual observations.
#   - Never automatically replace zero or negative values.
#   - Report model failures explicitly.
#   - Keep forecasting separate from database operations.
# ============================================================


# ------------------------------------------------------------
# 1. Validate input series
# ------------------------------------------------------------

validate_forecast_series <- function(y, horizon = 6L) {
  
  if (!is.numeric(y)) {
    stop("The input series must be numeric.")
  }
  
  if (length(y) < 12L) {
    stop("At least 12 monthly observations are required.")
  }
  
  if (any(!is.finite(y))) {
    stop(
      "The series contains missing or non-finite values. ",
      "Investigate them before fitting a model."
    )
  }
  
  if (
    length(horizon) != 1L ||
    !is.numeric(horizon) ||
    is.na(horizon) ||
    !is.finite(horizon) ||
    horizon < 1 ||
    horizon != as.integer(horizon)
  ) {
    stop("horizon must be a positive whole number.")
  }
  
  invisible(TRUE)
}


# ------------------------------------------------------------
# 2. Naive forecast
# ------------------------------------------------------------

fit_naive_forecast <- function(y, horizon = 6L) {
  
  validate_forecast_series(y, horizon)
  
  forecast::naive(
    stats::ts(
      y,
      start = c(2024, 1),
      frequency = 12
    ),
    h = as.integer(horizon)
  )
}


# ------------------------------------------------------------
# 3. Seasonal naive forecast
# ------------------------------------------------------------

fit_seasonal_naive_forecast <- function(
    y,
    horizon = 6L
) {
  
  validate_forecast_series(y, horizon)
  
  # A complete annual cycle is required.
  # Repeat the latest 12 observations in seasonal order.
  #
  # This implementation returns point forecasts only.
  # It does not calculate prediction intervals.
  
  last_season <- tail(y, 12L)
  
  forecast_values <- rep(
    last_season,
    length.out = as.integer(horizon)
  )
  
  # Return a list containing $mean so it remains
  # compatible with the other forecasting helpers.
  
  list(
    mean = forecast_values
  )
}


# ------------------------------------------------------------
# 4. ETS forecast
# ------------------------------------------------------------

fit_ets_forecast <- function(y, horizon = 6L) {
  
  validate_forecast_series(y, horizon)
  
  monthly_series <- stats::ts(
    y,
    start = c(2024, 1),
    frequency = 12
  )
  
  fitted_model <- forecast::ets(
    monthly_series,
    model = "ZZZ",
    damped = NULL
  )
  
  forecast::forecast(
    fitted_model,
    h = as.integer(horizon)
  )
}


# ------------------------------------------------------------
# 5. ARIMA forecast
# ------------------------------------------------------------

fit_arima_forecast <- function(y, horizon = 6L) {
  
  validate_forecast_series(y, horizon)
  
  monthly_series <- stats::ts(
    y,
    start = c(2024, 1),
    frequency = 12
  )
  
  fitted_model <- forecast::auto.arima(
    monthly_series,
    seasonal = TRUE,
    stepwise = TRUE,
    approximation = FALSE
  )
  
  forecast::forecast(
    fitted_model,
    h = as.integer(horizon)
  )
}


# ------------------------------------------------------------
# 6. Safely run a forecasting method
# ------------------------------------------------------------

run_forecast_safely <- function(
    y,
    method,
    horizon = 6L
) {
  
  forecast_functions <- list(
    naive = fit_naive_forecast,
    seasonal_naive = fit_seasonal_naive_forecast,
    ETS = fit_ets_forecast,
    ARIMA = fit_arima_forecast
  )
  
  if (
    length(method) != 1L ||
    is.na(method) ||
    !method %in% names(forecast_functions)
  ) {
    stop(
      "Unknown method. Choose: ",
      paste(names(forecast_functions), collapse = ", ")
    )
  }
  
  result <- tryCatch(
    {
      fitted_forecast <- forecast_functions[[method]](
        y = y,
        horizon = horizon
      )
      
      list(
        status = "success",
        method = method,
        forecast = fitted_forecast,
        error_message = NA_character_
      )
    },
    error = function(e) {
      list(
        status = "failed",
        method = method,
        forecast = NULL,
        error_message = conditionMessage(e)
      )
    }
  )
  
  result
}


# ------------------------------------------------------------
# 7. Extract forecast values into a data frame
# ------------------------------------------------------------

extract_forecast_values <- function(
    forecast_result,
    business_id,
    target,
    origin_date,
    horizon = 6L
) {
  
  if (!identical(forecast_result$status, "success")) {
    stop(
      "Cannot extract forecasts: ",
      forecast_result$error_message
    )
  }
  
  fitted_forecast <- forecast_result$forecast
  
  if (length(fitted_forecast$mean) != horizon) {
    stop(
      "The forecast length does not match ",
      "the requested horizon."
    )
  }
  
  future_dates <- seq.Date(
    from = as.Date(origin_date),
    by = "month",
    length.out = as.integer(horizon) + 1L
  )[-1L]
  
  data.frame(
    business_id = business_id,
    target = target,
    method = forecast_result$method,
    origin_date = as.Date(origin_date),
    forecast_date = future_dates,
    horizon = seq_len(as.integer(horizon)),
    forecast_value = as.numeric(fitted_forecast$mean),
    stringsAsFactors = FALSE
  )
}
