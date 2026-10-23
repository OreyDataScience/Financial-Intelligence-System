# ============================================================
# Orey Analytics
# Phase 06 — Liquidity Forecast
#
# Requires successful runs of scripts 03, 04 and 05.
# Does not infer a closing balance without an opening balance.
# ============================================================

project_dir <- normalizePath(
  getwd(),
  winslash = "/",
  mustWork = TRUE
)

forecast_dir <- file.path(
  project_dir, "05-outputs", "forecasts"
)

input_dir <- file.path(
  project_dir, "01-data-inputs"
)

credit_file <- file.path(
  forecast_dir, "03_revenue_forecasts.csv"
)

debit_file <- file.path(
  forecast_dir, "04_expense_forecasts.csv"
)

net_file <- file.path(
  forecast_dir, "05_cashflow_forecasts.csv"
)

# ------------------------------------------------------------
# 1. Validate required forecast files
# ------------------------------------------------------------

required_files <- c(
  credit_file,
  debit_file,
  net_file
)

missing_files <- required_files[
  !file.exists(required_files)
]

if (length(missing_files) > 0L) {
  stop(
    "Required forecast files are missing. ",
    "Run scripts 03, 04 and 05 first:\n",
    paste(missing_files, collapse = "\n")
  )
}

credit <- read.csv(
  credit_file,
  stringsAsFactors = FALSE
)

debit <- read.csv(
  debit_file,
  stringsAsFactors = FALSE
)

net <- read.csv(
  net_file,
  stringsAsFactors = FALSE
)

required_columns <- c(
  "business_id",
  "currency",
  "forecast_date",
  "forecast_value"
)

for (entry in list(
  credit = credit,
  debit = debit,
  net = net
)) {
  if (!all(required_columns %in% names(entry))) {
    stop(
      "A forecast file is missing required columns."
    )
  }
}

# origin_date is required for opening-balance validation.
if (!"origin_date" %in% names(net)) {
  stop(
    "The cash-flow forecast file is missing origin_date. ",
    "Check script 05 before continuing."
  )
}

# ------------------------------------------------------------
# 2. Convert forecast dates
# ------------------------------------------------------------

credit$forecast_date <- as.Date(
  credit$forecast_date
)

debit$forecast_date <- as.Date(
  debit$forecast_date
)

net$forecast_date <- as.Date(
  net$forecast_date
)

net$origin_date <- as.Date(
  net$origin_date
)

if (anyNA(credit$forecast_date) ||
    anyNA(debit$forecast_date) ||
    anyNA(net$forecast_date) ||
    anyNA(net$origin_date)) {
  stop(
    "Invalid or missing dates detected in forecast files."
  )
}

# ------------------------------------------------------------
# 3. Rename forecast values
# ------------------------------------------------------------

names(credit)[
  names(credit) == "forecast_value"
] <- "forecast_credit_inflows"

names(debit)[
  names(debit) == "forecast_value"
] <- "forecast_debit_outflows"

names(net)[
  names(net) == "forecast_value"
] <- "forecast_net_bank_movement"

# ------------------------------------------------------------
# 4. Retain required columns
# ------------------------------------------------------------

credit <- credit[c(
  "business_id",
  "currency",
  "forecast_date",
  "forecast_credit_inflows"
)]

debit <- debit[c(
  "business_id",
  "currency",
  "forecast_date",
  "forecast_debit_outflows"
)]

# IMPORTANT:
# Retain origin_date because the opening-balance validation
# below compares it with the supplied balance's as_of_month.

net <- net[c(
  "business_id",
  "currency",
  "forecast_date",
  "origin_date",
  "forecast_net_bank_movement"
)]

# ------------------------------------------------------------
# 5. Validate forecast uniqueness and numeric values
# ------------------------------------------------------------

key_columns <- c(
  "business_id",
  "forecast_date"
)

if (anyDuplicated(credit[key_columns]) > 0L ||
    anyDuplicated(debit[key_columns]) > 0L ||
    anyDuplicated(net[key_columns]) > 0L) {
  stop(
    "Duplicate business/date forecasts detected."
  )
}

