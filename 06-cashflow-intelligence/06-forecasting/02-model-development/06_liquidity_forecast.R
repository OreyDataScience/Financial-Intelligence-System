# ============================================================
# Orey Analytics
# Phase 06 — Liquidity Forecast
#
# Requires successful runs of scripts 03, 04 and 05.
# Does not infer a closing balance without an opening balance.
# ============================================================

project_dir <- normalizePath(getwd(), winslash = "/", mustWork = TRUE)

forecast_dir <- file.path(project_dir, "05-outputs", "forecasts")
input_dir <- file.path(project_dir, "01-data-inputs")

credit_file <- file.path(forecast_dir, "03_revenue_forecasts.csv")
debit_file <- file.path(forecast_dir, "04_expense_forecasts.csv")
net_file <- file.path(forecast_dir, "05_cashflow_forecasts.csv")

required_files <- c(credit_file, debit_file, net_file)
missing_files <- required_files[!file.exists(required_files)]

if (length(missing_files) > 0L) {
  stop(
    "Required forecast files are missing. Run scripts 03, 04 and 05 first:\n",
    paste(missing_files, collapse = "\n")
  )
}

credit <- read.csv(credit_file, stringsAsFactors = FALSE)
debit <- read.csv(debit_file, stringsAsFactors = FALSE)
net <- read.csv(net_file, stringsAsFactors = FALSE)

required_columns <- c(
  "business_id", "currency", "forecast_date", "forecast_value"
)

for (entry in list(
  credit = credit,
  debit = debit,
  net = net
)) {
  if (!all(required_columns %in% names(entry))) {
    stop("A forecast file is missing required columns.")
  }
}

credit$forecast_date <- as.Date(credit$forecast_date)
debit$forecast_date <- as.Date(debit$forecast_date)
net$forecast_date <- as.Date(net$forecast_date)

names(credit)[names(credit) == "forecast_value"] <-
  "forecast_credit_inflows"

names(debit)[names(debit) == "forecast_value"] <-
  "forecast_debit_outflows"

names(net)[names(net) == "forecast_value"] <-
  "forecast_net_bank_movement"

credit <- credit[c(
  "business_id", "currency", "forecast_date",
  "forecast_credit_inflows"
)]

debit <- debit[c(
  "business_id", "currency", "forecast_date",
  "forecast_debit_outflows"
)]

net$origin_date <- as.Date(net$origin_date)

net <- net[c(
  "business_id", "currency", "forecast_date",
  "forecast_net_bank_movement"
)]

key_columns <- c("business_id", "forecast_date")

if (anyDuplicated(credit[key_columns]) > 0L ||
    anyDuplicated(debit[key_columns]) > 0L ||
    anyDuplicated(net[key_columns]) > 0L) {
  stop("Duplicate business/date forecasts detected.")
}

if (any(!is.finite(credit$forecast_credit_inflows)) ||
    any(!is.finite(debit$forecast_debit_outflows)) ||
    any(!is.finite(net$forecast_net_bank_movement))) {
  stop("Non-finite forecast values detected. Investigate before proceeding.")
}

liquidity <- merge(
  credit, debit,
  by = c("business_id", "currency", "forecast_date"),
  all = FALSE
)

liquidity <- merge(
  liquidity, net,
  by = c("business_id", "currency", "forecast_date"),
  all = FALSE
)

if (nrow(liquidity) == 0L) {
  stop("No matching forecasts across all three target files.")
}

# Independent component-based estimate.
liquidity$component_net_movement <-
  liquidity$forecast_credit_inflows -
  liquidity$forecast_debit_outflows

# Difference between direct and component-based forecasts.
liquidity$net_forecast_reconciliation_gap <-
  liquidity$forecast_net_bank_movement -
  liquidity$component_net_movement

liquidity <- liquidity[
  order(liquidity$business_id, liquidity$forecast_date),
]

liquidity$forecast_horizon <- ave(
  liquidity$forecast_date,
  liquidity$business_id,
  FUN = function(x) seq_along(x)
)

# Optional opening cash balances.
opening_file <- file.path(
  input_dir, "opening_cash_balances.csv"
)

liquidity$opening_cash_balance <- NA_real_
liquidity$projected_closing_cash_balance <- NA_real_
liquidity$liquidity_status <- "opening_balance_required"

if (file.exists(opening_file)) {
  opening <- read.csv(opening_file, stringsAsFactors = FALSE)
  
  required_opening <- c(
    "business_id", "currency", "as_of_month",
    "opening_cash_balance"
  )
  
  if (!all(required_opening %in% names(opening))) {
    stop(
      "opening_cash_balances.csv must contain: ",
      paste(required_opening, collapse = ", ")
    )
  }
  
  opening$as_of_month <- as.Date(opening$as_of_month)
  opening$opening_cash_balance <- as.numeric(
    opening$opening_cash_balance
  )
  
  if (anyNA(opening$business_id) ||
      anyNA(opening$currency) ||
      anyNA(opening$as_of_month) ||
      any(!is.finite(opening$opening_cash_balance))) {
    stop("Opening-balance input contains missing or non-finite values.")
  }
  
  if (anyDuplicated(opening$business_id) > 0L) {
    stop("Opening-balance input must have one row per business.")
  }
  
  for (id in unique(liquidity$business_id)) {
    business_rows <- which(liquidity$business_id == id)
    opening_row <- opening[opening$business_id == id, ]
    
    if (nrow(opening_row) != 1L) {
      warning(
        "No unique opening balance for ", id,
        ". Closing balances will remain unavailable."
      )
      next
    }
    
    if (!all(liquidity$currency[business_rows] == opening_row$currency[1])) {
      stop("Currency mismatch in opening balance for ", id, ".")
    }
    
    # Validate that the opening balance corresponds to the
    # latest observed month used to generate these forecasts.
    origin_month <- max(net$origin_date[
      net$business_id == id
    ])
    
    if (length(origin_month) != 1L ||
        is.na(origin_month) ||
        opening_row$as_of_month[1] != as.Date(origin_month)) {
      warning(
        "Opening balance date does not match forecast origin for ",
        id, ". Closing balances will remain unavailable."
      )
      next
    }
    
    liquidity$opening_cash_balance[business_rows] <-
      opening_row$opening_cash_balance[1]
    
    ordered_rows <- business_rows[
      order(liquidity$forecast_date[business_rows])
    ]
    
    cumulative_movement <- cumsum(
      liquidity$forecast_net_bank_movement[ordered_rows]
    )
    
    liquidity$projected_closing_cash_balance[ordered_rows] <-
      opening_row$opening_cash_balance[1] + cumulative_movement
    
    liquidity$liquidity_status[ordered_rows] <-
      "projected_using_supplied_opening_balance"
  }
}

output_file <- file.path(
  forecast_dir, "06_liquidity_forecasts.csv"
)

write.csv(
  liquidity,
  output_file,
  row.names = FALSE
)

cat("\nLiquidity forecasting complete.\n")
cat("Output rows:", nrow(liquidity), "\n")
cat("Output file:", output_file, "\n")
cat(
  "Rows with opening balances:",
  sum(!is.na(liquidity$opening_cash_balance)), "\n"
)
cat(
  "Rows requiring opening balances:",
  sum(is.na(liquidity$opening_cash_balance)), "\n"
)
