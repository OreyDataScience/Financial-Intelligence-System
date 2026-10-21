# OREY ANALYTICS
# Phase 06 — Cash Flow Intelligence
# 01 — Time-Series Diagnostics
#
# Purpose:
#   Examine trends, outliers and temporal dependence before
#   selecting forecasting models.
#
# Data:
#   analytics.v_monthly_cashflow_monitoring
#
# Important:
#   - Flagged outliers are not automatically errors.
#   - Trend confidence intervals assume independent errors
#     in the basic linear regression model.
#   - Ljung-Box results are exploratory with short series.

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

diagnostics_dir <- file.path(
  project_dir,
  "05-outputs",
  "diagnostics"
)

evaluation_dir <- file.path(
  project_dir,
  "05-outputs",
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
# 3. RETRIEVE DATA
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
# 4. VALIDATE THE SERIES
# ============================================================

targets <- c(
  "total_credit_inflows",
  "total_debit_outflows",
  "net_bank_movement"
)

monthly_data$month_start <- as.Date(
  monthly_data$month_start
)

for (target in targets) {
  monthly_data[[target]] <- as.numeric(
    monthly_data[[target]]
  )
}

if (nrow(monthly_data) == 0) {
  stop("No monthly observations were retrieved.")
}

if (anyDuplicated(
  monthly_data[c("business_id", "month_start")]
) > 0) {
  stop("Duplicate business-month observations detected.")
}

if (any(!is.finite(
  as.matrix(monthly_data[targets])
))) {
  stop(
    "Target values contain missing or non-finite values. ",
    "Resolve the input issue before running diagnostics."
  )
}


# ============================================================
# 5. PREPARE DIAGNOSTIC RESULTS
# ============================================================

business_ids <- unique(monthly_data$business_id)

trend_results <- list()
outlier_results <- list()
ljung_box_results <- list()

trend_index <- 1
outlier_index <- 1
ljung_index <- 1


# ============================================================
# 6. ANALYSE EACH BUSINESS AND TARGET
# ============================================================

for (id in business_ids) {

  business_data <- monthly_data[
    monthly_data$business_id == id,
  ]

  business_data <- business_data[
    order(business_data$month_start),
  ]

  for (target in targets) {

    values <- business_data[[target]]
    dates <- business_data$month_start
    n <- length(values)

    if (n < 12) {
      warning(
        "Fewer than 12 observations for ",
        id, " / ", target,
        ". Some diagnostics will be skipped."
      )
    }

    # --------------------------------------------------------
    # 6A. TIME-SERIES PLOT
    # --------------------------------------------------------

    plot_file <- paste0(
      id, "_",
      target,
      "_time_series.png"
    )

    png(
      filename = file.path(
        diagnostics_dir,
        plot_file
      ),
      width = 1200,
      height = 700,
      res = 120
    )

    plot(
      dates,
      values,
      type = "o",
      pch = 16,
      xlab = "Month",
      ylab = "Amount (ZAR)",
      main = paste(
        business_data$business_name[1],
        "\n",
        target
      )
    )

    grid()
    dev.off()


    # --------------------------------------------------------
    # 6B. LINEAR TREND REGRESSION
    # --------------------------------------------------------

    time_index <- seq_len(n)

    trend_model <- lm(
      values ~ time_index
    )

    trend_summary <- summary(trend_model)
    slope_ci <- confint(trend_model)["time_index", ]

    trend_results[[trend_index]] <- data.frame(
      business_id = id,
      business_name = business_data$business_name[1],
      target = target,
      observations = n,
      monthly_slope = unname(coef(trend_model)["time_index"]),
      slope_standard_error = unname(
        trend_summary$coefficients[
          "time_index", "Std. Error"
        ]
      ),
      slope_t_statistic = unname(
        trend_summary$coefficients[
          "time_index", "t value"
        ]
      ),
      slope_p_value = unname(
        trend_summary$coefficients[
          "time_index", "Pr(>|t|)"
        ]
      ),
      slope_ci_lower = slope_ci[1],
      slope_ci_upper = slope_ci[2],
      r_squared = trend_summary$r.squared,
      adjusted_r_squared = trend_summary$adj.r.squared
    )

    trend_index <- trend_index + 1


    # --------------------------------------------------------
    # 6C. IQR-BASED OUTLIER FLAGS
    # --------------------------------------------------------

    q1 <- unname(quantile(values, 0.25))
    q3 <- unname(quantile(values, 0.75))
    iqr_value <- IQR(values)

    lower_fence <- q1 - 1.5 * iqr_value
    upper_fence <- q3 + 1.5 * iqr_value

    flagged <- values < lower_fence |
      values > upper_fence

    outlier_results[[outlier_index]] <- data.frame(
      business_id = id,
      business_name = business_data$business_name[1],
      target = target,
      month_start = dates,
      observed_value = values,
      q1 = q1,
      q3 = q3,
      iqr = iqr_value,
      lower_fence = lower_fence,
      upper_fence = upper_fence,
      outlier_flag = flagged,
      investigation_required_count =
        business_data$investigation_required_count,
      reversal_count = business_data$reversal_count,
      sign_inconsistency_count =
        business_data$sign_inconsistency_count
    )

    outlier_index <- outlier_index + 1


    # --------------------------------------------------------
    # 6D. ACF AND PACF
    # --------------------------------------------------------

    # With 24 observations, show only a small set of lags.
    max_lag <- min(6, floor(n / 3))

    if (n >= 12) {

      acf_file <- paste0(
        id, "_", target, "_acf.png"
      )

      png(
        filename = file.path(
          diagnostics_dir,
          acf_file
        ),
        width = 1000,
        height = 650,
        res = 120
      )

      acf(
        values,
        lag.max = max_lag,
        main = paste(id, target, "ACF")
      )

      dev.off()


      pacf_file <- paste0(
        id, "_", target, "_pacf.png"
      )

      png(
        filename = file.path(
          diagnostics_dir,
          pacf_file
        ),
        width = 1000,
        height = 650,
        res = 120
      )

      pacf(
        values,
        lag.max = max_lag,
        main = paste(id, target, "PACF")
      )

      dev.off()
    }


    # --------------------------------------------------------
    # 6E. LJUNG-BOX TEST
    # --------------------------------------------------------

    # This tests the joint null hypothesis that autocorrelations
    # through the selected lag are zero.
    #
    # The raw series may contain trend. Therefore this test is
    # exploratory; residual diagnostics from a fitted model
    # will be more informative later.

    if (n >= 12) {

      test_lag <- min(6, floor(n / 3))

      lb_test <- Box.test(
        values,
        lag = test_lag,
        type = "Ljung-Box",
        fitdf = 0
      )

      ljung_box_results[[ljung_index]] <- data.frame(
        business_id = id,
        business_name = business_data$business_name[1],
        target = target,
        observations = n,
        test_lag = test_lag,
        test_statistic = unname(lb_test$statistic),
        degrees_of_freedom = unname(lb_test$parameter),
        p_value = lb_test$p.value
      )

      ljung_index <- ljung_index + 1
    }
  }
}


# ============================================================
# 7. SAVE RESULTS
# ============================================================

trend_table <- do.call(rbind, trend_results)

outlier_table <- do.call(rbind, outlier_results)

write.csv(
  trend_table,
  file.path(
    evaluation_dir,
    "linear_trend_diagnostics.csv"
  ),
  row.names = FALSE
)

write.csv(
  outlier_table,
  file.path(
    diagnostics_dir,
    "iqr_outlier_diagnostics.csv"
  ),
  row.names = FALSE
)

if (length(ljung_box_results) > 0) {

  ljung_box_table <- do.call(
    rbind,
    ljung_box_results
  )

  write.csv(
    ljung_box_table,
    file.path(
      evaluation_dir,
      "ljung_box_diagnostics.csv"
    ),
    row.names = FALSE
  )
}