if (anyNA(credit$business_id) ||
    anyNA(debit$business_id) ||
    anyNA(net$business_id) ||
    anyNA(credit$currency) ||
    anyNA(debit$currency) ||
    anyNA(net$currency)) {
  stop(
    "Missing business IDs or currencies detected."
  )
}

if (any(!is.finite(credit$forecast_credit_inflows)) ||
    any(!is.finite(debit$forecast_debit_outflows)) ||
    any(!is.finite(net$forecast_net_bank_movement))) {
  stop(
    "Non-finite forecast values detected. ",
    "Investigate before proceeding."
  )
}

# ------------------------------------------------------------
# 6. Merge the three forecast components
# ------------------------------------------------------------

liquidity <- merge(
  credit,
  debit,
  by = c(
    "business_id",
    "currency",
    "forecast_date"
  ),
  all = FALSE
)

liquidity <- merge(
  liquidity,
  net,
  by = c(
    "business_id",
    "currency",
    "forecast_date"
  ),
  all = FALSE
)

if (nrow(liquidity) == 0L) {
  stop(
    "No matching forecasts across all three target files."
  )
}

# ------------------------------------------------------------
# 7. Calculate reconciliation diagnostics
# ------------------------------------------------------------

# Independent component-based estimate.
liquidity$component_net_movement <-
  liquidity$forecast_credit_inflows -
  liquidity$forecast_debit_outflows

# Difference between direct and component-based forecasts.
# Nonzero gaps are retained for investigation.
liquidity$net_forecast_reconciliation_gap <-
  liquidity$forecast_net_bank_movement -
  liquidity$component_net_movement

# ------------------------------------------------------------
# 8. Assign integer forecast horizons
# ------------------------------------------------------------

liquidity$forecast_date <- as.Date(
  liquidity$forecast_date
)

liquidity <- liquidity[
  order(
    liquidity$business_id,
    liquidity$forecast_date
  ),
]

# Assign horizons separately for each business.
# The first forecast month is 1, then 2, through 6.
liquidity$forecast_horizon <- ave(
  seq_len(nrow(liquidity)),
  liquidity$business_id,
  FUN = function(x) seq_along(x)
)

liquidity$forecast_horizon <- as.integer(
  liquidity$forecast_horizon
)

# ------------------------------------------------------------
# 9. Initialize opening and closing cash balances
# ------------------------------------------------------------

opening_file <- file.path(
  input_dir,
  "opening_cash_balances.csv"
)

liquidity$opening_cash_balance <- NA_real_

liquidity$projected_closing_cash_balance <- NA_real_

liquidity$liquidity_status <- "opening_balance_required"

# ------------------------------------------------------------
# 10. Apply opening balances if a valid input file exists
# ------------------------------------------------------------

if (file.exists(opening_file)) {
  
  opening <- read.csv(
    opening_file,
    stringsAsFactors = FALSE
  )
  
  required_opening <- c(
    "business_id",
    "currency",
    "as_of_month",
    "opening_cash_balance"
  )
  
  if (!all(required_opening %in% names(opening))) {
    stop(
      "opening_cash_balances.csv must contain: ",
      paste(required_opening, collapse = ", ")
    )
  }
  
  opening$as_of_month <- as.Date(
    opening$as_of_month
  )
  
  opening$opening_cash_balance <- as.numeric(
    opening$opening_cash_balance
  )
  
  if (anyNA(opening$business_id) ||
      anyNA(opening$currency) ||
      anyNA(opening$as_of_month) ||
      any(!is.finite(opening$opening_cash_balance))) {
    stop(
      "Opening-balance input contains missing ",
      "or non-finite values."
    )
  }
  
  if (anyDuplicated(opening$business_id) > 0L) {
    stop(
      "Opening-balance input must have one row per business."
    )
  }
  
  for (id in unique(liquidity$business_id)) {
    
    business_rows <- which(
      liquidity$business_id == id
    )
    
    opening_row <- opening[
      opening$business_id == id,
      ,
      drop = FALSE
    ]
    
    if (nrow(opening_row) != 1L) {
      warning(
        "No unique opening balance for ",
        id,
        ". Closing balances will remain unavailable."
      )
      
      next
    }
    
    if (!all(
      liquidity$currency[business_rows] ==
      opening_row$currency[1]
    )) {
      stop(
        "Currency mismatch in opening balance for ",
        id,
        "."
      )
    }
    
    # Validate that the opening balance corresponds to
    # the latest observed month used to generate forecasts.
    origin_month <- max(
      net$origin_date[
        net$business_id == id
      ]
    )
    
    if (length(origin_month) != 1L ||
        is.na(origin_month) ||
        opening_row$as_of_month[1] !=
        as.Date(origin_month)) {
      
      warning(
        "Opening balance date does not match forecast ",
        "origin for ",
        id,
        ". Closing balances will remain unavailable."
      )
      
      next
    }
    
    # Apply the supplied opening cash balance.
    liquidity$opening_cash_balance[business_rows] <-
      opening_row$opening_cash_balance[1]
    
    ordered_rows <- business_rows[
      order(
        liquidity$forecast_date[business_rows]
      )
    ]
    
    # Project closing balances using direct net movement.
    cumulative_movement <- cumsum(
      liquidity$forecast_net_bank_movement[
        ordered_rows
      ]
    )
    
    liquidity$projected_closing_cash_balance[
      ordered_rows
    ] <-
      opening_row$opening_cash_balance[1] +
      cumulative_movement
    
    liquidity$liquidity_status[ordered_rows] <-
      "projected_using_supplied_opening_balance"
  }
}

# ------------------------------------------------------------
# 11. Validate final liquidity output
# ------------------------------------------------------------

if (!inherits(liquidity$forecast_date, "Date")) {
  stop(
    "forecast_date must be a Date column."
  )
}

if (!is.integer(liquidity$forecast_horizon)) {
  stop(
    "forecast_horizon must be an integer column."
  )
}

if (anyDuplicated(
  liquidity[c("business_id", "forecast_date")]
) > 0L) {
  stop(
    "Duplicate business/date forecasts detected."
  )
}

# Every business must have exactly one forecast
# for each horizon from 1 through 6.
horizon_check <- split(
  liquidity$forecast_horizon,
  liquidity$business_id
)

if (!all(vapply(
  horizon_check,
  function(x) identical(sort(x), 1:6),
  logical(1)
))) {
  stop(
    "Each SME must have exactly one forecast ",
    "for horizons 1-6."
  )
}

# Validate that the reconciliation gap is calculable.
if (any(!is.finite(
  liquidity$net_forecast_reconciliation_gap
))) {
  stop(
    "Non-finite reconciliation gaps detected."
  )
}

# ------------------------------------------------------------
# 12. Display and export results
# ------------------------------------------------------------

print(
  liquidity[
    ,
    c(
      "business_id",
      "forecast_date",
      "forecast_horizon",
      "opening_cash_balance",
      "projected_closing_cash_balance"
    )
  ],
  row.names = FALSE
)

output_file <- file.path(
  forecast_dir,
  "06_liquidity_forecasts.csv"
)

write.csv(
  liquidity,
  output_file,
  row.names = FALSE
)

cat("\nLiquidity forecasting complete.\n")

cat(
  "Output rows:",
  nrow(liquidity),
  "\n"
)

cat(
  "Output file:",
  output_file,
  "\n"
)

cat(
  "Rows with opening balances:",
  sum(!is.na(liquidity$opening_cash_balance)),
  "\n"
)

cat(
  "Rows requiring opening balances:",
  sum(is.na(liquidity$opening_cash_balance)),
  "\n"
)

cat(
  "Rows with projected closing balances:",
  sum(!is.na(
    liquidity$projected_closing_cash_balance
  )),
  "\n"
)

cat(
  "Rows with reconciliation gaps:",
  sum(
    abs(liquidity$net_forecast_reconciliation_gap) > 1e-8
  ),
  "\n"
)
